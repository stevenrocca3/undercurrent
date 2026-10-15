# Change note: replay vs batch on the real week (measurement only)

**Date:** 2026-10-16 · **Spec:** §4 Replay, §8 criterion 3 · **Status:** committed locally on `pipeline`, not pushed · **Files:** `BENCHMARKS.md`

## Why
The week 2026-09-15 → 09-21 has real duplicates, which the day didn't. Steven asked for replay vs batch on it.

## Proof (code `40ec71e`, input `~/undercurrent-data/gharchive/`, 168 hours, cutoffs daily 2026-09-16 → 09-22 00:00Z)
```
python -m pipeline run IN 2026-09-15T00:00:00Z 2026-09-21T23:00:00Z OUT_b --cutoff … (×7)            batch:  439.43 s, 2,289 MB max RSS
python -m pipeline run IN 2026-09-15T00:00:00Z 2026-09-21T23:00:00Z OUT_r --cutoff … (×7) --replay   replay: 793.52 s, 2,647 MB max RSS
cmp OUT_b/canon_digest.csv OUT_r/canon_digest.csv        → identical
  canon,14964610,f45a96b7…  quarantine,146,4b321a19…  duplicates,9,fb1434b4…
compare_outputs.py dirs OUT_b OUT_r                      → PASS (all 7 files); r3 = 14964601,9,0
duplicates tables, row for row                          → equal (9 rows)
```

## Findings
- **Replay and batch are byte-identical on 15M real events.**
- **All 9 duplicates are within a single hour file**, not across hours. In each case the kept occurrence is the earlier line in the same file, the record hashes are equal, and there are no conflicts. So this run tests replay's dedup *within* an hour on real data. Dedup *across* hours is still covered only by fixtures F03, F26 and `test_dedup.py`. (The week comparison note says the duplicates "appeared twice across hour files"; the `duplicates` table shows otherwise.)
- **The batch digest is expensive at this scale.** The same week took 223.93 s at `56878e6`, before the digest existed, and 439.43 s now. That's most likely the sort plus the Python-side hashing of 15M rows in `table_digests`; it hasn't been profiled. Max RSS rose to 2.3 GB. Projected linearly to the month, it adds about 26 min. A cheaper digest (for example, hashing per hour in DuckDB) is worth a follow-up, but nothing was changed here.
