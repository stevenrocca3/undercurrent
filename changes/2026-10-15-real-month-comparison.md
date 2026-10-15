# Real month: pipeline = reference on all of September

**Result: PASS.** Both implementations were run on the full Gate 1 window, 2026-09-01 → 09-30 (720 hours), with all 24 §8 R5 cutoffs (daily, 2026-09-08 → 2026-10-01). `compare_outputs.py dirs` found all 7 files (R1–R7) equal. `registry_evidence.csv` is not compared (G26).

## Numbers

| | value |
|---|---|
| input | 720 `.json.gz`, 19 GB; sha256 over files `300794da9561e350…` |
| lines | 54,580,428 = 54,579,647 canonical + 780 Q2 + 1 Q1 |
| duplicates | 40 real duplicates, 0 conflicts (r3: 54,579,607 unique) |
| flags | 0 future_skewed, 0 late, 0 unrecognized_type |
| registry | 719 present, 1 truncated |
| rows | r2 11,009; r4 468,309; r5 2,082,422 |
| reference | 3,074.63 s, 1,575 MB peak |
| pipeline | 771.84 s, 2,259 MB peak (largest single process); `canon.duckdb` 4,307,038,208 B = 78.9 B/row |

Both ran at commit `df52f20` (the pipeline code is unchanged from `5b10891`), one after the other. Other agents may have been active, so the machine is **not confirmed idle**.

## The truncated hour

The download of `2026-09-06-20.json.gz` failed partway: 22.3 MB of 85.6 MB, and curl printed `MISSING`. Both implementations marked the hour `truncated` in the registry and quarantined the cut final line as Q1. So this run is also a real-data check of truncation handling, which both pass identically.

It also means this run is **not quite the true September**. The full file has since been downloaded to `~/undercurrent-data/gharchive/` (it passes `gzip -t`). The partial copy is kept in `~/undercurrent-data/partial/` so this run can be reproduced. For clean Gate 1 evidence, rerun the month (~65 min of machine time, almost no tokens).

## Against the estimates

| | estimate | measured |
|---|---|---|
| reference run time | ~41 min | 51.2 min |
| pipeline run time | ~16 min | 12.9 min |
| `canon.duckdb` | ~5.7 GB | 4.31 GB |
| source gzip | ~44 GB | 19 GB |

## Also in this change

- `.DS_Store` and `tools/.DS_Store` (macOS Finder metadata, committed by mistake in PR #16) are no longer tracked; `.DS_Store` is added to `.gitignore`.
- The `changes/README.md` index now gives the restore note's PR (#15).
