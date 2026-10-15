# Change note: tidy `canon.py` (no behaviour change)

**Date:** 2026-10-16 · **Status:** committed locally on `pipeline`, not pushed · **Files:** `pipeline/canon.py`

## Why
Steven asked for a pass to remove anything unnecessary. The pipeline is already small: 507 lines of code and 196 of tests. Only `canon.py` had real redundancy.

## What changed
- `CanonStore`:
  - The spool paths are set once in `__init__`; they were rebuilt every hour.
  - `source_file_hour` and `available_at` are formatted once per hour in `begin_hour`; they were formatted per row.
- The G32 rule ("store `payload_raw` as null") moved out of `classify`, which parses, into `CanonStore.add`, which stores.
- `get("public")` is read once instead of twice.

I found nothing else worth removing. Every function is called, every column is in §2, and every file is in §6 or the spec's registry evidence.

## Proof
```
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok \|^note '
27/27 fixtures equal
PASS
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py   → Ran 37 tests, OK
```
