# Change note: pipeline step 5, R2 and R4 (all R1–R7 files), plus one real hour

**Date:** 2026-10-15 · **Spec:** v0.11 §6 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/metrics.py`, `pipeline/__main__.py`, `check.sh`, `fixtures/SPEC-GAPS.md`

## What changed
- Merged `origin/main` (spec v0.11). Added **G31** to `SPEC-GAPS.md` as DECIDED. The pipeline already let the last key win at every level, so no code changed.
- **`metrics.py`:**
  - `events_by_hour_and_type` (R2): kept events grouped by `(source_file_hour, event_type)`.
  - `stars_by_repo_and_date` (R4): kept star events grouped by `(repo_id, UTC date of event_time)`.
  - Both use `ORDER BY ALL`, which in DuckDB is byte order for text.
- **`run`** now writes all seven files (§6).
- **`check.sh`** has two new steps after the existing ones: `python -m pipeline fixtures fixtures "$out/pipeline"`, then the comparator on that output.
- **G32 (OPEN, new):** month-scale disk use (see below).

## Proof
```
$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok \|^note '
27/27 fixtures equal
PASS
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py   → Ran 37 tests, OK
```
The two new `check.sh` steps, run on their own into a temp dir: `27/27 fixtures equal`, `PASS`. I couldn't run the full `./check.sh` here, because `reference/` isn't in this checkout.

## Real hour `2026-09-15-15` (data.gharchive.org: HTTP 200, 61,691,001 bytes; 296,464,186 bytes decompressed)
- **Run:** 8.7 s wall, 572 MB peak RSS. Registry `present`, 81,142 lines.
- **Line status:** canonical 81,136, Q2 6, other Q codes 0. All 6 Q2 lines have `"repo": {}`, so `repo.id` is missing.
- **Counts:** r3 is 81,136 distinct IDs with 0 duplicates. All flags are 0.
- **`canon.duckdb`: 286,273,536 bytes, or 3,528 bytes per canonical row.** Of that, `payload_raw` is 255.9 MB, stored `Uncompressed` per `pragma_storage_info`.
- **Month estimate:** 720 hours is about 200–250 GB, against about 31 GB free. That's G32. The time estimate is about 1.7 h for the month.
- **Reference comparison:** not done. The reference isn't in this checkout. Steven runs it with `compare_outputs.py dirs` (brief, "done" item 3).

## Left open
- **G32:** the month run is blocked until it's decided.
- **Brief step 6** (replay vs batch) is not started.
