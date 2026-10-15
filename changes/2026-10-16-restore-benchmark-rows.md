# Change note: restore 4 benchmark rows lost in a merge

**Date:** 2026-10-16
**Files:** `BENCHMARKS.md`
**Status:** committed on `restore-benchmark-rows`, not pushed

## What happened

Merging `main` into `real-data-week` (`426d5bc`) rewrote `BENCHMARKS.md` and dropped 4 rows that the pipeline agent had added on `pipeline`. The pipeline agent noticed and reported it.

## Fix

The 4 rows were recovered **verbatim from git history** (`git log -p -- BENCHMARKS.md`, rows present in history but missing now) and appended to the end of their tables:
- Correctness: the speed-up changes no output (R1–R7 and `canon`/`quarantine` identical before and after, on 2026-09-15)
- Performance:
  - pipeline `f639320`, same day, idle machine: 124.36 s
  - the per-phase profile
  - after the speed-up: 34.10 s

No existing row was changed. The change notes these rows cite already existed.

## Note on the two "same day" pipeline times

`f639320` is the same code as `2bea3ea`, yet it measured 124.36 s on an idle machine, while the reference agent's run of `2bea3ea` measured 508.94 s. Both rows stand as measured. The 508.94 s run likely overlapped with other work on the machine, so the idle-machine figure is the fair comparison. Future benchmark runs should note whether the machine was otherwise idle.
