# Change note: remove iCloud duplicate files

**Date:** 2026-10-15
**Files:** 25 tracked `* 2*` files deleted; 18 empty `fixtures/F* 2/` folders removed (untracked); `.gitignore`
**Spec:** no change
**Status:** committed on `remove-icloud-duplicates`, not pushed

## What happened

`~/Documents` is synced by iCloud Drive (Desktop & Documents). On a sync conflict, iCloud keeps both versions by saving a copy named `name 2.ext`. Commit `8e5d86e` ("Fixed the mds, CVS, and implemented step 1") added 25 such copies, and PR #4 merged them into `main`. That commit contains **no pipeline code**; step 1 is still only on the clone's `pipeline` branch.

## Why it matters

- **Independence leak.** The copies include `reference/reference 2.py` and duplicates of the hidden reference notes. The clone's sparse-checkout patterns and `.geminiignore` match the original names only, so merging `main` into `pipeline` would have put the reference code in front of the pipeline agent.
- **Phantom fixtures.** 18 empty `fixtures/F* 2/` folders. They're harmless today only because the tools look for `expected/` or `fixture.json` inside each folder.

## What changed

- All 25 tracked copies were deleted. Each was checked first to be byte-identical to its original on `main`, so no content is lost.
- The 18 empty duplicate fixture folders were deleted.
- `.gitignore` now has `* 2` and `* 2.*`, so new iCloud copies can't be committed by accident.

## Verification

- `./check.sh`: exit 0.
- After the change, no `* 2*` paths remain outside `.venv/` and `.git/`.

## Not fixed: the cause

While the repo is inside an iCloud-synced folder, iCloud can keep making copies, and it can also damage `.git/` itself. Moving both `undercurrent/` and `undercurrent-pipeline/` outside `~/Documents` (for example to `~/code/`) fixes the cause. Steven decides.
