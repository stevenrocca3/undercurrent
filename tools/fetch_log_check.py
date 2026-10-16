"""Fetch log consistency (02-live-ingestion.md §8.4, §9 criteria 1 and 4).

    python tools/fetch_log_check.py ROOT FIRST_HOUR LAST_HOUR

ROOT holds `fetch_log.csv` and `archive/YYYY-MM-DD-H/<sha256>.json.gz`. Checks:
every hour FIRST..LAST (inclusive) has exactly one final outcome, and no logged
hour has more than one; every file a final outcome names is archived with that
SHA-256; and every archived file is named by some fetch-log row of its hour.
Prints each failure and exits 1 if there are any.

Standard library only; imports neither implementation.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

from archive_input import FINAL, hour_name, sha256
from gate1_evidence import hours


def problems(root, first, last):
    with open(root / "fetch_log.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    finals = Counter(r["source_file_hour"] for r in rows if r["outcome"] in FINAL)
    out = [f"{h}: no final outcome" for h in hours(first, last) if finals[h] == 0]
    out += [f"{h}: {n} final outcomes" for h, n in sorted(finals.items()) if n > 1]
    for r in rows:
        if r["outcome"] in FINAL and r["sha256"]:
            f = root / "archive" / hour_name(r["source_file_hour"]) / f"{r['sha256']}.json.gz"
            if not f.is_file() or sha256(f) != r["sha256"]:
                out.append(f"{f}: absent or SHA-256 differs from the fetch log")
    named = {(hour_name(r["source_file_hour"]), r["sha256"]) for r in rows if r["sha256"]}
    for f in sorted((root / "archive").glob("*/*.json.gz")):
        if (f.parent.name, f.name.removesuffix(".json.gz")) not in named:
            out.append(f"{f}: archived but named by no fetch-log row")
    return out


def main(argv):
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    found = problems(Path(argv[1]), argv[2], argv[3])
    for p in found:
        print(p)
    print(f"{len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
