# Change note: live fetcher (brief `pipeline-live-ingestion.md` step 2)

**Date:** 2026-10-16 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/fetcher.py`, `pipeline/test_fetcher.py`, `check.sh`, `fixtures/SPEC-GAPS.md` (G34), `BENCHMARKS.md`

## Why
Step 2: the fetcher of 02 §3–§5, local only, no VM yet.

## What changed
- `python -m pipeline.fetcher run ROOT START_HOUR [--base-url] [--end-hour]` and `manifest ROOT OUT_CSV`. Stdlib only, runs on Python 3.9 (the VM's version); no DuckDB needed on the VM.
- Schedule (02 §3): first attempt at `h+1h`, `P = 5 min` on 404, backoff 1, 2, 4, 5, 5 … min on 429/5xx/network errors, `D = 24 h`, then hourly for 7 days. One request at a time (a single loop). User-Agent with `srocca2000@outlook.com`.
- Success (02 §4): 200, `Content-Length` matched, temp file in `archive/` then `os.replace`, full decode with the existing `HourRead` = `present`; `available_at` is stamped after that. Truncated/unreadable bodies are archived and logged `incomplete`.
- Records (02 §5): `archive/YYYY-MM-DD-H/<sha256>.json.gz` (an identical version is not rewritten); `fetch_log.csv`, fsynced per row. State is rebuilt from the log on start; a half-written last row (crash) is cut off.
- Recheck at `available_at + 24h` with `If-None-Match`: `republished` (new SHA) or `unchanged`. The manifest keeps the first version's `available_at`.
- Clock: a `clock` row from `chronyc tracking` at start and every 24 h.
- `check.sh`: runs `pipeline/test_fetcher.py` after the existing steps.

## Proof
```
.venv/bin/python -m unittest -q pipeline/test_fetcher.py   -> Ran 11 tests in 6.533s, OK
/usr/bin/python3 -m unittest -q pipeline/test_fetcher.py    -> Python 3.9.6: Ran 11 tests, OK
pipeline tests (6 files)                                    -> Ran 38 tests, OK
.venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out -> 32/32 fixtures equal, PASS
```
Tests cover: 404 then 200; truncated then complete; dropped mid-body (no archived or temp file left); 429/500 backoff timing; deadline with only truncated versions; downtime past `D` then a late file; 7 late days then stop; restart mid-hour with a torn row; republished and unchanged at +24 h; clock rows.
`./check.sh` itself can't run here (no `reference/`); `tools/test_manifest_errors.py` fails only on its reference side for the same reason.

## Open
- **G34 (OPEN):** fetch-log columns/outcomes the spec doesn't define; provisional choices in `SPEC-GAPS.md`.
- A late file sits in the archive but the hour stays missing; step 3's replay must take hours from the manifest/log, not from every archived file.
- Not yet measured against real `data.gharchive.org` (step 4, VM).
