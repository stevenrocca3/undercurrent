# Change note: briefs for the verifier and pipeline agents

**Date:** 2026-10-14
**Files:** new `briefs/verifier-F18-plus.md` and `briefs/pipeline-author.md`; `changes/2026-10-14-refactor-proposal-shared-contract.md` (item 4 status)
**Spec:** no change
**Status:** committed locally, not pushed. Steven reviews before sending either brief.

## Why

Steven asked for the handoff material for the other agents. None existed: the spec v0.6 note and the refactor proposal (item 4a) pointed at the work, but were written from the reference side. Several of those notes describe the reference's behaviour on edge cases, so passing them on would break the §6 independence rule.

## What's in them

**`briefs/verifier-F18-plus.md`**: fixtures for the rules that only throwaway probes have checked so far (G9, G11, G13, G14, G16, G18, G19–G22). It's a table of **cases plus the spec section** each one is derived from, **with no expected results**. It says what not to read (`reference/` and the reference change notes) and not to run the reference until expected outputs are committed, and never to change an expected output to match the reference. It lists three gaps the spec doesn't settle (int64 overflow on IDs, CSV quoting, invalid UTF-8 reaching r2), to be raised as G23+ rather than guessed.

**`briefs/pipeline-author.md`**: start after F18+ is committed (§7 ordering). It gives an allow/deny reading list. Scope is §8 criteria 1, 2, 3 and 5; BigQuery reconciliation and CI evidence are left for later briefs. It uses the same `run` / `fixtures` CLI as the comparator expects, extends `check.sh`, and states the scale constraints (30 GB, 8 GB RAM). Done means `check.sh` passes, a replay-vs-batch test passes, and there's a real-data comparison. The pipeline agent may run the reference but may not read it.

## How independence was kept

Both briefs were written from `01-event-semantics.md`, `fixtures/README.md` and `SPEC-GAPS.md`. Facts that came from the reference work were left out on purpose: probe results, the CRC/chunk-boundary bug and its fix, DuckDB, the re-feed design. The one exception is the real-data observation that some events have `repo: {}`. That's a fact about the data, not the code.

## Not done

- The §7 table isn't extended; the verifier proposes that.
- No brief yet for §5.2 reconciliation or CI evidence.
