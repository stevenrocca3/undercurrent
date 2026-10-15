"""Reference calculation, R1-R7 (01-event-semantics.md §6).

The dumbest correct implementation, kept independent of the pipeline: it reads
the raw GH Archive .json.gz files directly and imports nothing from the
pipeline codebase. Python does per-line parsing and quarantine (§2) and the
missing-hour registry (§1); DuckDB does dedup and aggregation (§3, §4, §6),
because a month of event_ids does not fit in memory as a Python set.

    python reference/reference.py run INPUT_DIR FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...]
        FIRST_HOUR/LAST_HOUR inclusive, e.g. 2026-09-01T00:00:00Z.

    python reference/reference.py fixtures FIXTURES_DIR OUT_ROOT
        Runs every FIXTURES_DIR/Fxx-*/ (input/ + fixture.json) into OUT_ROOT/Fxx-*/.

Then compare with tools/compare_outputs.py.
"""

import csv
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

US_PER_HOUR = 3_600_000_000
LAG_L_HOURS = 6  # §4, OPEN-2: available_at = source_file_hour + 1h + L
INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1
RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|[+-]\d{2}:\d{2})")
EVENT_TYPES = set(
    (Path(__file__).resolve().parent.parent / "fixtures" / "event_types.txt").read_text().split()
)
CHUNK = 1 << 20
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


# ---------- time helpers ----------

def parse_hour(s):
    return datetime.strptime(s, TS_FORMAT).replace(tzinfo=timezone.utc)


def to_us(dt):
    return (dt - datetime(1970, 1, 1, tzinfo=timezone.utc)) // timedelta(microseconds=1)


def fmt_ts(us):
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=us)).strftime(TS_FORMAT)


def hour_file_name(dt):
    return f"{dt:%Y-%m-%d}-{dt.hour}.json.gz"  # hour not zero-padded


# ---------- §1: reading one hour file, with registry status ----------

def read_hour(path):
    """Return (status, lines). lines = [(line_bytes, is_partial)]. §1 registry rules.

    present    - every gzip member decoded to its end
    unreadable - decoding failed before yielding one complete line; no lines returned
    truncated  - decoding failed after >= 1 complete line; complete lines kept,
                 bytes after the last \\n returned as one partial line (-> Q1)
    """
    if not path.exists():
        return "missing", []
    data = path.read_bytes()
    out, failed, pos = [], False, 0
    while True:
        d = zlib.decompressobj(wbits=31)
        for i in range(pos, len(data), CHUNK):
            d, failed = feed(d, data[i:i + CHUNK], out)
            if failed or d.eof:
                break
        if failed:
            break
        if not d.eof:
            failed = True  # stream ended early
            break
        if not d.unused_data:
            break
        pos = len(data) - len(d.unused_data)  # next gzip member
    text = b"".join(out)
    parts = text.split(b"\n")
    complete, tail = parts[:-1], parts[-1]
    if failed and not complete:
        return "unreadable", []
    lines = [(b, False) for b in complete]
    if tail:
        lines.append((tail, failed))  # a complete stream may also lack a final \n
    return ("truncated" if failed else "present"), lines


def feed(d, chunk, out):
    """Decompress chunk into out; return (decompressor, failed).

    zlib discards a call's output when it raises (e.g. a CRC error in the
    trailer), so on error re-feed the chunk byte by byte from a saved copy.
    That keeps everything decodable before the error, whatever the chunk size.
    """
    saved = d.copy()
    try:
        out.append(d.decompress(chunk))
        return d, False
    except zlib.error:
        d = saved
        for k in range(len(chunk)):
            try:
                out.append(d.decompress(chunk[k:k + 1]))
            except zlib.error:
                return d, True
            if d.eof:
                return d, False
        return d, False


# ---------- §2: one line -> quarantine code or canonical row ----------

def is_int64(v):
    return isinstance(v, int) and not isinstance(v, bool) and INT64_MIN <= v <= INT64_MAX


def utf8_ok(s):
    try:
        s.encode("utf-8")
        return True
    except UnicodeEncodeError:  # a lone surrogate escape such as \ud800
        return False


def get(obj, *keys):
    for k in keys:
        if not isinstance(obj, dict) or obj.get(k) is None:
            return None
        obj = obj[k]
    return obj


def classify(raw, is_partial):
    """Return ("Q1".."Q4", None) or (None, canonical fields). First failing check wins (§2)."""
    if is_partial:
        return "Q1", None
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return "Q1", None
    if not isinstance(obj, dict):
        return "Q1", None
    texts = (obj.get("id"), obj.get("type"), get(obj, "actor", "login"), get(obj, "repo", "name"),
             get(obj, "payload", "action"))
    if any(isinstance(t, str) and not utf8_ok(t) for t in texts):  # G28: text fields must be UTF-8-writable
        return "Q1", None
    required = [("id",), ("type",), ("repo", "id"), ("actor", "id"), ("created_at",), ("public",), ("payload",)]
    if any(get(obj, *k) is None for k in required):
        return "Q2", None
    created = obj["created_at"]
    if not isinstance(created, str) or not RFC3339.fullmatch(created):
        return "Q3", None
    try:
        event_dt = datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return "Q3", None
    if not isinstance(obj["id"], str) or not is_int64(obj["repo"]["id"]) or not is_int64(obj["actor"]["id"]):
        return "Q4", None
    payload = obj["payload"]
    action = payload.get("action") if isinstance(payload, dict) else None
    etype = obj["type"]
    return None, {
        "record_hash": hashlib.sha256(raw[:-1] if raw.endswith(b"\r") else raw).hexdigest(),  # §2: no \r\n
        "event_id": obj["id"],
        "event_type": etype if isinstance(etype, str) else json.dumps(etype),
        "recognized": isinstance(etype, str) and etype in EVENT_TYPES,
        "repo_id": obj["repo"]["id"],
        "event_us": to_us(event_dt),
        "event_date": event_dt.strftime("%Y-%m-%d"),
        "is_star": etype == "WatchEvent" and action == "started",
    }


# ---------- the run ----------

CANON_TYPES = {"record_hash": "VARCHAR", "event_id": "VARCHAR", "event_type": "VARCHAR",
               "recognized": "BOOLEAN", "repo_id": "BIGINT", "event_us": "BIGINT",
               "event_date": "VARCHAR", "is_star": "BOOLEAN", "hour_us": "BIGINT", "line": "INTEGER"}
CSV_COLUMNS = "{" + ", ".join(f"'{c}': '{t}'" for c, t in CANON_TYPES.items()) + "}"


def run(input_dir, first, last, cutoffs, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    db = duckdb.connect(str(tmp / "reference.duckdb"))  # on disk: a month does not fit in RAM
    db.execute(f"SET temp_directory = '{tmp}'")
    db.execute("SET memory_limit = '3GB'")
    r1, registry = load(db, input_dir, first, last, tmp)
    write_outputs(db, r1, registry, cutoffs, out_dir)
    db.close()
    shutil.rmtree(tmp)


def load(db, input_dir, first, last, tmp):
    """Parse every requested hour into table `canon`; return (r1 counts, registry rows)."""
    db.execute(f"CREATE TABLE canon ({', '.join(f'{c} {t}' for c, t in CANON_TYPES.items())})")
    r1, registry = Counter({"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0, "canonical": 0}), []
    hour = first
    while hour <= last:
        status, lines = read_hour(input_dir / hour_file_name(hour))
        registry.append((hour.strftime(TS_FORMAT), status))
        hour_csv = tmp / "hour.csv"
        with open(hour_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for line_no, (raw, is_partial) in enumerate(lines, start=1):
                code, row = classify(raw, is_partial)
                if code:
                    r1[code] += 1
                    continue
                r1["canonical"] += 1
                row.update(hour_us=to_us(hour), line=line_no)
                w.writerow([row[c] for c in CANON_TYPES])
        db.execute(f"INSERT INTO canon SELECT * FROM read_csv('{hour_csv}', auto_detect = false, header = false, "
                   f"delim = ',', quote = '\"', escape = '\"', columns = {CSV_COLUMNS})")
        hour += timedelta(hours=1)
    return r1, registry


def write_outputs(db, r1, registry, cutoffs, out_dir):
    """Deduplicate `canon` (§3) and write R1-R7 (§6)."""
    # §3: keep the smallest (source_file_hour, source_line) per event_id.
    db.execute("""CREATE TABLE ranked AS SELECT *,
        row_number() OVER w AS rn,
        first_value(record_hash) OVER w AS kept_hash
        FROM canon WINDOW w AS (PARTITION BY event_id ORDER BY hour_us, line)""")
    db.execute("CREATE TABLE kept AS SELECT * FROM ranked WHERE rn = 1")

    write_csv(out_dir / "r1.csv", ["line_status", "count"], sorted(r1.items()))
    write_csv(out_dir / "r2.csv", ["source_file_hour", "event_type", "event_count"],
              [(fmt_ts(h), t, n) for h, t, n in db.execute(
                  "SELECT hour_us, event_type, count(*) FROM kept GROUP BY ALL ORDER BY ALL").fetchall()])
    write_csv(out_dir / "r3.csv", ["distinct_event_ids", "duplicate_count", "conflict_count"],
              db.execute("""SELECT count(*) FILTER (rn = 1), count(*) FILTER (rn > 1),
                  count(*) FILTER (rn > 1 AND record_hash <> kept_hash) FROM ranked""").fetchall())
    write_csv(out_dir / "r4.csv", ["repo_id", "event_date", "star_events"], db.execute(
        "SELECT repo_id, event_date, count(*) FROM kept WHERE is_star GROUP BY ALL ORDER BY ALL").fetchall())

    # §4/§6 R5: event_time in [t - 7d, t) and available_at <= t.
    r5 = []
    for t in sorted(cutoffs):
        t_us = to_us(t)
        r5 += [(fmt_ts(t_us), repo, n) for repo, n in db.execute(
            """SELECT repo_id, count(*) FROM kept WHERE is_star
               AND event_us >= ? AND event_us < ? AND hour_us + ? <= ?
               GROUP BY ALL ORDER BY ALL""",
            [t_us - 7 * 24 * US_PER_HOUR, t_us, (1 + LAG_L_HOURS) * US_PER_HOUR, t_us]).fetchall()]
    write_csv(out_dir / "r5.csv", ["cutoff", "repo_id", "star_events"], r5)

    write_csv(out_dir / "registry.csv", ["source_file_hour", "status"], registry)

    # §4: flags on kept occurrences, against the kept occurrence's source_file_hour.
    late, future, unrecognized = db.execute(
        """SELECT count(*) FILTER (event_us < hour_us - ?),
                  count(*) FILTER (event_us > hour_us + ?),
                  count(*) FILTER (NOT recognized) FROM kept""",
        [US_PER_HOUR, 2 * US_PER_HOUR]).fetchone()
    write_csv(out_dir / "flags.csv", ["flag", "count"],
              [("future_skewed", future), ("late", late), ("unrecognized_type", unrecognized)])


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def run_fixtures(fixtures_dir, out_root):
    for fx in sorted(p for p in fixtures_dir.iterdir() if (p / "fixture.json").exists()):
        spec = json.loads((fx / "fixture.json").read_text())
        first, last = (parse_hour(h) for h in spec["requested_hours"])
        run(fx / "input", first, last, [parse_hour(c) for c in spec["cutoffs"]], out_root / fx.name)
        print(f"ran {fx.name}")


def main(argv):
    if len(argv) >= 6 and argv[1] == "run":
        cutoffs = [parse_hour(argv[i + 1]) for i, a in enumerate(argv) if a == "--cutoff"]
        run(Path(argv[2]), parse_hour(argv[3]), parse_hour(argv[4]), cutoffs, Path(argv[5]))
    elif len(argv) == 4 and argv[1] == "fixtures":
        run_fixtures(Path(argv[2]), Path(argv[3]))
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
