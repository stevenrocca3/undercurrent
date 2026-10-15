# Change note: real-week comparison, pipeline vs reference

**Date:** 2026-10-16
**Files:** `BENCHMARKS.md` (new rows), `changes/README.md`. No code changed.
**Spec:** v0.12
**Status:** committed on `real-data-week`, not pushed

## Result

**PASS.** On a full real week, the pipeline and the reference produce exactly equal R1–R7 output (7/7 files).

| | |
|---|---|
| Input | GH Archive 2026-09-15 → 2026-09-21, 168 hours, 4.0 GB gzip; SHA-256 of the files concatenated in hour order begins `70ff9b4598ab2ac4` |
| Lines | 14,964,756: 14,964,610 canonical, 146 Q2 |
| r3 | 14,964,601 distinct, **9 duplicates**, 0 conflicts |
| Flags | 0 late, 0 future-skewed, 0 unrecognized |
| Registry | 168 present |
| Rows compared | r2 2,638, r4 92,098, r5 383,396 (cutoffs daily 2026-09-16 → 09-22, 00:00Z) |

| | Commit | Wall time | Peak memory |
|---|---|---|---|
| reference | `04fd948` | 576.22 s | 2,387 MB |
| pipeline | `56878e6` | 223.93 s | 1,124 MB (`canon.duckdb` 88.7 B/row) |

**New compared to the day run:** real duplicates. The 9 events that appeared twice across hour files were deduplicated identically by both implementations. Until now, deduplication had only been tested by fixtures.

## The pipeline changed during this run

The pipeline agent committed a speed-up at 02:40, before the pipeline's week run started at 02:42. The commits:
- `76050d2` profile
- `bfcb830` tidy
- `56878e6` "Speed up pipeline 3.6x: C JSON decoder, slimmer spool rows, parallel hours"

So this result is for `56878e6`, not `2bea3ea` (the day run). Because the JSON decoder changed, I re-checked:
- `56878e6` on all fixtures: **27/27 equal, PASS**
- my hand-made probes for G28 (lone surrogates), G30 (raw `type` text) and G31 (repeated keys), both implementations: **PASS** each. No fixture covers these yet, so this is the only check they've had on the new decoder.

The pipeline is now **2.6× faster than the reference** on the week (224 s vs 576 s). On the day run, before the speed-up, it was 5.5× slower.

## What it does and doesn't prove

- **Proves:** exact agreement on 15M real events, including real deduplication, R5 at 7 cutoffs and 7 days of R4 dates.
- **Doesn't prove:**
  - **Agreement with the source** (§5.2 BigQuery is still to come).
  - **Rare cases** that didn't occur this week: conflicts, late or future events, unrecognized types, truncated or missing hours. These still rest on fixtures.

## Reproduce

```
curl -O https://data.gharchive.org/2026-09-{15..21}-{0..23}.json.gz   # into IN
reference/reference.py run IN 2026-09-15T00:00:00Z 2026-09-21T23:00:00Z OUT/reference --cutoff 2026-09-16T00:00:00Z … --cutoff 2026-09-22T00:00:00Z
python -m pipeline run    IN 2026-09-15T00:00:00Z 2026-09-21T23:00:00Z OUT/pipeline  (same cutoffs; from the pipeline checkout)
tools/compare_outputs.py dirs OUT/reference OUT/pipeline
```

The reference agent **ran** the pipeline and did not read its code (§6).
