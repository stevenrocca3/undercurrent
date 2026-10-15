"""Turn raw lines into canon-v1 records or quarantine reason codes (spec §2).

`classify(raw, partial)` returns `(code, fields)`: code is `Q1`..`Q4` with
fields None, or `canonical` with the fields parsed from the line. The checks
run in the §2 order and the first match wins. `CanonStore` writes canonical
records and quarantined lines to a DuckDB file on disk.
"""

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from json.decoder import scanstring

import duckdb

SCHEMA_VERSION = "canon-v1"
AVAILABILITY_LAG = timedelta(hours=6)  # L, spec §4 (OPEN-2)
INT64_MIN, INT64_MAX = -2**63, 2**63 - 1

WS = re.compile(r"[ \t\n\r]*")  # JSON whitespace
CREATED_AT = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?"
    r"(?:Z|([+-])([0-9]{2}):([0-9]{2}))"
)


def _reject_constant(name):
    raise ValueError(f"not JSON: {name}")


DECODER = json.JSONDecoder(parse_constant=_reject_constant)  # NaN/Infinity are not JSON


def parse_object(text):
    """Parse text that must be one JSON object. Return {key: (value, raw_text)}.

    Same grammar as json.loads (duplicate keys: last wins), but it also keeps
    each top-level value's raw text, so a non-string `type` is stored exactly
    as it appeared, not re-serialized (G30). Raises ValueError.
    """
    i = WS.match(text).end()
    if text[i:i + 1] != "{":
        raise ValueError("not an object")
    i = WS.match(text, i + 1).end()
    members = {}
    if text[i:i + 1] == "}":
        i += 1
    else:
        while True:
            if text[i:i + 1] != '"':
                raise ValueError("expected a key")
            key, i = scanstring(text, i + 1)
            i = WS.match(text, i).end()
            if text[i:i + 1] != ":":
                raise ValueError("expected ':'")
            start = WS.match(text, i + 1).end()
            value, i = DECODER.raw_decode(text, start)
            members[key] = (value, text[start:i])
            i = WS.match(text, i).end()
            if text[i:i + 1] == ",":
                i = WS.match(text, i + 1).end()
            elif text[i:i + 1] == "}":
                i += 1
                break
            else:
                raise ValueError("expected ',' or '}'")
    if WS.match(text, i).end() != len(text):
        raise ValueError("data after the object")
    return members


def parse_created_at(value):
    """§2 Q3: the strict form, a valid instant. Return a naive UTC datetime (µs), or None."""
    m = CREATED_AT.fullmatch(value) if isinstance(value, str) else None
    if not m:
        return None
    year, month, day, hour, minute, second, frac, sign, off_h, off_m = m.groups()
    try:
        local = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                         int((frac or "0").ljust(6, "0")))
        offset = timedelta(0)
        if sign:
            if int(off_h) > 23 or int(off_m) > 59:
                return None
            offset = timedelta(hours=int(off_h), minutes=int(off_m)) * (1 if sign == "+" else -1)
        return local - offset
    except (ValueError, OverflowError):  # e.g. month 13, second 60, year 0, out of range in UTC
        return None


def is_int64(value):
    return type(value) is int and INT64_MIN <= value <= INT64_MAX  # bool is not an int here


def _sub(obj, key):
    return obj.get(key) if isinstance(obj, dict) else None


def _str_or_none(value):
    return value if isinstance(value, str) else None


def _utf8_ok(text):
    """False for a string holding a lone surrogate (from a `\\ud800` escape): not encodable as UTF-8."""
    try:
        text.encode("utf-8")
        return True
    except UnicodeEncodeError:
        return False


def classify(raw, partial):
    """Return (reason_code, None) or ("canonical", fields) for one line (§2)."""
    if partial:
        return "Q1", None
    try:
        text = raw.decode("utf-8")
        obj = DECODER.decode(text)  # C scanner; same grammar as parse_object, last duplicate key wins
    except (UnicodeDecodeError, ValueError, RecursionError):
        return "Q1", None
    if not isinstance(obj, dict):
        return "Q1", None

    get = obj.get
    event_id, event_type, created_at, public = get("id"), get("type"), get("created_at"), get("public")
    actor, repo, org, payload = get("actor"), get("repo"), get("org"), get("payload")
    actor_id, repo_id = _sub(actor, "id"), _sub(repo, "id")
    fields = {
        "event_id": event_id,
        # G30: a non-string type is stored as its raw text; only then is the slower raw parse needed
        "event_type": event_type if isinstance(event_type, str) or event_type is None else parse_object(text)["type"][1],
        "actor_id": actor_id,
        "actor_login": _str_or_none(_sub(actor, "login")),
        "repo_id": repo_id,
        "repo_name": _str_or_none(_sub(repo, "name")),
        "org_id": _sub(org, "id") if is_int64(_sub(org, "id")) else None,
        "is_public": public if isinstance(public, bool) else None,
        "payload_action": _str_or_none(_sub(payload, "action")),
    }
    text_fields = (event_id, event_type, fields["actor_login"], fields["repo_name"], fields["payload_action"])
    if not all(_utf8_ok(v) for v in text_fields if isinstance(v, str)):
        return "Q1", None  # §2 Q1, G28: lone surrogate in a field stored as text; payload is not checked

    if any(v is None for v in (event_id, event_type, repo_id, actor_id, created_at, public, payload)):
        return "Q2", None
    fields["event_time"] = parse_created_at(created_at)
    if fields["event_time"] is None:
        return "Q3", None
    if not isinstance(event_id, str) or not is_int64(actor_id) or not is_int64(repo_id):
        return "Q4", None
    return "canonical", fields


def record_hash(raw):
    """SHA-256 of the raw line bytes; the `\\n` is already gone, a trailing `\\r` is dropped (§2)."""
    return hashlib.sha256(raw[:-1] if raw.endswith(b"\r") else raw).hexdigest()


CANON_COLUMNS = {
    "event_id": "VARCHAR NOT NULL",
    "event_type": "VARCHAR NOT NULL",
    "actor_id": "BIGINT NOT NULL",
    "actor_login": "VARCHAR",
    "repo_id": "BIGINT NOT NULL",
    "repo_name": "VARCHAR",              # SPEC-GAPS G27: null when repo.name is missing or not a string
    "org_id": "BIGINT",
    "is_public": "BOOLEAN",              # SPEC-GAPS G27: null when `public` is not a JSON bool
    "payload_action": "VARCHAR",
    "payload_raw": "VARCHAR",            # null in Gate 1 runs (§2, G32)
    "event_time": "TIMESTAMP NOT NULL",  # all TIMESTAMP columns are UTC, µs
    "source_file_hour": "TIMESTAMP NOT NULL",
    "source_line": "INTEGER NOT NULL",
    "available_at": "TIMESTAMP NOT NULL",
    "source_last_modified": "TIMESTAMP",
    "ingested_at": "TIMESTAMP NOT NULL",
    "record_hash": "VARCHAR NOT NULL",
    "schema_version": "VARCHAR NOT NULL",
}
QUARANTINE_COLUMNS = {
    "source_file_hour": "TIMESTAMP NOT NULL",
    "source_line": "INTEGER NOT NULL",
    "reason_code": "VARCHAR NOT NULL",
    "raw_line": "BLOB NOT NULL",  # bytes as read, without the `\n`; may be invalid UTF-8
}


# Columns that are the same for every row of an hour or a run are set in SQL at load time,
# not written per row (§2, §4; G32: payload_raw is null in Gate 1 runs).
HOUR_CONSTANTS = ("payload_raw", "source_file_hour", "available_at", "source_last_modified",
                  "ingested_at", "schema_version")
SPOOLED = [c for c in CANON_COLUMNS if c not in HOUR_CONSTANTS]


def spool_paths(spool_dir, hour):
    stem = spool_dir / f"{hour:%Y-%m-%dT%H}"
    return stem.with_suffix(".canon.ndjson"), stem.with_suffix(".quarantine.ndjson")


def spool_hour(read, spool_dir):
    """Classify one hour's lines into two NDJSON spool files. Return the R1 line-status counts.

    Runs in a worker process; `read` is an ingest.HourRead whose registry fields are set on return.
    """
    counts = Counter()
    canon_path, quarantine_path = spool_paths(spool_dir, read.hour)
    with open(canon_path, "w", encoding="utf-8") as canon, open(quarantine_path, "w", encoding="utf-8") as quarantine:
        for source_line, raw, partial in read.lines():
            code, fields = classify(raw, partial)
            counts[code] += 1
            if code == "canonical":
                fields["event_time"] = fields["event_time"].isoformat()
                fields["source_line"] = source_line
                fields["record_hash"] = record_hash(raw)
                canon.write(json.dumps(fields) + "\n")
            else:
                quarantine.write(json.dumps({"source_line": source_line, "reason_code": code,
                                             "raw_line": raw.hex()}) + "\n")
    return read, counts


class CanonStore:
    """canon-v1 and quarantine tables in a DuckDB file, loaded one hour's spool files at a time."""

    def __init__(self, db_path, ingested_at):
        db_path.unlink(missing_ok=True)
        self.con = duckdb.connect(str(db_path))
        self.con.execute("SET memory_limit = '3GB'")  # 8 GB machine: larger work spills to <db>.tmp
        self.ingested_at = ingested_at.astimezone(timezone.utc).replace(tzinfo=None)
        for name, columns in (("canon", CANON_COLUMNS), ("quarantine", QUARANTINE_COLUMNS)):
            self.con.execute(f"CREATE TABLE {name} ({', '.join(f'{c} {t}' for c, t in columns.items())})")

    def load_hour(self, hour, spool_dir):
        """Insert one hour's spool files, then delete them."""
        hour = hour.astimezone(timezone.utc).replace(tzinfo=None)
        params = {"source_file_hour": hour, "available_at": hour + timedelta(hours=1) + AVAILABILITY_LAG,
                  "ingested_at": self.ingested_at, "schema_version": SCHEMA_VERSION}
        canon_path, quarantine_path = spool_paths(spool_dir, hour)
        self._insert("canon", canon_path, {c: CANON_COLUMNS[c] for c in SPOOLED}, params,
                     ["$" + c if c in params else "NULL" if c in HOUR_CONSTANTS else c for c in CANON_COLUMNS])
        self._insert("quarantine", quarantine_path,
                     {"source_line": "INTEGER", "reason_code": "VARCHAR", "raw_line": "VARCHAR"},
                     {"source_file_hour": hour},
                     ["$source_file_hour", "source_line", "reason_code", "unhex(raw_line)"])

    def _insert(self, table, path, spooled_types, params, select):
        if path.stat().st_size:
            json_types = {c: t.replace(" NOT NULL", "") for c, t in spooled_types.items()}
            self.con.execute(
                f"INSERT INTO {table} SELECT {', '.join(select)} FROM read_json($path, "
                f"format='newline_delimited', columns={json_types!r}, maximum_object_size=268435456)",
                dict(params, path=str(path)))
        path.unlink()

    def close(self):
        self.con.close()


# §4 Replay, §8 criterion 3: tables compared by content hash after a fixed sort. ingested_at and
# source_last_modified record when a run happened, not what the data says (G29), so they are left out.
DIGESTED_TABLES = {
    "canon": "SELECT * EXCLUDE (ingested_at, source_last_modified) FROM canon",
    "quarantine": "SELECT * FROM quarantine",
    "duplicates": "SELECT * FROM duplicates",
}


def table_digests(con):
    """[(table, rows, sha256)]: each row as JSON text plus LF, in (source_file_hour, source_line) order.

    Sorted one source_file_hour at a time (NOT NULL in every digested table): one sort of the whole
    table spills past memory_limit and took 443 s of a 1,269 s month run; per hour, the bytes are the same.
    """
    out = []
    for table, select in DIGESTED_TABLES.items():
        digest, rows = hashlib.sha256(), 0
        hours = con.execute(f"SELECT DISTINCT source_file_hour FROM ({select}) t ORDER BY 1").fetchall()
        for (hour,) in hours:
            result = con.execute(f"SELECT to_json(t)::VARCHAR FROM ({select}) t WHERE source_file_hour = $hour"
                                 " ORDER BY source_line", {"hour": hour})
            while batch := result.fetchmany(100_000):
                rows += len(batch)
                digest.update("".join(text + "\n" for (text,) in batch).encode("utf-8"))
        out.append((table, rows, digest.hexdigest()))
    return out
