"""Write the delay report from a live fetcher root (02-live-ingestion.md §7).

    python tools/delay_report.py ROOT OUT_FILE

ROOT holds `fetch_log.csv` and `clock.csv` (02 §5.2, §5.4). For every hour with
a `success` final outcome, delay = available_at - due time (h + 1 h). Missing and
ingested-truncated hours (`deadline` rows) are counted, never folded into the
delay distribution. Percentiles are nearest-rank (G35). The proposed
`L` is the p99 rounded up to a whole hour (01 §4).

Standard library only; imports neither implementation.
"""

import csv
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

P_SECONDS = 300  # 02 §3


def instant(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def nearest_rank(sorted_values, q):
    return sorted_values[max(1, math.ceil(q * len(sorted_values))) - 1]


def report(root):
    with open(root / "fetch_log.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(root / "clock.csv", newline="", encoding="utf-8") as f:
        clock = list(csv.DictReader(f))
    hours = sorted({r["source_file_hour"] for r in rows})
    final = {r["source_file_hour"]: r for r in rows if r["outcome"] in ("success", "deadline")}
    delays = sorted(
        (instant(r["available_at"]) - instant(h) - timedelta(hours=1)).total_seconds()
        for h, r in final.items() if r["outcome"] == "success")
    deadline = [r for r in final.values() if r["outcome"] == "deadline"]
    out = {
        "window_start": hours[0] if hours else None,
        "window_end": hours[-1] if hours else None,
        "hours_tracked": len(hours),
        "succeeded": len(delays),
        "missing": sum(1 for r in deadline if not r["sha256"]),
        "ingested_truncated": sum(1 for r in deadline if r["sha256"]),
        "republished": len({r["source_file_hour"] for r in rows if r["outcome"] == "republished"}),
        "no_final_outcome_yet": len(hours) - len(final),
        "delay_seconds": None,
        "proposed_L_hours": None,
        "P_seconds": P_SECONDS,
        "clock_offsets": clock,
    }
    if delays:
        out["delay_seconds"] = {
            "min": delays[0], "p50": nearest_rank(delays, 0.50), "p90": nearest_rank(delays, 0.90),
            "p99": nearest_rank(delays, 0.99), "max": delays[-1]}
        out["proposed_L_hours"] = math.ceil(out["delay_seconds"]["p99"] / 3600)
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    out = report(Path(argv[1]))
    Path(argv[2]).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"{out['succeeded']} delays, proposed L = {out['proposed_L_hours']} h")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
