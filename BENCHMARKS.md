# Benchmarks

Every measured number goes here as it comes in: timings, sizes, counts, correctness results. This is the source for any resume or write-up claim, so each row says **how it was measured** and **where the evidence is**.

**Rules (for every agent):**
- **Add a row when you measure something.** Use one row per result, in the right table. Don't edit old rows: if a number changes, add a new row with the new date.
- **Measured or estimated: say which.** Estimates go in their own table, with the arithmetic.
- **Give a way to reproduce it:** the command, or the change note it's described in, plus the commit.
- **Note the machine** if it's not the default below.
- **Only numbers you actually observed.** No rounding up, and no "about" in a measured row.

Default machine: Apple M2, 8 cores, 8 GB RAM, macOS 14.6.1, Python 3.13.7, DuckDB 1.5.6, 228 GB disk (29 GB free on 2026-10-15).

## Correctness

| Date | Result | How measured | Evidence | By |
|---|---|---|---|---|
| 2026-10-14 | Reference matches hand-derived expected outputs on **17/17** fixtures (R1–R7) | `./check.sh` | `changes/2026-10-14-reference-calculation.md`, `27db891` | reference |
| 2026-10-14 | Reference gives byte-identical output on two runs of 109 real hours | `compare_outputs.py dirs` on run 1 vs run 2 | `changes/2026-10-14-reference-calculation.md` | reference |
| 2026-10-14 | Reference gives `truncated`, 200,000 lines on a CRC-damaged file, identical at read-chunk sizes 1 KB, 64 KB, 1 MB, 16 MB | direct probe | `changes/2026-10-14-reference-calculation.md` | reference |
| 2026-10-14 | Fixture inputs regenerate byte-identically after a generator refactor (39 files) | `generate_inputs.py`, then `git status` | `changes/2026-10-14-review-and-tidy-F18-plus.md`, `d971a92` | reference |
| 2026-10-14 | Reference matches verifier's hand-derived outputs on **27/27** fixtures (two independent authors, no disagreements) | `./check.sh` | `changes/2026-10-14-review-and-tidy-F18-plus.md` | reference |
| 2026-10-15 | CI passes on first run (GitHub Actions, ubuntu-latest) | workflow `check` | run 38681981532 | reference |
| 2026-10-15 | Pipeline matches **27/27** fixtures, all R1–R7 files; 37 tests pass | comparator in the pipeline clone | `pipeline` branch `4a18564` | pipeline |
| 2026-10-15 | Pipeline output unchanged when run with the machine set to the Asia/Kolkata time zone | step 4 run | `pipeline` branch `d4bc998` | pipeline |
| 2026-10-15 | Pipeline and reference each found the same 6 `repo: {}` lines (Q2) in hour `2026-09-15-15`, independently | pipeline r1 vs reference change note | `changes/2026-10-14-reference-calculation.md`; `pipeline` `4a18564` | both |
| 2026-10-15 | Pipeline matches **27/27** fixtures with `payload_raw` stored as null (G32); 37 tests pass | `python -m pipeline fixtures` + `compare_outputs.py fixtures` | `changes/2026-10-15-pipeline-payload-raw-null.md`, `pipeline` branch | pipeline |
| 2026-10-16 | **Pipeline and reference agree exactly on a full real day** (2026-09-15, 24 hours, 1,789,869 lines): all 7 files R1–R7 equal, no differences. 1,789,839 canonical, 30 Q2, 0 duplicates, 0 flags; r2 384 rows, r4 28,862 rows, r5 28,528 rows (2 cutoffs) | `compare_outputs.py dirs` (commands in note) | `changes/2026-10-16-first-real-day-comparison.md`; reference `main` `8f60d65`, pipeline `2bea3ea` | reference |

## Spec rigour

| Date | Result | Evidence |
|---|---|---|
| 2026-10-15 | **32 spec gaps** (G1–G32) found while implementing; 31 decided and written into the spec (v0.2 → v0.11) | `fixtures/SPEC-GAPS.md`, `01-event-semantics.md` §9 |
| 2026-10-15 | The pipeline author's G28 report exposed a **crash in the reference** (lone surrogate escape). The reference was fixed, so the two-author design caught a real bug | `changes/2026-10-15-spec-v0.9-g27-g29.md` |
| 2026-10-15 | The reference author's review exposed a pipeline/reference **disagreement on r2** for non-string `type` (G30), which no fixture covered. It was resolved in the spec before Gate 1 | `changes/2026-10-15-spec-v0.10-g30.md` |

## Performance (measured)

| Date | Implementation | Input | Wall time | Peak memory | Storage | Evidence | By |
|---|---|---|---|---|---|---|---|
| 2026-10-14 | reference | real hour `2026-09-15-15`, 81,142 lines | 5.3 s | 870 MB | — | `changes/2026-10-14-reference-calculation.md` | reference |
| 2026-10-14 | reference | 109 hours `2026-09-15T15` → `2026-09-20T03` (2 present, 107 missing), 190,273 lines | 8.5 s | 1 GB (recorded as "~1 GB") | — | same | reference |
| 2026-10-15 | pipeline | synthetic hour, 100,000 lines | 7 s | 466 MB | — | `pipeline` `5c91de9` | pipeline |
| 2026-10-15 | pipeline | real hour `2026-09-15-15`, 81,136 canonical rows | 8.7 s | — | `canon.duckdb` 286 MB = **3,528 B/row** (`payload_raw` 256 MB) | `pipeline` `4a18564` | pipeline |
| 2026-10-15 | pipeline, `payload_raw` null (G32) | real hour `2026-09-15-15` (SHA-256 `6c5def0c63c6574d…`), 81,142 lines, 81,136 canonical rows | 6.39 s | 124 MB (max RSS, `/usr/bin/time -l`) | `canon.duckdb` 7,614,464 B (7.2 MiB, all tables) = **93.8 B per canonical row** | `changes/2026-10-15-pipeline-payload-raw-null.md`, `pipeline` branch | pipeline |
| 2026-10-16 | reference | real day 2026-09-15, 24 hours, 1,789,869 lines, 1.0 GB gzip | 92.24 s | 1,331 MB | — | `changes/2026-10-16-first-real-day-comparison.md` | reference |
| 2026-10-16 | pipeline | same day | 508.94 s | 322 MB | `canon.duckdb` 175,648,768 B = 98.1 B/row | same | reference (ran it) |

## Estimates (not measurements)

| Date | Estimate | Arithmetic | By |
|---|---|---|---|
| 2026-10-14 | Reference, full month: ~1 h | ~5 s per busy hour × 720 | reference |
| 2026-10-15 | Pipeline, full month: ~1.7 h | 8.7 s × 720 | pipeline |
| 2026-10-15 | Pipeline `canon.duckdb`, full month: 200–250 GB | 3,528 B/row × ~70M rows | pipeline |
| 2026-10-15 | Month of source `.json.gz`: ~44 GB | from sampled hour sizes | pipeline |
| 2026-10-15 | Pipeline `canon.duckdb`, full month, `payload_raw` null: 5.5–6.6 GB | 7,614,464 B × 720 hours = 5.48 GB (every hour like `2026-09-15-15`); 93.8 B/row × 70M rows = 6.57 GB | pipeline |
| 2026-10-16 | Month (30 days) run time: reference ~46 min, pipeline ~4.2 h | real-day times × 30 | reference |
| 2026-10-16 | Pipeline `canon.duckdb`, month: ~6.9 GB | 98.1 B/row × ~70M rows | reference |
