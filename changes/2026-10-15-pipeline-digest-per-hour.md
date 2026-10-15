# Change note: digest one hour at a time (month regression)

**Date:** 2026-10-15 · **Spec:** §4 Replay, §8 criterion 3 · **Status:** committed locally on `pipeline` (`4dac241`), not pushed
**Files:** `pipeline/canon.py`, `pipeline/test_replay.py`, `BENCHMARKS.md`

## Why
The clean month run took 1,268.52 s at `7017a34`, against 771.84 s at `df52f20` (`2026-10-15-clean-month-rerun.md`, branch `month-clean-rerun`). Pipeline code is unchanged from `56878e6` to `df52f20`, and from `7017a34` to `0cab6d9`.

- **Cause:** `table_digests` (step 6, `ef6a5e0`) sorted all of `canon` at once with the `to_json` text as payload. Above `memory_limit = 3GB` the sort spills, so its cost grows faster than the data: 3.54 s on a day, 83.21 s on the week, **442.81 s on the month**.
- **How measured:** `table_digests` alone on the clean run's `canon.duckdb`, opened read-only with the same memory limit. It reproduced that run's `canon_digest.csv` exactly.
- **Where the time goes (week):** fetching the sorted rows without hashing took 79.83 s, and fetching unsorted rows 24.32 s. So the cost is the whole-table sort, not the hashing.

## What changed
- **`table_digests` sorts one `source_file_hour` at a time.** That column is `NOT NULL` in `canon` and `quarantine`, and `duplicates` copies it from `canon`. Each batch is hashed with a single `update`. The bytes hashed are unchanged, so every earlier `canon_digest.csv` stays valid.
- **New test:** `test_digest_is_whole_table_sort_across_hours` checks that the digest equals one whole-table sort when rows are inserted out of hour order.

## Proof
```
unittest pipeline/test_*.py tools/test_compare_outputs.py   → Ran 42 tests, OK
compare_outputs.py fixtures fixtures OUT                     → 27/27 fixtures equal, PASS
table_digests on week canon.duckdb: 83.21 s → 39.29 s, SHA-256s identical (canon f45a96b7ff74…)
week, phase timer, old (df52f20) vs this: 213.55 s vs 242.82 s; table_digests 39.82 s, load_hour 194.09 vs 185.55 s
month (run below): 1,096.78 s; canon_digest.csv and r1–r5, registry, flags.csv byte-identical to the clean run
```
Month command: as in the clean rerun, 24 cutoffs 2026-09-08 → 10-01. Output is in `~/undercurrent-data/runs/2026-09-month-digestfix/`.

## Open
- **Not fully restored.** The digest now scales linearly, but still costs about 145 s on the month (39.82 s × 54.66M / 14.96M rows, an estimate). Nothing else in step 6 is slower on the week.
- **Busy machine:** during the month run, load averages reached 12.78 and 17.22. The 1,096.78 s figure includes that noise.
- **Getting back to the old time:** returning to ~772 s would mean writing the digest only when it's asked for (replay-vs-batch checks). That's Steven's decision.
- **No timing test:** there's no unit seam for the time itself, so the week and month benchmarks are the guard.
