# Change note: GEMINI.md and .geminiignore

**Date:** 2026-10-14
**Files:** new `GEMINI.md` and `.geminiignore`; one line reworded in `changes/2026-10-14-spec-v0.7-g23-g25-and-fixtures.md`
**Spec:** no change
**Status:** committed locally, not pushed

## Why

Gemini CLI is the verifier, and possibly the pipeline author. It hit its usage limit partway through its first task. It had no project instructions, so it spent requests finding its way around the repo. Nothing but the brief's wording kept it away from `reference/`.

## What changed

- **`GEMINI.md`** (loaded by Gemini CLI every session):
  - the spec is authoritative, and spec edits are proposals only
  - a one-role-per-session table (verifier or pipeline author)
  - the independence rules, including no reading through shell commands
  - a repo layout table and the commands
  - Steven's working rules: a change note per change, no over-coding, commit locally and never push
  - ways to keep request count down
- **`.geminiignore`** hides two groups of files:
  - **for independence:** `reference/`, the reference change notes, the refactor proposal, and `changes/2026-10-14-agent-briefs.md`, which names reference internals
  - **as noise:** `.venv/`, the installed skills, output folders, and the binary `fixtures/*/input/`
- **The spec v0.7 note** had one line describing *how* the reference meets G23–G25 (which Python mechanisms it uses). That line now says only that it conforms.

## Limits

- `.geminiignore` applies to Gemini's file tools only. Shell commands (`cat`, `git show`) can still read anything, so `GEMINI.md` forbids that, but nothing enforces it. Full isolation would need a separate checkout without `reference/`.
- The old wording of the v0.7 note is still in git history (`c522977`).

## Verification

`./check.sh`: exit 0.
