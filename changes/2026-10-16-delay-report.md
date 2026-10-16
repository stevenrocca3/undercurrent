# Delay report tool (`tools/delay_report.py`, 02 §7)

**Why:** Gate 2 criterion 5 needs `evidence/delay-report.json`, and the brief puts that tool in `tools/`. It also answers, as the window runs, what `L` the data proposes.

**What:** `python tools/delay_report.py ROOT OUT_FILE` reads `fetch_log.csv` and `clock.csv` (02 §5.2, §5.4). It uses the standard library only and imports neither implementation.
- **Fields:** the §7 fields: window start and end; hours tracked, succeeded, missing, ingested truncated, republished; delay min, p50, p90, p99, max in seconds; `P`; the clock offsets.
- **Added fields:**
  - `no_final_outcome_yet`, so a mid-window report doesn't look complete.
  - `proposed_L_hours`, the p99 rounded up to a whole hour.
- **Delay:** only `success` final outcomes count, as `available_at - (hour + 1 h)`. Missing and truncated hours are counted, never put in the distribution.
- **Percentiles:** nearest-rank, provisional. Opened as **G35** in `fixtures/SPEC-GAPS.md` (OPEN), together with what "round up" does to an exact hour.

**First numbers:** 9 live hours from the VM give delays of 305–603 s and propose `L` = 1 h (`BENCHMARKS.md`). This is not evidence: it's 9 hours, not 14 days.

**Also:**
- Carries `df2f7b5` (the `archive_input` live-run row and note), which missed the #36 merge.
- `./check.sh` runs `tools/test_delay_report.py`; it passes.
- AGENTS.md lists the tool, and stops naming a session ID for the scrum master: session names change per session (this one is `undercurrent-c1`).
- **Step-4 status:** the fetcher runs under systemd on the VM (`undercurrent-fetcher.service`, active since 2026-10-16 06:01 GMT, start hour 06:00Z). The pipeline agent has no record of the install. Whether this is the start of the 14-day window is Steven's call.
