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
| 2026-10-16 | **Pipeline and reference agree exactly on a full real week** (2026-09-15 → 09-21, 168 hours, 14,964,756 lines): all 7 files R1–R7 equal. 14,964,610 canonical, 146 Q2; **9 real duplicates** (0 conflicts) deduplicated identically; r2 2,638 rows, r4 92,098 rows, r5 383,396 rows (7 daily cutoffs) | `compare_outputs.py dirs` | `changes/2026-10-16-real-week-comparison.md`; reference `04fd948`, pipeline `56878e6` | reference |
| 2026-10-16 | After the pipeline's 3.6× speed-up (new JSON decoder), pipeline still matches 27/27 fixtures and matches the reference on hand-made G28 (lone surrogates), G30 (raw `type` text) and G31 (repeated keys) probes | comparator, fixtures and dirs mode | same note | reference |
| 2026-10-16 | **Replay and batch byte-identical** (§8 criterion 3) on 27/27 fixtures and the real day 2026-09-15 (24 hours; canon 1,789,839 rows, quarantine 30, duplicates 0): same `canon_digest.csv` (SHA-256 per table after a fixed sort, excluding `ingested_at`, `source_last_modified`) and identical R1–R7; 41 tests pass | `pipeline/test_replay.py`; `run … --replay` vs batch, `cmp` + `compare_outputs.py dirs` | `changes/2026-10-16-pipeline-replay-vs-batch.md`, `pipeline` `ef6a5e0` | pipeline |
| 2026-10-16 | **Replay and batch byte-identical on the real week** 2026-09-15 → 09-21 (168 hours): same `canon_digest.csv` (canon 14,964,610 rows, quarantine 146, duplicates 9) and identical R1–R7 (7 cutoffs). The 9 duplicates (0 conflicts) were discarded identically, row for row; all 9 are **within one hour file** (0 across hours), so replay's cross-hour dedup is still covered only by fixtures | `run … --replay` vs batch; `cmp`, `compare_outputs.py dirs`, DuckDB query on `duplicates` | `changes/2026-10-16-pipeline-replay-vs-batch-week.md`, `pipeline` `40ec71e` | pipeline |
| 2026-10-15 | **Pipeline and reference agree exactly on the full Gate 1 month** (2026-09-01 → 09-30, 720 hours, 54,580,428 lines): all 7 files R1–R7 equal. 54,579,647 canonical, 780 Q2, 1 Q1; **40 real duplicates** (0 conflicts) deduplicated identically; r2 11,009 rows, r4 468,309 rows, r5 2,082,422 rows (**all 24 §8 cutoffs**, 09-08 → 10-01). One hour (`2026-09-06-20`) was only partly downloaded; both marked it `truncated` in the registry and quarantined the cut line as Q1 | `compare_outputs.py dirs` | `changes/2026-10-15-real-month-comparison.md`; reference and pipeline at `df52f20` | reference |
| 2026-10-15 | **Pipeline and reference agree exactly on the complete Gate 1 month** (2026-09-01 → 09-30, all 720 hours verified with `gzip -t`, 54,662,224 lines): all 7 files R1–R7 equal. 54,661,441 canonical, 783 Q2; **40 real duplicates** (0 conflicts); registry 720 present; r2 11,009, r4 469,422, r5 2,087,742 rows (**all 24 §8 cutoffs**). Supersedes the run with one partly downloaded hour | `compare_outputs.py dirs` | `changes/2026-10-15-clean-month-rerun.md`; both at `7017a34`; input sha256 `d60fc65a531d7c8c` | reference |
| 2026-10-15 | After the pipeline's per-hour digest fix, **pipeline still equals the reference on the complete month** (all 7 files R1–R7, 24 cutoffs), and its `canon_digest.csv` is byte-identical to the `7017a34` run | `compare_outputs.py dirs` against the clean run's reference output; `cmp` of digests | `changes/2026-10-15-gate1-evidence-and-reconciliation.md`; pipeline `f5bf11d` | reference |
| 2026-10-15 | **Source reconciliation against BigQuery GH Archive (§5.2): every difference explained exactly.** 30,498 cells (event count by hour × type, distinct ids by hour, stars for the top 1,000 repos by day) for September 2026; 311 outside the 0.1% tolerance, all categorized: 301 `parse_or_schema` (783 ForkEvents with `repo: {}`, quarantined Q2) and 10 `dedup_policy` (40 duplicates). In all 30,498 cells, the gap equals Q2 lines + duplicate copies exactly; 0 time-bucketing differences, 0 unexplained | `tools/reconcile.py` on BigQuery exports (75 GB scanned, sandbox) vs pipeline `f5bf11d` month output; per-cell check against the `quarantine`/`duplicates` output tables | `changes/2026-10-15-gate1-evidence-and-reconciliation.md`; `evidence/reconciliation-categories.csv` | reference |
| 2026-10-15 | **Gate 1 passes, with evidence generated in CI** (§8, all 6 criteria): 27/27 fixtures in both implementations; pipeline = reference on all 7 files R1–R7 for September 2026 (54.66M events, 24 cutoffs); replay = batch byte-identical; BigQuery reconciliation 30,498 cells, 0 unexplained; 720-hour registry; `evidence/gate1.json` with commit, config hash, 720-file SHA-256 manifest and 9 check results | `gate1` workflow on a self-hosted runner, `tools/gate1.sh` → `tools/gate1_evidence.py` | `changes/2026-10-15-gate1-pass.md`; `evidence/gate1.json`; CI run 38821187454; commit `01403c0` | reference |

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
| 2026-10-16 | reference | real week 2026-09-15 → 09-21, 168 hours, 14,964,756 lines, 4.0 GB gzip | 576.22 s | 2,387 MB | — | `changes/2026-10-16-real-week-comparison.md` | reference |
| 2026-10-16 | pipeline (`56878e6`, after speed-up) | same week | 223.93 s | 1,124 MB | `canon.duckdb` 1,327,247,360 B = 88.7 B/row | same | reference (ran it) |
| 2026-10-16 | pipeline `f639320` (same code as `2bea3ea`) | same day, rerun on an otherwise idle machine | **124.36 s** | 328 MB (max RSS) | `canon.duckdb` 169,619,456 B | `changes/2026-10-16-pipeline-profile-real-day.md` | pipeline |
| 2026-10-16 | pipeline `f639320`, by phase (driver script) | same day | 124.6 s total: classify 65.5, add 35.6, load 11.9, read 11.4, dedup 0.1, metrics 0.1 | — | — | `changes/2026-10-16-pipeline-profile-real-day.md` | pipeline |
| 2026-10-16 | pipeline, speed-up (C JSON decoder, slimmer spool rows, 8 worker processes) | same day | **34.10 s** (3.6× faster than 124.36 s; reference 92.24 s) | 324 MB max RSS per process; 724 MB total across processes (`ps` sampled every 0.5 s) | `canon.duckdb` 173,027,328 B | `changes/2026-10-16-pipeline-speedup.md` | pipeline |
| 2026-10-16 | pipeline batch (`ef6a5e0`, now also writes `canon_digest.csv`) | real day 2026-09-15 | 44.99 s | 703 MB (max RSS, one process) | — | `changes/2026-10-16-pipeline-replay-vs-batch.md`, `pipeline` `ef6a5e0` | pipeline |
| 2026-10-16 | pipeline replay (`ef6a5e0`, one hour at a time, serial, per-hour dedup) | same day | 88.17 s | 1,217 MB (max RSS) | — | `changes/2026-10-16-pipeline-replay-vs-batch.md`, `pipeline` `ef6a5e0` | pipeline |
| 2026-10-16 | pipeline batch (`40ec71e`, writes `canon_digest.csv`) | real week 2026-09-15 → 09-21, 168 hours | 439.43 s | 2,289 MB (max RSS, one process) | — | `changes/2026-10-16-pipeline-replay-vs-batch-week.md`, `pipeline` `40ec71e` | pipeline |
| 2026-10-16 | pipeline replay (`40ec71e`, serial, per-hour dedup) | same week | 793.52 s | 2,647 MB (max RSS) | — | `changes/2026-10-16-pipeline-replay-vs-batch-week.md`, `pipeline` `40ec71e` | pipeline |
| 2026-10-15 | pipeline `table_digests` only (`7017a34`), read-only on the clean month run's `canon.duckdb` | month canon 54,661,441 rows | 442.81 s | — | — | `changes/2026-10-15-pipeline-digest-per-hour.md` | pipeline |
| 2026-10-15 | pipeline `table_digests` only, whole-table sort (`7017a34`) vs per hour (`4dac241`), same SHA-256s | week `canon.duckdb` (`56878e6` run), 14,964,610 rows | 83.21 s vs 39.29 s | — | — | same | pipeline |
| 2026-10-15 | pipeline batch, phase timer: `df52f20` vs `4dac241` (`table_digests` 39.82 s of it), run back to back, load avg 12–22 | real week 2026-09-15 → 09-21 | 213.55 s vs 242.82 s | — | — | same | pipeline |
| 2026-10-15 | pipeline batch (`4dac241`), outputs byte-identical to the clean run; load avg up to 17.22 during run | real month 2026-09, 720 hours, 24 cutoffs | 1,096.78 s | 1,363 MB (max RSS), 3,771 MB peak footprint | `canon.duckdb` 4,312,805,376 B | same | pipeline |
| 2026-10-15 | reference | real month 2026-09-01 → 09-30, 720 hours, 54,580,428 lines, 19 GB gzip (machine not confirmed idle) | **3,074.63 s** (51.2 min, 17.8k lines/s) | 1,575 MB | — | `changes/2026-10-15-real-month-comparison.md` | reference |
| 2026-10-15 | pipeline (`df52f20`) | same month | **771.84 s** (12.9 min, 70.7k lines/s; 4.0× the reference) | 2,259 MB (max RSS, largest single process) | `canon.duckdb` 4,307,038,208 B = 78.9 B/row | same | reference (ran it) |
| 2026-10-15 | reference | complete month 2026-09-01 → 09-30, 720 hours, 54,662,224 lines, 19 GB gzip (machine not confirmed idle) | **2,847.60 s** (47.5 min, 19.2k lines/s) | 1,440 MB | — | `changes/2026-10-15-clean-month-rerun.md` | reference |
| 2026-10-15 | pipeline (`7017a34`, with step 6 replay/digest code) | same month | **1,268.52 s** (21.1 min, 43.1k lines/s; 2.2× the reference) | 2,374 MB (max RSS, largest single process) | `canon.duckdb` 4,310,446,080 B = 78.9 B/row | same | reference (ran it) |
| 2026-10-15 | pipeline (`f5bf11d`, digest per hour) | complete month, 720 hours, 54,662,224 lines (**machine busy**: 1-min load median 32.6, max 95.3, sampled every 30 s) | **989.47 s** (16.5 min; 1,268.52 s at `7017a34`, 771.84 s at `df52f20`) | 1,565 MB (max RSS, largest single process) | `canon.duckdb` 4,309,921,792 B | `changes/2026-10-15-gate1-evidence-and-reconciliation.md` | reference (ran it) |
| 2026-10-15 | reference, in CI | complete month, 720 hours, 54,662,224 lines (**idle**: load median 3.07) | **1,405 s** (23.4 min) | — | — | `changes/2026-10-15-gate1-pass.md`; `evidence/gate1.json`; CI run 38821187454 | reference (ran it) |
| 2026-10-15 | pipeline batch (`01403c0`), in CI | same month, idle | **482 s** (8.0 min, 113k lines/s; 2.9× the reference) | — | — | same | reference (ran it) |
| 2026-10-15 | pipeline replay (`01403c0`), in CI | same month, idle | 1,343 s (22.4 min) | — | — | same | reference (ran it) |
| 2026-10-15 | whole Gate 1 run in CI (fixtures, both implementations, replay, BigQuery, reconciliation, evidence) | same month, idle | 3,284 s (54.7 min) | — | — | same | reference (ran it) |

## Fetcher host (measured)

Oracle Cloud Always Free `VM.Standard.E2.1.Micro` (x86_64, 2 vCPUs reported, 498 MiB RAM, 30 GB root), Oracle Linux 9.8, region US East (Ashburn), at `150.136.138.5`. Freshly created; nothing else running.

| Date | Result | How measured | Evidence | By |
|---|---|---|---|---|
| 2026-10-16 05:08 UTC | clock synchronized; offset **0.000000619 s slow** of NTP, RMS offset 0.000397 s, source 169.254.169.254 (Oracle NTP, stratum 3), root dispersion 0.000392 s | `timedatectl`; `chronyc tracking`; `chronyc sources` over SSH | `changes/2026-10-16-oracle-fetcher-vm.md` | reference |
| 2026-10-16 05:08 UTC | `data.gharchive.org` reachable from the VM: `HTTP/2 200`, `content-length: 6461705` for `2026-10-15-0.json.gz` | `curl -sI` | same | reference |

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
| 2026-10-16 | Month (30 days) run time: reference ~41 min, pipeline ~16 min | real-week times × 30/7 | reference |
| 2026-10-16 | Pipeline `canon.duckdb`, month: ~5.7 GB | 1.33 GB × 30/7 | reference |
