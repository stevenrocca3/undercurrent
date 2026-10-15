# Change note: pipeline stores `payload_raw` as null (G32)

**Date:** 2026-10-15 · **Spec:** v0.12 §2 (`payload_raw` in Gate 1) · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/canon.py`, `fixtures/SPEC-GAPS.md`, `BENCHMARKS.md`

## Why
At 3,528 B per row, a month of `payload_raw` would be 200–250 GB, against about 29 GB free (step 5 note). Steven chose option (a), and spec v0.12 now says Gate 1 runs store `payload_raw` as null.

## What changed
- Merged `origin/main` (spec v0.12, `BENCHMARKS.md`, a brief line saying every measurement goes in `BENCHMARKS.md`).
- **`canon.py`:**
  - `classify` no longer takes the payload's raw text; `payload_raw` is always None.
  - The column is now nullable `VARCHAR`.
  - `parse_object` still keeps raw text, because a non-string `type` needs it (G30).
  - The G28 check never looked at the payload, so Q1–Q4 behaviour is unchanged.
- **`SPEC-GAPS.md`:** G32 marked DECIDED (v0.12), option (a).
- **`BENCHMARKS.md`:** three new rows (correctness, measured performance, estimate). No old rows were edited.

## Proof
```
$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok \|^note '
27/27 fixtures equal
PASS
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py   → Ran 37 tests, OK
$ /usr/bin/time -l .venv/bin/python -m pipeline run <scratch>/real/in 2026-09-15T15:00:00Z 2026-09-15T15:00:00Z <scratch>/real/out --cutoff 2026-09-22T00:00:00Z
  6.39 real, 124,272,640 max RSS
  r1: Q1 0, Q2 6, Q3 0, Q4 0, canonical 81136   (unchanged from step 5)
  canon.duckdb 7,614,464 B; 81,136 canon rows, 0 non-null payload_raw → 93.8 B/row
```
The input is `2026-09-15-15.json.gz` from data.gharchive.org (61,691,001 B, SHA-256 prefix `6c5def0c63c6574d`). The file size covers every table in the database (canon, quarantine, duplicates). Quarantine has 6 rows and duplicates has 0, so nearly all of it is `canon`.

**Estimate:** 5.5–6.6 GB for the month (see `BENCHMARKS.md`). That fits on the disk.

## Left open
- Brief step 6 (replay vs batch) is not started.
