# Change note: pipeline step 6, replay vs batch

**Date:** 2026-10-16 · **Spec:** v0.12 §4 Replay, §8 criterion 3, G29 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/dedup.py`, `pipeline/canon.py`, `pipeline/__main__.py`, `pipeline/test_replay.py` (new), `pipeline/test_dedup.py`, `check.sh`, `BENCHMARKS.md`

## What changed
- **`--replay`** (on both `run` and `fixtures`) feeds the hour files one at a time in `source_file_hour` order, in one process, with their original `available_at` (§4 backfill). It deduplicates each hour as it arrives.
- **Batch** is unchanged: hours are read in parallel, then deduplicated once.
- **`dedup.py`:** one query serves both modes. Replay restricts it to the new hour, plus the rows already kept from earlier hours with the same `event_id`. The tables and views are now created up front (`create_dedup_tables`), and `r3_counts` is split out.
- **`canon_digest.csv`** (`table,rows,sha256`) is written by every run. It covers `canon` (without `ingested_at` and `source_last_modified`, per G29), `quarantine` and `duplicates`. Each row is hashed as DuckDB `to_json` text plus LF, sorted by `(source_file_hour, source_line)`. It isn't one of the R1–R7 files, so the comparator only notes it.
- **Tests:**
  - `test_replay.py` checks that every fixture produces byte-identical R1–R7 files and `canon_digest.csv` in both modes, and that the digest ignores `ingested_at` and `source_last_modified` but not data columns.
  - `test_dedup.py` checks replay hour by hour against batch, with duplicates and conflicts across hours.
  - `check.sh` runs both.

## Proof
```
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py      → Ran 41 tests, OK
$ python -m pipeline fixtures fixtures /tmp/po_b ; python -m pipeline fixtures fixtures /tmp/po_r --replay
  compare_outputs.py fixtures (each)   → 27/27 fixtures equal, PASS (both)
  diff -r -x canon.duckdb /tmp/po_b /tmp/po_r   → no differences (27 canon_digest.csv identical)
$ python -m pipeline run ~/undercurrent-data/gharchive 2026-09-15T00:00:00Z 2026-09-15T23:00:00Z OUT [--replay] \
      --cutoff 2026-09-15T12:00:00Z --cutoff 2026-09-16T00:00:00Z
  batch 44.99 s, replay 88.17 s; cmp canon_digest.csv → identical; compare_outputs.py dirs → PASS
  canon,1789839,7cbd365c…  quarantine,30,8764e56c…  duplicates,0,e3b0c442…
  batch vs the pre-step-6 output (56878e6) → PASS
```
The brief asks for at least two real hours; this is 24.

## Left open
- **The digest costs batch time:** the day went from 34.10 s to 44.99 s, because all rows are fetched into Python and hashed. That's about 5 min for the month (an estimate).
- **Replay is not built for the month.** Each hour's dedup checks the new hour's IDs against all earlier rows, so its cost grows with the number of hours. It's meant for this check, not the production run.
- **The real day has 0 duplicates**, so replay's dedup across hours is exercised only by fixtures F02, F03, F04, F24 and F26, plus the unit test.
- This is the last brief item. Brief criteria 1 and 3 (the full `./check.sh` and the real-data run against the reference) need Steven's main checkout.
