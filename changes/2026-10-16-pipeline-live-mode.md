# Change note: clock.csv (G34) and live mode (brief `pipeline-live-ingestion.md` step 3)

**Date:** 2026-10-16 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/fetcher.py`, `pipeline/__main__.py`, `pipeline/ingest.py`, `pipeline/test_fetcher.py`, `pipeline/test_live.py`, `check.sh`, `BENCHMARKS.md`

## Why
G34 is decided (02 v0.6): clock offsets go to `clock.csv` (02 §5.4). Step 3: live mode (02 §6).

## What changed
- **Fetcher:** clock rows move to `clock.csv` (`checked_at, source, offset_seconds, error`); `offset_seconds` is signed from `chronyc tracking` ("fast" = positive), empty with the reason in `error` when unreadable. New helpers `final_outcomes` (the hour's `success`/`deadline` row) and `archived_file`; the manifest export uses them. Only the fetcher repairs a torn last log row; readers just skip it.
- **`HourRead`** takes an explicit `path` (None = missing) when `input_dir` is None.
- **`run --archive`:** INPUT_DIR is a fetcher root; each hour's file is the one its final outcome names (02 §6), never an archive listing, so `late`/`republished` files are never read. `http_status` fills `registry_evidence.csv`.
- **`python -m pipeline live ROOT FIRST LAST OUT [--cutoff] [--poll S]`:** the same replay loop, but before each hour it polls the fetch log until that hour has a final outcome, then uses its observed `available_at` (missing hours fall back to the backfill value, as the exported manifest does). Strict hour order (L5). FIRST must be at or after the fetcher's start hour. Outputs are written when LAST is done.
- `check.sh`: `pipeline/test_live.py` added to the fetcher test step.

## Proof
```
pipeline tests, 7 files                                 -> Ran 42 tests, OK (skipped=1)
/usr/bin/python3 -m unittest pipeline/test_fetcher.py   -> Python 3.9.6, OK (12)
tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out -> 32/32 fixtures equal, PASS
LIVE_REAL=1 ... test_real_september_hours               -> OK, 36.094 s, 3 real hours byte-identical
```
`test_live.py` runs the fetcher on a fake clock against a local server, with `live` in a thread polling the fetch log, then replays the archive with the exported manifest and compares all 9 output files byte for byte. F26: hour 1 succeeds before hour 0 and waits; hour 0 is republished at +24 h, and R1–R4, registry and flags still equal F26's expected files (first version kept). F23: truncated/unreadable hours go to the deadline and a never-published hour is missing.
`./check.sh` can't run here (no `reference/`); `tools/test_manifest_errors.py` fails only on its reference side.

## Open
- Live tables live in `OUT/canon.duckdb` until LAST is done; there is no resume of a stopped live run (rerunning from the archive gives the same result, by §8.1).
- The real-data test is opt-in (`LIVE_REAL=1`), so `check.sh` and CI don't need `~/undercurrent-data`.
