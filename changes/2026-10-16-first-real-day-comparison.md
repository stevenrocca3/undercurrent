# Change note: first real-data comparison, pipeline vs reference (one day)

**Date:** 2026-10-16
**Files:** `BENCHMARKS.md` (new rows), `changes/README.md` (index fix and this note). No code changed.
**Spec:** v0.12
**Status:** committed on `real-data-day1`, not pushed

## Result

**PASS.** On a full real day, the pipeline and the reference produce exactly equal R1–R7 output: 7/7 files, no differences.

| | |
|---|---|
| Input | GH Archive 2026-09-15, hours 0–23 (24 files, 1.0 GB gzip; SHA-256 of the 24 files concatenated in hour order begins `004b33b7e1396086`) |
| Lines | 1,789,869: 1,789,839 canonical, 30 Q2, 0 Q1/Q3/Q4 |
| r3 | 1,789,839 distinct, 0 duplicates, 0 conflicts |
| Flags | 0 late, 0 future-skewed, 0 unrecognized types |
| Registry | 24 present |
| Rows compared | r2 384, r4 28,862, r5 28,528 (cutoffs `2026-09-15T12:00:00Z`, `2026-09-16T00:00:00Z`) |

| | Wall time | Peak memory |
|---|---|---|
| reference | 92.24 s | 1,331 MB |
| pipeline | 508.94 s | 322 MB (`canon.duckdb` 98.1 B/row) |

## What it proves and what it doesn't

- **Proves:** two independently written implementations agree on every compared count for 1.79M real events, including quarantine, dedup, R4 star dates and R5 point-in-time windows.
- **Doesn't prove:**
  - **Correctness against the source.** Both could share a misreading of the spec; that's what §5.2 BigQuery reconciliation is for.
  - **Rare cases.** This day had no duplicates, conflicts, flags or truncated hours, so those paths were tested by fixtures only.
  - **Month scale.**

## Observations

- **The pipeline is 5.5× slower than the reference** on a real day (509 s vs 92 s), and slower than its own estimate (6.4 s/hour from one hour → 21 s/hour here). Month estimate: about 4.2 h. That's acceptable for Gate 1, but worth raising with the pipeline agent.
- **The pipeline uses 4× less memory** (322 MB vs 1,331 MB).

## Reproduce

Data in `~/undercurrent-data/gharchive/` (download: `curl -O https://data.gharchive.org/2026-09-15-{0..23}.json.gz`).

```
reference/reference.py run IN 2026-09-15T00:00:00Z 2026-09-15T23:00:00Z OUT/reference --cutoff 2026-09-15T12:00:00Z --cutoff 2026-09-16T00:00:00Z
python -m pipeline run    IN 2026-09-15T00:00:00Z 2026-09-15T23:00:00Z OUT/pipeline  (same cutoffs; run from the pipeline checkout)
tools/compare_outputs.py dirs OUT/reference OUT/pipeline
```

The reference agent **ran** the pipeline from its own checkout and did not read its code (§6).
