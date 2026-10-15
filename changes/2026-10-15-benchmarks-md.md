# Change note: BENCHMARKS.md

**Date:** 2026-10-15
**Files:** new `BENCHMARKS.md`; `GEMINI.md`, `briefs/pipeline-author.md` and `README.md` point to it. The clone's untracked `CLAUDE.md` has the same rule.
**Spec:** no change
**Status:** committed on `benchmarks`, not pushed

## Why

Steven wants every benchmark tracked as it comes in, especially results for a resume. Until now the numbers were spread across change notes and pasted agent reports.

## What's in it

- **Rules for every agent:**
  - one row per measured result, never editing old rows
  - measured and estimated numbers kept apart
  - each row has how it was measured and where the evidence is (note or commit), plus the machine if it's not the default
- **Default machine:** Apple M2, 8 GB, macOS 14.6.1, Python 3.13.7, DuckDB 1.5.6.
- **Back-filled tables:**
  - **correctness**: 9 rows, e.g. the reference matches 27/27 fixtures, the pipeline matches 27/27, the time zone check, the same 6 `repo: {}` lines found independently
  - **spec rigour**: 32 gaps found; the reference crash caught by the pipeline author (G28); the r2 disagreement caught before Gate 1 (G30)
  - **measured performance**: 4 rows
  - **estimates**: 4 rows
- Every back-filled number comes from an existing change note or a pipeline report, word for word. One reference memory figure was recorded as "~1 GB", and the row says so.

## Agent instructions

The same rule ("record every measurement in `BENCHMARKS.md`…") is now in `GEMINI.md` (verifier, Gemini), `briefs/pipeline-author.md`, and the clone's `CLAUDE.md`. The pipeline agent gets the file with its next `git merge origin/main`.
