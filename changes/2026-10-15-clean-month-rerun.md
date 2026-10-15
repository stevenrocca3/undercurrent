# Clean month rerun: pipeline = reference on complete September

**Result: PASS.** This reruns `2026-10-15-real-month-comparison.md` with hour `2026-09-06-20` fully downloaded. Before the run, all 720 hour files passed `gzip -t`. Both implementations ran at `7017a34` with all 24 §8 cutoffs. `compare_outputs.py dirs` found all 7 files (R1–R7) equal. `canon_digest.csv` and `registry_evidence.csv` are not compared.

This run supersedes the first one as Gate 1 evidence.

| | first run (1 partial hour) | clean run |
|---|---|---|
| input sha256 | `300794da9561e350` | `d60fc65a531d7c8c` |
| lines | 54,580,428 | 54,662,224 |
| canonical / Q2 / Q1 | 54,579,647 / 780 / 1 | 54,661,441 / 783 / 0 |
| duplicates, conflicts | 40, 0 | 40, 0 |
| registry | 719 present, 1 truncated | 720 present |
| r2 / r4 / r5 rows | 11,009 / 468,309 / 2,082,422 | 11,009 / 469,422 / 2,087,742 |
| reference | 3,074.63 s, 1,575 MB | 2,847.60 s, 1,440 MB |
| pipeline | 771.84 s, 2,259 MB (`df52f20`) | 1,268.52 s, 2,374 MB (`7017a34`) |
| `canon.duckdb` | 4,307,038,208 B | 4,310,446,080 B (78.9 B/row) |

## Pipeline slower than in the first run

The pipeline took 64% longer: 1,268.52 s against 771.84 s. The pipeline code differs between the two runs. `7017a34` adds step 6, which includes writing `canon_digest.csv` (a SHA-256 per table after a fixed sort). That is a likely cause, but I can't check it, because the reference agent does not read pipeline code (§6). Machine load is another possible cause: neither run was confirmed idle. **Action for the pipeline agent:** profile the month (or the week) at `7017a34`, and say whether the digest step accounts for the difference.

Run commands: the same as the first run, with output in `~/undercurrent-data/runs/2026-09-month-clean/` and a `gzip -t` pass first.
