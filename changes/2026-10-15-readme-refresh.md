# README refresh after Gate 1

**File:** `README.md`

**Before.** The README described only the reference and `check.sh` as they stood on 2026-10-14.

**After.** It now covers:
- what the project is
- Gate 1 status, with links to the evidence and the CI run
- how the verification works: spec, fixtures, two independent implementations, exact comparison, BigQuery reconciliation, CI evidence
- the Gate 1 result table and idle timings
- how to run the checks, both implementations and the Gate 1 workflow
- a repo map

**Sources.** Every number is copied from `BENCHMARKS.md` or `evidence/gate1.json`. The commands are copied from the change notes and `tools/gate1.sh`, not from pipeline code, which the reference author doesn't read.

**Also.** Moved 11 more iCloud " 2" copies to the Trash. They were already untracked through `.gitignore`. 10 were identical to their originals. The 11th, `.github/workflows/gate1 2.yml`, was the workflow before the `caffeinate` fix.
