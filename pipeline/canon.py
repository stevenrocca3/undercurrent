"""Turn raw lines into canon-v1 records or quarantine reason codes (spec §2).

`classify(raw, partial)` returns `(code, fields)`: code is `Q1`..`Q4` with
fields None, or `canonical` with the fields parsed from the line. The checks
run in the §2 order and the first match wins. `CanonStore` writes canonical
records and quarantined lines to a DuckDB file on disk.
"""

import hashlib
import json
import re
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
    each top-level value's raw text, so `payload_raw` and a non-string `type`
    are stored exactly as they appeared, not re-serialized. Raises ValueError.
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
        members = parse_object(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return "Q1", None

    def get(key):
        return members[key][0] if key in members else None

    event_id, event_type, created_at = get("id"), get("type"), get("created_at")
    actor, repo, org, payload = get("actor"), get("repo"), get("org"), get("payload")
    actor_id, repo_id = _sub(actor, "id"), _sub(repo, "id")
    fields = {
        "event_id": event_id,
        "event_type": event_type if isinstance(event_type, str) else members.get("type", (None, None))[1],
        "actor_id": actor_id,
        "actor_login": _str_or_none(_sub(actor, "login")),
        "repo_id": repo_id,
        "repo_name": _str_or_none(_sub(repo, "name")),
        "org_id": _sub(org, "id") if is_int64(_sub(org, "id")) else None,
        "is_public": get("public") if isinstance(get("public"), bool) else None,
        "payload_action": _str_or_none(_sub(payload, "action")),
        "payload_raw": members.get("payload", (None, None))[1],
    }
    text_fields = (event_id, event_type, fields["actor_login"], fields["repo_name"], fields["payload_action"])
    if not all(_utf8_ok(v) for v in text_fields if isinstance(v, str)):
        return "Q1", None  # §2 Q1, G28: lone surrogate in a field stored as text; payload is not checked

    if any(v is None for v in (event_id, event_type, repo_id, actor_id, created_at, get("public"), payload)):
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
    "payload_raw": "VARCHAR NOT NULL",   # the payload's raw JSON text
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


def _ts(dt):
    return None if dt is None else dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


class CanonStore:
    """canon-v1 and quarantine tables in a DuckDB file.

    Rows for one hour are spooled to NDJSON files next to the database, then
    loaded in one statement, so memory holds one row at a time.
    """

    def __init__(self, db_path, ingested_at):
        db_path.unlink(missing_ok=True)
        self.con = duckdb.connect(str(db_path))
        self.con.execute("SET memory_limit = '3GB'")  # 8 GB machine: larger work spills to <db>.tmp
        self.spool_dir = db_path.parent
        self.ingested_at = _ts(ingested_at)
        for name, columns in (("canon", CANON_COLUMNS), ("quarantine", QUARANTINE_COLUMNS)):
            self.con.execute(f"CREATE TABLE {name} ({', '.join(f'{c} {t}' for c, t in columns.items())})")

    def begin_hour(self, hour):
        self.hour = hour
        self.canon_path = self.spool_dir / "canon.spool.ndjson"
        self.quarantine_path = self.spool_dir / "quarantine.spool.ndjson"
        self.canon_file = open(self.canon_path, "w", encoding="utf-8")
        self.quarantine_file = open(self.quarantine_path, "w", encoding="utf-8")

    def add(self, source_line, raw, code, fields):
        hour = self.hour.replace(tzinfo=None)
        if code == "canonical":
            row = dict(fields, event_time=_ts(fields["event_time"]), source_file_hour=_ts(hour),
                       source_line=source_line, available_at=_ts(hour + timedelta(hours=1) + AVAILABILITY_LAG),
                       source_last_modified=None, ingested_at=self.ingested_at,
                       record_hash=record_hash(raw), schema_version=SCHEMA_VERSION)
            self.canon_file.write(json.dumps(row) + "\n")
        else:
            row = {"source_file_hour": _ts(hour), "source_line": source_line,
                   "reason_code": code, "raw_line": raw.hex()}
            self.quarantine_file.write(json.dumps(row) + "\n")

    def end_hour(self):
        self.canon_file.close()
        self.quarantine_file.close()
        for table, path, columns in (("canon", self.canon_path, CANON_COLUMNS),
                                     ("quarantine", self.quarantine_path, QUARANTINE_COLUMNS)):
            if path.stat().st_size:
                json_types = {c: ("VARCHAR" if c == "raw_line" else t.replace(" NOT NULL", ""))
                              for c, t in columns.items()}
                select = ", ".join("unhex(raw_line)" if c == "raw_line" else c for c in columns)
                self.con.execute(
                    f"INSERT INTO {table} SELECT {select} FROM read_json(?, format='newline_delimited', "
                    f"columns={json_types!r}, maximum_object_size=268435456)", [str(path)])
            path.unlink()

    def close(self):
        self.con.close()
