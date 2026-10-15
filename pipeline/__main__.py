"""Gate 1 pipeline (spec 01-event-semantics.md v0.8).

    python -m pipeline run INPUT_DIR FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...]
    python -m pipeline fixtures FIXTURES_DIR OUT_ROOT

Hours are inclusive, e.g. 2026-09-01T00:00:00Z. Writes canon.duckdb (canon-v1,
quarantine, and the dedup tables), r1.csv, r3.csv, registry.csv (R6) and
registry_evidence.csv; later steps add r2, r4, r5 and flags.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pipeline.canon import CanonStore, classify
from pipeline.dedup import deduplicate
from pipeline.ingest import HourRead, format_timestamp, parse_timestamp, requested_hours


def csv_cell(text):
    """RFC 4180 quoting (§6): quote only cells containing , " or a line break."""
    if any(c in text for c in ',"\r\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        for row in [header, *rows]:
            f.write(",".join(csv_cell(str(cell)) for cell in row) + "\n")


R1_ROWS = ["Q1", "Q2", "Q3", "Q4", "canonical"]  # always present (§6)


def run(input_dir, first, last, out_dir, cutoffs):
    out_dir.mkdir(parents=True, exist_ok=True)
    store = CanonStore(out_dir / "canon.duckdb", datetime.now(timezone.utc))
    line_status = Counter({code: 0 for code in R1_ROWS})
    reads = []
    for hour in requested_hours(first, last):
        read = HourRead(input_dir, hour)
        store.begin_hour(hour)
        for source_line, raw, partial in read.lines():
            code, fields = classify(raw, partial)
            line_status[code] += 1
            store.add(source_line, raw, code, fields)
        store.end_hour()
        reads.append(read)
    r3 = deduplicate(store.con)
    store.close()
    write_csv(out_dir / "r1.csv", ["line_status", "count"], sorted(line_status.items()))
    write_csv(out_dir / "r3.csv", ["distinct_event_ids", "duplicate_count", "conflict_count"], [r3])
    write_csv(out_dir / "registry.csv", ["source_file_hour", "status"],
              [[format_timestamp(r.hour), r.status] for r in reads])
    write_csv(out_dir / "registry_evidence.csv",
              ["source_file_hour", "status", "file_bytes", "lines", "error"],
              [[format_timestamp(r.hour), r.status, "" if r.file_bytes is None else r.file_bytes,
                r.line_count, r.error] for r in reads])


def run_fixtures(fixtures_dir, out_root):
    for fx in sorted(p for p in fixtures_dir.iterdir() if (p / "fixture.json").is_file()):
        spec = json.loads((fx / "fixture.json").read_text())
        first, last = (parse_timestamp(h) for h in spec["requested_hours"])
        cutoffs = [parse_timestamp(t) for t in spec["cutoffs"]]
        run(fx / "input", first, last, out_root / fx.name, cutoffs)


def main(argv):
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("input_dir", type=Path)
    p_run.add_argument("first_hour", type=parse_timestamp)
    p_run.add_argument("last_hour", type=parse_timestamp)
    p_run.add_argument("out_dir", type=Path)
    p_run.add_argument("--cutoff", type=parse_timestamp, action="append", default=[])
    p_fx = sub.add_parser("fixtures")
    p_fx.add_argument("fixtures_dir", type=Path)
    p_fx.add_argument("out_root", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "run":
        run(args.input_dir, args.first_hour, args.last_hour, args.out_dir, args.cutoff)
    else:
        run_fixtures(args.fixtures_dir, args.out_root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
