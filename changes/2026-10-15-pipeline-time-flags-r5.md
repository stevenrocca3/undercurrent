# Change note: pipeline step 4, time flags and R5

**Date:** 2026-10-15 · **Spec:** v0.10 §4, §6 (R5, R7) · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/metrics.py` (new); `pipeline/__main__.py`, `fixtures/SPEC-GAPS.md`

## Why
Brief item 4: `available_at` for backfill, late and future-skewed flags over kept occurrences, and the point-in-time rule for R5.

## What changed
- Merged `origin/main` (spec v0.10, CI workflow, `changes/README.md`).
- Added **G30** to `SPEC-GAPS.md` as DECIDED (v0.10). Raw text was already the pipeline's behaviour, so no code change.
- **`available_at`** has been `source_file_hour + 1h + 6h` since step 2 (`canon.py`, `AVAILABILITY_LAG`). This step adds no code for it.
- **`pipeline/metrics.py`**, run over the `events` view (kept occurrences, step 3):
  - `flag_counts`: `future_skewed` is `event_time > source_file_hour + 2h` and `late` is `event_time < source_file_hour − 1h`, both strict. `unrecognized_type` means `event_type` is not in `fixtures/event_types.txt`, the canonical copy named in §2.
  - `stars_as_of`: for each cutoff `t`, star events (§6) with `t − 7d ≤ event_time < t` and `available_at ≤ t`, grouped by `repo_id`. Zero rows are omitted.
  - Cutoffs go to DuckDB as naive UTC. An aware datetime would be compared through the session time zone.
- `run` writes `r5.csv` and `flags.csv`. `flags.csv` always has its 3 rows.

## Proof
```
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py      → Ran 37 tests, OK
$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok '
  → 0/27 fixtures equal, FAIL. Every FAIL line is "missing in actual" (54 = r2, r4 × 27).
    r1, r3, r5, flags and registry are ok in 27/27, including F07, F08, F12, F26 and F27.
$ TZ=Asia/Kolkata .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out_tz   → the same result
```
I added no unit tests: F07, F08, F12, F26 and F27 already cover every boundary in this step.

## Left open
- **G31 (OPEN, raised by the reference agent):** repeated keys. The pipeline already lets the last one win (`parse_object`, and `json.loads` for nested objects), which is what G31 recommends.
- **`changes/README.md` index:** pipeline notes aren't listed, following its line "Pipeline notes live on the `pipeline` branch until it merges".
- Disk use at month scale is still unmeasured (see the step 3 note).
