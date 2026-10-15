# Change note: pipeline step 1, ingest and missing-hour registry

**Date:** 2026-10-15
**Files:** `pipeline/__init__.py`, `pipeline/ingest.py`, `pipeline/__main__.py`, `pipeline/test_ingest.py` (all new); `check.sh` (one step and a comment line added); `fixtures/SPEC-GAPS.md` (G26 added, OPEN)
**Spec:** v0.7, §1. No spec change.
**Status:** committed locally on `pipeline`, not pushed

## Why

Brief `briefs/pipeline-author.md`, item 1: read GH Archive hour files and produce the missing-hour registry (R6) with all four statuses, including recovery of a truncated stream's last partial line. Built from the spec and fixtures only.

## What changed

- **`pipeline/ingest.py`**
  - `inflate(f)` streams a gzip file through `zlib.decompressobj(wbits=31)` in 64 KiB chunks. It handles multiple members (after `eof`, `unused_data` starts a new member) and raises `StreamError` once it has yielded everything it could recover. That happens when the file is empty or not gzip, a member is corrupt or has a bad CRC, the stream stops before the end-of-stream marker, or non-gzip bytes follow a complete member. zlib throws away the output of a chunk that raises an error, so `inflate` saves the decompressor state (`copy()`) before each chunk. On an error it replays that chunk one byte at a time from the saved state, which recovers every byte before the bad one. F23 hour 6 depends on this: the CRC error and the line's data arrive in the same chunk.
  - `HourRead(input_dir, hour).lines()` yields `(source_line, raw_bytes, partial)`. A line is the bytes between `\n`s, without the `\n`; any `\r` stays in the bytes, because only `record_hash` strips it. The status is set once the generator is exhausted:
    - `missing`: no file named `YYYY-MM-DD-H.json.gz`.
    - `unreadable`: a `StreamError` before any complete line. Nothing is yielded, and partial bytes are discarded.
    - `truncated`: a `StreamError` after ≥ 1 complete line. The complete lines are yielded, then the bytes after the last `\n`, if there are any, as a line with `partial=True` (step 2 will make it `Q1` without parsing it).
    - `present`: decoded fully. A final line with no `\n` is an ordinary line (F24).
  - Memory holds at most one line plus one chunk.
- **`pipeline/__main__.py`**: the brief's two modes, `run INPUT_DIR FIRST LAST OUT [--cutoff T ...]` and `fixtures FIXTURES_DIR OUT_ROOT`. Only requested hours are looked up, so files outside the range are never opened (F25). For now it writes `registry.csv` and `registry_evidence.csv` (see G26). `--cutoff` is parsed but not used yet. `csv_cell` does the §6 RFC 4180 quoting.
- **`pipeline/test_ingest.py`** (6 tests):
  - For every fixture, recovered line count = the sum of expected `r1.csv`.
  - Results are identical at chunk sizes 1, 7, 100 and 65536, which exercises the replay path.
  - F16: partial line 5 is exactly 55 bytes.
  - F23: statuses and line counts per hour.
  - F24: the last line has no LF, and the CR is kept in the raw bytes.
  - F09: missing hour.
- **`check.sh`**: runs `pipeline/test_ingest.py` after the existing steps, which are unchanged. The fixture-run-and-compare step for the pipeline comes later: until r1–r5 and flags exist it would fail by design.

## Proof

```
$ .venv/bin/python -m unittest tools/test_compare_outputs.py pipeline/test_ingest.py
Ran 27 tests in 0.300s
OK

$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out
...
0/27 fixtures equal
FAIL
```

That overall FAIL is expected at step 1. Every FAIL line says `missing in actual`, for one of `r1..r5` or `flags` (162 = 27 × 6). `registry.csv` is `ok` in **27/27** fixtures, with no registry mismatch. Counted from the comparator output:

```
registry.csv ok: 27/27
registry.csv FAIL: 0
```

`registry_evidence.csv` for F23 shows the evidence each status rests on:

```
source_file_hour,status,file_bytes,lines,error
2026-09-01T00:00:00Z,present,283,6,
2026-09-01T01:00:00Z,unreadable,25,0,stream ended before the end-of-stream marker
2026-09-01T02:00:00Z,truncated,174,1,decompression error: Error -3 while decompressing data: incorrect header check
2026-09-01T03:00:00Z,unreadable,0,0,empty file: not a gzip stream
2026-09-01T04:00:00Z,present,20,0,
2026-09-01T05:00:00Z,present,311,2,
2026-09-01T06:00:00Z,truncated,155,1,decompression error: Error -3 while decompressing data: incorrect data check
```

## Left open

- **G26 (OPEN, new):** §1 asks for evidence that includes an HTTP status, but the pipeline reads local files and `registry.csv` has no evidence columns. Provisional behaviour: a separate, uncompared `registry_evidence.csv` with no HTTP column. Steven to decide.
- Not run on real September hours yet. That's for after steps 2–5, when there are outputs to compare against the reference.
- `run` reads every requested hour but doesn't parse lines yet (step 2).
