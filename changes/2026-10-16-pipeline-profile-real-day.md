# Change note: pipeline profile on a real day (no code change)

**Date:** 2026-10-16 · **Status:** committed locally on `pipeline`, not pushed · **Files:** `BENCHMARKS.md`
Also merged `origin/main`. Its `BENCHMARKS.md` conflicted with the pipeline's rows; both sets of rows were appended, so I kept both, in date order.

## Why
The real-day comparison (`changes/2026-10-16-first-real-day-comparison.md`) recorded 508.94 s for the pipeline against 92.24 s for the reference on 2026-09-15. Steven asked where the time goes.

## Measured (default machine, input `~/undercurrent-data/gharchive/`, 24 hours, 1,789,869 lines)
**1. Phase timings.** A driver script in the scratchpad calls the pipeline's own functions and times each phase. Run on code `f639320`:

| Phase | Seconds | Share |
|---|---|---|
| `classify` (Python-level parse of the top-level object, Q1–Q4) | 65.5 | 53% |
| `add` (`json.dumps` of 18 columns per row, plus SHA-256, to the spool file) | 35.6 | 29% |
| `load` (DuckDB `read_json` insert) | 11.9 | 10% |
| `read` (zlib inflate, split into lines) | 11.4 | 9% |
| dedup + R2/R4/R5/flags | 0.2 | 0% |
| **total** | **124.6** | |

**2. The real command, same code, otherwise idle machine:**
`python -m pipeline run ~/undercurrent-data/gharchive 2026-09-15T00:00:00Z 2026-09-15T23:00:00Z OUT --cutoff 2026-09-15T12:00:00Z --cutoff 2026-09-16T00:00:00Z`
gave **124.36 s** wall and 328 MB max RSS. r1 was canonical 1,789,839 and Q2 30, the same as the recorded run.

## Finding
- **508.94 s doesn't reproduce.** The same code takes 124.36 s, so the recorded run was most likely slowed by other load on the machine; I can't confirm that from here. The real gap to the reference is 124 s vs 92 s (1.35×), not 5.5×.
- **Top 3 costs:** `classify` 53%, `add` 29%, `load` 10%. DuckDB dedup and the metrics are negligible.

## Left open
The speed-up itself is in a separate note.
