"""Gate 1 pipeline (spec 01-event-semantics.md v0.11).

    python -m pipeline run INPUT_DIR FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...] [--replay] [--available-at FILE]
    python -m pipeline fixtures FIXTURES_DIR OUT_ROOT [--replay]
    python -m pipeline live FETCHER_ROOT FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...] [--poll SECONDS]

Batch (default) reads hours in parallel and deduplicates once at the end.
--replay feeds the hour files one at a time in source_file_hour order and
deduplicates each as it arrives (§4 Replay). Both write canon_digest.csv;
on the same input the two files must be identical (§8 criterion 3).

--available-at FILE reads a 02 §8 manifest: listed hours take its available_at,
the rest the §4 backfill value. Fixtures use available_at.csv beside fixture.json.

--archive reads INPUT_DIR as a fetcher root (02 §5): each hour's file is the one
its fetch-log final outcome names (02 §6), and http_status fills the registry
evidence. `live` is replay on a fetcher root that waits for each hour's final
outcome, in hour order, and takes the observed available_at (02 §6). FIRST_HOUR
must be at or after the fetcher's start hour. Live = a replay with --archive and
the exported manifest (02 §8.1).

Hours are inclusive, e.g. 2026-09-01T00:00:00Z. Writes canon.duckdb (canon-v1,
quarantine, and the dedup tables), the R1-R7 files r1..r5.csv, registry.csv
and flags.csv, registry_evidence.csv and canon_digest.csv.
"""

import argparse
import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from pipeline.canon import CanonStore, available_at, read_manifest, spool_hour, table_digests
from pipeline.dedup import create_dedup_tables, deduplicate, r3_counts
from pipeline.metrics import events_by_hour_and_type, flag_counts, stars_as_of, stars_by_repo_and_date
from pipeline.fetcher import archived_file, final_outcomes, parse_instant
from pipeline.ingest import HourRead, format_instant, format_timestamp, parse_timestamp, requested_hours


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


def run(input_dir, first, last, out_dir, cutoffs, replay=False, manifest=None, archive=False, live_poll=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    store = CanonStore(out_dir / "canon.duckdb", datetime.now(timezone.utc))
    line_status = Counter({code: 0 for code in R1_ROWS})
    reads = []
    create_dedup_tables(store.con)
    hours = list(requested_hours(first, last))
    manifest = dict(manifest or {})
    finals = final_outcomes(input_dir) if archive else {}
    http = {}

    def hour_read(hour):
        """The hour's HourRead; in live mode, first wait for its final outcome and take its available_at."""
        nonlocal finals
        if not archive:
            return HourRead(input_dir, hour)
        while live_poll and hour not in finals:
            time.sleep(live_poll)
            finals = final_outcomes(input_dir)
        row = finals.get(hour)
        if row is None:
            return HourRead(None, hour)
        http[hour] = row["http_status"]
        if live_poll and row["available_at"]:
            manifest[hour.replace(tzinfo=None)] = parse_instant(row["available_at"]).replace(tzinfo=None)
        return HourRead(None, hour, path=archived_file(input_dir, row))

    available = {}
    if replay or live_poll:
        for hour in hours:  # one file at a time, in source_file_hour order
            read = hour_read(hour)
            available[hour] = available_at(hour, manifest)
            read, counts = spool_hour(read, out_dir)
            line_status.update(counts)
            store.load_hour(hour, out_dir, available[hour])
            deduplicate(store.con, hour.replace(tzinfo=None))
            reads.append(read)
    else:
        # Hours are read and classified in parallel; results come back in hour order and are loaded one by one.
        with ProcessPoolExecutor() as pool:
            hour_reads = [hour_read(h) for h in hours]
            available = {h: available_at(h, manifest) for h in hours}
            for read, counts in pool.map(spool_hour, hour_reads, [out_dir] * len(hours)):
                line_status.update(counts)
                store.load_hour(read.hour, out_dir, available[read.hour])
                reads.append(read)
        deduplicate(store.con)
    r3 = r3_counts(store.con)
    digests = table_digests(store.con)
    r2 = events_by_hour_and_type(store.con)
    r4 = stars_by_repo_and_date(store.con)
    flags = flag_counts(store.con)
    r5 = stars_as_of(store.con, cutoffs)
    store.close()
    write_csv(out_dir / "r1.csv", ["line_status", "count"], sorted(line_status.items()))
    write_csv(out_dir / "r2.csv", ["source_file_hour", "event_type", "event_count"],
              [[format_timestamp(h), event_type, n] for h, event_type, n in r2])
    write_csv(out_dir / "r3.csv", ["distinct_event_ids", "duplicate_count", "conflict_count"], [r3])
    write_csv(out_dir / "r4.csv", ["repo_id", "event_date", "star_events"],
              [[repo_id, f"{day:%Y-%m-%d}", n] for repo_id, day, n in r4])
    write_csv(out_dir / "r5.csv", ["cutoff", "repo_id", "star_events"],
              [[format_timestamp(t), repo_id, n] for t, repo_id, n in r5])
    write_csv(out_dir / "flags.csv", ["flag", "count"], flags)
    write_csv(out_dir / "registry.csv", ["source_file_hour", "status"],
              [[format_timestamp(r.hour), r.status] for r in reads])
    write_csv(out_dir / "canon_digest.csv", ["table", "rows", "sha256"], digests)
    write_csv(out_dir / "registry_evidence.csv",
              ["source_file_hour", "status", "file_bytes", "lines", "error", "http_status", "available_at"],
              [[format_timestamp(r.hour), r.status, "" if r.file_bytes is None else r.file_bytes,
                r.line_count, r.error, http.get(r.hour, ""), format_instant(available[r.hour])] for r in reads])


def run_fixtures(fixtures_dir, out_root, replay=False):
    for fx in sorted(p for p in fixtures_dir.iterdir() if (p / "fixture.json").is_file()):
        spec = json.loads((fx / "fixture.json").read_text())
        first, last = (parse_timestamp(h) for h in spec["requested_hours"])
        cutoffs = [parse_timestamp(t) for t in spec["cutoffs"]]
        manifest_path = fx / "available_at.csv"
        manifest = read_manifest(manifest_path) if manifest_path.is_file() else None
        run(fx / "input", first, last, out_root / fx.name, cutoffs, replay, manifest)


def main(argv):
    parser = argparse.ArgumentParser(prog="python -m pipeline")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("input_dir", type=Path)
    p_run.add_argument("first_hour", type=parse_timestamp)
    p_run.add_argument("last_hour", type=parse_timestamp)
    p_run.add_argument("out_dir", type=Path)
    p_run.add_argument("--cutoff", type=parse_timestamp, action="append", default=[])
    p_run.add_argument("--replay", action="store_true")
    p_run.add_argument("--available-at", type=Path)
    p_run.add_argument("--archive", action="store_true", help="INPUT_DIR is a fetcher root (02 §5)")
    p_fx = sub.add_parser("fixtures")
    p_fx.add_argument("fixtures_dir", type=Path)
    p_fx.add_argument("out_root", type=Path)
    p_fx.add_argument("--replay", action="store_true")
    p_live = sub.add_parser("live")
    p_live.add_argument("fetcher_root", type=Path)
    p_live.add_argument("first_hour", type=parse_timestamp)
    p_live.add_argument("last_hour", type=parse_timestamp)
    p_live.add_argument("out_dir", type=Path)
    p_live.add_argument("--cutoff", type=parse_timestamp, action="append", default=[])
    p_live.add_argument("--poll", type=float, default=60, help="seconds between fetch-log reads")
    args = parser.parse_args(argv)
    if args.mode == "run":
        run(args.input_dir, args.first_hour, args.last_hour, args.out_dir, args.cutoff, args.replay,
            read_manifest(args.available_at) if args.available_at else None, args.archive)
    elif args.mode == "live":
        run(args.fetcher_root, args.first_hour, args.last_hour, args.out_dir, args.cutoff, archive=True,
            live_poll=args.poll)
    else:
        run_fixtures(args.fixtures_dir, args.out_root, args.replay)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
