# Change note: pipeline speed-up (3.6× on a real day)

**Date:** 2026-10-16 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/canon.py`, `pipeline/__main__.py`, `pipeline/test_canon.py`, `BENCHMARKS.md`

## Why
The profile (`2026-10-16-pipeline-profile-real-day.md`) found three top costs: `classify` 53%, writing spool rows 29%, loading 10%. Steven asked for the changes I proposed.

## What changed
1. **`classify`** decodes with the stdlib C scanner (`DECODER.decode`). The grammar is the same: `NaN` and `Infinity` are rejected, a BOM or trailing data is Q1, and the last repeated key wins (G31). `parse_object`'s slower raw-text parse now runs only when `type` is present and not a string (G30).
2. **Spool rows** carry only the 13 per-row fields. `source_file_hour`, `available_at`, `ingested_at` and `schema_version` are bound as SQL parameters at load time; `payload_raw` and `source_last_modified` are `NULL` in the SQL. `event_time` is written with `isoformat`.
3. **Parallel hours:**
   - `spool_hour` reads and classifies one hour into its own spool files, in a `ProcessPoolExecutor` (one worker per core).
   - `pool.map` returns the hours in order, and the main process loads each hour into DuckDB and deletes its spool files.
   - The tables keep the same row order as a serial run. Dedup depends only on `(source_file_hour, source_line)`, so results can't depend on which worker finishes first.
- **New test:** a non-string `type` keeps its raw text `[1, 2]`, and the last `type` key wins over an earlier string.

## Proof
```
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok \|^note '
27/27 fixtures equal
PASS
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py   → Ran 38 tests, OK
$ /usr/bin/time -l python -m pipeline run ~/undercurrent-data/gharchive 2026-09-15T00:00:00Z 2026-09-15T23:00:00Z OUT \
      --cutoff 2026-09-15T12:00:00Z --cutoff 2026-09-16T00:00:00Z
  before (bfcb830 code = f639320): 124.36 s   after: 34.10 s real, 119.25 s user
$ compare_outputs.py dirs BEFORE AFTER                      → PASS (all 7 files)
$ DuckDB EXCEPT ALL both ways, canon EXCLUDE (ingested_at)  → canon 1,789,839 rows, 0 differ; quarantine 30 rows, 0 differ
```
Peak memory is 724 MB summed across all processes (`ps` sampled every 0.5 s); the largest single process is 324 MB. Estimate for the month: 34.10 s × 30 = 17 min.

## Left open
- The fixtures run is slower, 7.1 s, because each of the 27 fixtures starts its own pool. That's still fast enough for `check.sh`.
- Worker count defaults to the core count (8). It isn't configurable; nothing needs that yet.
