"""Build a flat input folder from a live fetcher root (02 §5, §6, §8.4).

    python tools/archive_input.py ROOT OUT_DIR

ROOT holds `fetch_log.csv` and `archive/YYYY-MM-DD-H/<sha256>.json.gz`. For every
hour, the final outcome (a `success` or `deadline` row) names the one file that
is ingested; OUT_DIR gets `YYYY-MM-DD-H.json.gz` as a symlink to it. A `deadline`
row without a file is a missing hour: no link. `late` and `republished` files
are never linked.

Stops (exit 1) if an hour has more than one final row, or a named file is absent
or its SHA-256 differs. Standard library only; imports neither implementation.
"""

import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

FINAL = {"success", "deadline"}


def hour_name(source_file_hour):
    h = datetime.strptime(source_file_hour, "%Y-%m-%dT%H:00:00Z")
    return f"{h:%Y-%m-%d}-{h.hour}"


def sha256(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            d.update(block)
    return d.hexdigest()


def build(root, out):
    with open(root / "fetch_log.csv", newline="", encoding="utf-8") as f:
        finals = [r for r in csv.DictReader(f) if r["outcome"] in FINAL]
    names = [hour_name(r["source_file_hour"]) for r in finals]
    twice = sorted({n for n in names if names.count(n) > 1})
    if twice:
        raise ValueError(f"more than one final outcome for {twice} (02 §8.4)")
    out.mkdir(parents=True, exist_ok=True)
    for name, r in zip(names, finals):
        if not r["sha256"]:
            continue
        src = root / "archive" / name / f"{r['sha256']}.json.gz"
        if not src.is_file() or sha256(src) != r["sha256"]:
            raise ValueError(f"{src}: absent or SHA-256 differs from the fetch log (02 §8.4)")
        (out / f"{name}.json.gz").symlink_to(src.resolve())
    return len(finals)


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        n = build(Path(argv[1]), Path(argv[2]))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{n} hours with a final outcome")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
