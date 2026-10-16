# Change notes

One note per change, named `YYYY-MM-DD-<topic>.md`. Add a line here with each new note.

A note's own **Status** line records the moment it was written (often "not pushed"). This table records where it actually landed.

| Note | Change | Merged |
|---|---|---|
| 2026-10-14-resolve-open-decisions | resolve OPEN-1, OPEN-2, OPEN-3 | #1 |
| 2026-10-14-fixtures-and-spec-v0.3 | fixtures F01–F17 and spec v0.3 | #1 |
| 2026-10-14-comparison-script | output comparison script | #1 |
| 2026-10-14-comparison-script-review-fixes | comparison script, review follow-up | #1 |
| 2026-10-14-reference-adds-r6-r7 | reference adds R6 (registry) and R7 (flags) | #1 |
| 2026-10-14-comparator-counter-multiset | comparator uses Counter for row differences | #2 |
| 2026-10-14-reference-calculation | reference calculation R1–R7 | #2 |
| 2026-10-14-spec-v0.6-g19-g22-cutoffs | spec v0.6: G19–G22, Gate 1 R5 cutoffs | #2 |
| 2026-10-14-tidy-reference-and-tests | tidy reference.py and comparator tests | #2 |
| 2026-10-14-refactor-proposal-shared-contract | **proposal**: cross-file duplication and tooling | #2 |
| 2026-10-14-check-script | one check command (`check.sh`) | #2 |
| 2026-10-14-agent-briefs | briefs for the verifier and pipeline agents | #2 |
| 2026-10-14-fixtures-F18-plus | fixtures F18–F27 (verifier) | #2 |
| 2026-10-14-review-and-tidy-F18-plus | review of F18–F27; tidy generator and test | #2 |
| 2026-10-14-spec-v0.7-g23-g25-and-fixtures | spec v0.7: G23–G25, §7 lists F18–F27 | #2 |
| 2026-10-14-gemini-config | `GEMINI.md` and `.geminiignore` | #3 |
| 2026-10-15-spec-v0.8-g26-registry-evidence | spec v0.8: G26 registry evidence | #4 |
| 2026-10-15-remove-icloud-duplicates | remove iCloud duplicate files | #5 |
| 2026-10-15-spec-v0.9-g27-g29 | spec v0.9: G27–G29; reference fix for G28 | #6 |
| 2026-10-15-ci-check-workflow | CI runs `check.sh` | #7 |
| 2026-10-15-spec-v0.10-g30 | spec v0.10: G30; G31 raised | #8 |
| 2026-10-15-refactor-and-cleanup | reference tidy, this index, cleanups | #8 |
| 2026-10-15-spec-v0.11-g31-and-line-limit | spec v0.11: G31 repeated keys; §6 limit 350 | #9 |
| 2026-10-15-benchmarks-md | `BENCHMARKS.md` and the rule for all agents | #10 |
| 2026-10-15-spec-v0.12-g32 | spec v0.12: G32, no `payload_raw` in Gate 1 | #11 |
| 2026-10-16-first-real-day-comparison | first real-day comparison: pipeline = reference on 2026-09-15 | #12 |
| 2026-10-16-real-week-comparison | real week: pipeline = reference on 2026-09-15 → 21 (15M events) | #14 |
| 2026-10-16-restore-benchmark-rows | restore 4 benchmark rows dropped by a merge | #15 |
| 2026-10-15-real-month-comparison | real month: pipeline = reference on all of September (54.6M events, 24 cutoffs) | #17 |
| 2026-10-15-clean-month-rerun | clean month rerun: pipeline = reference on complete September, all 720 hours | #19 |
| 2026-10-15-gate1-evidence-and-reconciliation | Gate 1 tooling: CI evidence run, BigQuery reconciliation; pipeline digest fix verified on the month | #20 |
| 2026-10-15-gate1-caffeinate | Gate 1 workflow: no idle sleep during the run (first run lost the runner) | #21 |
| 2026-10-15-gate1-pass | **Gate 1 passes**: CI evidence run 38821187454, all 6 criteria | #22 |
| 2026-10-15-readme-refresh | README: what the project is, how it is verified, Gate 1 result, how to run | #23 |
| 2026-10-15-spec-02-live-ingestion-draft | spec 02 draft: live ingestion, delay measurement, Gate 2 | #24 |
| 2026-10-15-spec-02-approved-v0.13 | spec 02 approved (14-day window, 24 h deadline); spec 01 v0.13 | #24 |
| 2026-10-15-reference-available-at | reference: `--available-at` manifest | #25 |
| 2026-10-15-live-ingestion-briefs | briefs for live ingestion (pipeline, verifier); 02 v0.3 manifest format | #25 |
| 2026-10-15-copilot-instructions | Copilot instructions and quota-saving settings | #26 |
| 2026-10-15-live-step1-cross-check | live step 1 cross-check (PASS on a real week), G33 findings, VM setup guide | #27 |
| 2026-10-15-g33-manifest-validation | G33 decided (02 v0.4): strict manifest validation; reference tightened; black-box test of both | — |
| 2026-10-15-verifier-live-fixtures | fixtures F28-F32 for 02 §8.3; requested_hours fix | — |

Pipeline notes (`2026-10-15-pipeline-*`) live on the `pipeline` branch until it merges.
