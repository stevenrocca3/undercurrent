"""Source reconciliation against BigQuery GH Archive (01-event-semantics.md §5.2, §8 criterion 4).

    python tools/reconcile.py OURS_DIR THEIRS_DIR OUT_DIR [--categories FILE]

OURS_DIR holds our r2.csv, r4.csv and registry.csv (§6 contract).
THEIRS_DIR holds the three exports of tools/bigquery/*.sql:
    type_by_hour.csv   hour,event_type,event_count
    ids_by_hour.csv    hour,distinct_event_ids
    stars.csv          repo_id,event_date,star_events   (top 1,000 repos only)

One cell per key, over the union of keys on both sides (a missing side is 0):
    type_by_hour  (hour, event_type)  ours = r2
    ids_by_hour   hour                ours = r2 summed over types (one kept row per event_id)
    stars         (repo_id, date)     ours = r4, restricted to the repos in stars.csv

Tolerance (OPEN-3, fixed in advance): |ours - theirs| / theirs <= 0.001;
theirs = 0 with ours != 0 is out of tolerance.

Every out-of-tolerance cell gets one category, first match wins:
    1. --categories FILE (metric,key,category,reason): a finding written down by
       whoever investigated the cell; the reason is copied into the report.
    2. missing_hour_ours: our registry status for the cell's hour is not "present".
    3. missing_hour_theirs: BigQuery has no events at all in the cell's hour.
    4. unexplained.

Writes OUT_DIR/reconciliation.csv (every cell) and OUT_DIR/reconciliation.json
(counts and pass). Exit 0 = pass (zero unexplained), 1 = fail, 2 = usage error.

Standard library only. Must not import anything from the pipeline codebase.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

TOLERANCE = 0.001
CATEGORIES = {"missing_hour_ours", "missing_hour_theirs", "dedup_policy",
              "parse_or_schema", "time_bucketing", "unexplained"}
FIELDS = ["metric", "key", "ours", "theirs", "rel_diff", "within_tolerance", "category", "reason"]


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def counts(rows, key_cols, value_col):
    out = Counter()
    for r in rows:
        out["|".join(r[c] for c in key_cols)] += int(r[value_col])
    return out


def rel_diff(ours, theirs):
    if theirs == 0:
        return 0.0 if ours == 0 else float("inf")
    return abs(ours - theirs) / theirs


def build_cells(ours_dir, theirs_dir):
    """{metric: (ours Counter, theirs Counter)}"""
    r2 = read(ours_dir / "r2.csv")
    stars_theirs = counts(read(theirs_dir / "stars.csv"), ["repo_id", "event_date"], "star_events")
    top_repos = {k.split("|")[0] for k in stars_theirs}
    stars_ours = counts([r for r in read(ours_dir / "r4.csv") if r["repo_id"] in top_repos],
                        ["repo_id", "event_date"], "star_events")
    return {
        "type_by_hour": (counts(r2, ["source_file_hour", "event_type"], "event_count"),
                         counts(read(theirs_dir / "type_by_hour.csv"), ["hour", "event_type"], "event_count")),
        "ids_by_hour": (counts(r2, ["source_file_hour"], "event_count"),
                        counts(read(theirs_dir / "ids_by_hour.csv"), ["hour"], "distinct_event_ids")),
        "stars": (stars_ours, stars_theirs),
    }


def reconcile(ours_dir, theirs_dir, overrides=()):
    """Return (cells, summary). overrides: rows with metric,key,category,reason."""
    manual = {(o["metric"], o["key"]): o for o in overrides}
    bad = {o["category"] for o in manual.values()} - CATEGORIES
    if bad:
        raise ValueError(f"unknown categories: {sorted(bad)}")
    status = {r["source_file_hour"]: r["status"] for r in read(ours_dir / "registry.csv")}
    metrics = build_cells(ours_dir, theirs_dir)
    their_hours = {h for h, n in metrics["ids_by_hour"][1].items() if n > 0}

    cells = []
    for metric, (ours, theirs) in metrics.items():
        for key in sorted(ours.keys() | theirs.keys()):
            d = rel_diff(ours[key], theirs[key])
            cell = {"metric": metric, "key": key, "ours": ours[key], "theirs": theirs[key],
                    "rel_diff": f"{d:.6f}", "within_tolerance": d <= TOLERANCE,
                    "category": "", "reason": ""}
            if not cell["within_tolerance"]:
                hour = key.split("|")[0] if metric != "stars" else None
                if (metric, key) in manual:
                    cell["category"] = manual[metric, key]["category"]
                    cell["reason"] = manual[metric, key]["reason"]
                elif hour and status.get(hour, "missing") != "present":
                    cell["category"] = "missing_hour_ours"
                elif hour and hour not in their_hours:
                    cell["category"] = "missing_hour_theirs"
                else:
                    cell["category"] = "unexplained"
            cells.append(cell)

    out = [c for c in cells if not c["within_tolerance"]]
    summary = {
        "tolerance": TOLERANCE,
        "cells": dict(Counter(c["metric"] for c in cells)),
        "out_of_tolerance": len(out),
        "by_category": dict(Counter(c["category"] for c in out)),
        "unexplained": sum(c["category"] == "unexplained" for c in out),
    }
    summary["pass"] = summary["unexplained"] == 0
    return cells, summary


def main(argv):
    args = argv[1:]
    overrides = []
    if "--categories" in args:
        i = args.index("--categories")
        overrides = read(Path(args[i + 1]))
        del args[i:i + 2]
    if len(args) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    ours_dir, theirs_dir, out_dir = map(Path, args)
    try:
        cells, summary = reconcile(ours_dir, theirs_dir, overrides)
    except (OSError, KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "reconciliation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(cells)
    (out_dir / "reconciliation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
