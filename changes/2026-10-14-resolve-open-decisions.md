# Change note: resolve OPEN-1, OPEN-2, OPEN-3

**Date:** 2026-10-14
**Document:** `01-event-semantics.md`
**Version:** v0.1 → v0.2
**Decided by:** Steven (owner)
**Status:** proposed, awaiting owner review and merge (§10)

## Why

All three OPEN items blocked Gate 1. Resolving them is the first step that unblocks work on the pipeline and the reference calculation.

## Decisions

| ID | Decision | Resolution |
|---|---|---|
| OPEN-1 | Gate 1 month | **September 2026**, UTC, `[2026-09-01T00:00Z, 2026-10-01T00:00Z)`, 720 hour files |
| OPEN-2 | Historical availability lag `L` | **6h**, later recalibrated to the measured live p99, rounded up to the next hour |
| OPEN-3 | Source-reconciliation tolerance | **≤ 0.1%** relative difference per cell |

## What changed, by section

- **Header:** version bumped to v0.2. The agent note now explains the DECIDED marker.
- **§1 Scope:** OPEN-1 is replaced with the exact month, its half-open UTC range, and the expected number of hour files (720). That count is what the missing-hour registry is checked against.
- **§4 Time semantics:** OPEN-2 is replaced with `L = 6h`. Recalibration now explicitly goes through change control (§10). The existing rule stays: changing `L` invalidates detector runs made under the old value.
- **§5.2 Source reconciliation:** OPEN-3 is replaced with the 0.1% tolerance. Steven should check these two additions, which go beyond the original wording:
  1. **Scope widened.** The draft attached the tolerance to `(hour, event_type)` cells only. v0.2 applies it to every §5.2 metric (distinct IDs per hour, and star events per repo per day). Without this, those two metrics would have no tolerance at all.
  2. **Formula and zero case defined.** Relative difference is `|ours − theirs| / theirs`. A cell where `theirs = 0` but `ours ≠ 0` counts as out of tolerance. The tolerance may not be changed after results are seen.
- **§9:** the "Open decisions" table is now a "Decisions" table recording each resolution and when it was made.

## What did not change

- §2 schema, §3 identity and deduplication, §6 reference outputs, §7 fixtures, §8 Gate 1 criteria. **§3 and §4 rules are unchanged except for setting the value of `L`.** Gate 1 has not run yet, so nothing needs re-running.

## Effects

- **0.1% is effectively exact on small cells.** A cell with fewer than 1,000 events goes out of tolerance after a difference of just one event. Expect many small `(hour, event_type)` and `(repo_id, date)` cells to need categorizing. This is intended, not a bug.
- **Data volume:** September 2026 is 720 hour files, likely tens of GB compressed. The reference script (§6) should stream line by line rather than load whole files.
- **BigQuery:** the comparison runs against the `githubarchive.day` / `githubarchive.month` tables for 2026-09. Querying a full month has a cost, so plan for it.

## Next necessary steps

1. Owner reviews and merges this change.
2. Fixtures F1–F13 with hand-checked expected outputs (§7). They must be committed before any pipeline code they test.
3. Reference calculation R1–R5 (§6), written by Steven.
