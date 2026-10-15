# Change note: refactor and cleanup pass

**Date:** 2026-10-15
**Files:** `reference/reference.py`, new `changes/README.md`. Outside the repo: the clone's untracked `CLAUDE.md`, and merged branches on GitHub.
**Spec:** no change
**Status:** committed on `spec-v0.10-g30`, not pushed

## Done (no behaviour change)

| Where | Change | Why |
|---|---|---|
| `reference.py` | `EPOCH` constant | the 1970 epoch was spelled out twice (`to_us`, `fmt_ts`) |
| `reference.py` | `is_star` reads `get(obj, "payload", "action")` | it repeated what `get()` already does |
| `changes/README.md` | one-line index of all 22 notes, with the PR each merged in | refactor proposal item 5. Many notes still say "not pushed"; the index records the truth without rewriting history. |
| clone `CLAUDE.md` | "spec v0.7" → "latest version on `main`" | it would go stale with every spec bump |
| GitHub | deleted merged branches `ci-check`, `remove-icloud-duplicates`, `spec-v0.8-g26`, `spec-v0.9-g27-g29` | all merged into `main` |

Proof: `./check.sh`: 21 tests OK, 27/27 fixtures equal.

## Not done: for Steven to decide

1. **The reference's size limit.** §6 says "roughly 250 lines", but the reference is now 320. All of the growth comes from spec decisions: truncated-gzip recovery (R6), G28, G30. Getting back under 250 would mean making it denser, which hurts the "clarity over speed" rule in the same section. **Proposal:** change §6 to "roughly 350 lines", or remove the number.
2. **Moving `event_types.txt` out of `fixtures/`** (proposal item 2). The pipeline reads that path too, so moving it now would break the `pipeline` branch when it merges. **Proposal:** do it after the pipeline merges, as one change across spec, reference, pipeline and the fixtures README.
3. **The cause of the iCloud duplicates.** Both repos are still inside `~/Documents`, which is synced. Moving them (e.g. to `~/code/`) is the only real fix. `.gitignore` only stops the copies being committed.

Proposal items 1 (shared contract: leave as is), 3 (`check.sh`: done) and 4 (fixtures: done as F18–F27) are closed.
