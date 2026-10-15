# Change note: one check command (`check.sh`)

**Date:** 2026-10-14
**Files:** `check.sh` (new), `README.md`, `changes/2026-10-14-refactor-proposal-shared-contract.md` (item 3 marked done)
**Spec:** no change
**Status:** committed locally, not pushed

## Why

Refactor proposal item 3, chosen by Steven. `tools/` ran on system `python3` and `reference/` needed `.venv` (DuckDB), so the checks were three commands with two interpreters. §8 requires CI-generated evidence, so CI needs a single command to call.

## What changed

- **`check.sh`** runs, using one interpreter (`.venv/bin/python`, or `$PYTHON` if set):
  1. `python -m unittest tools/test_compare_outputs.py`
  2. `reference/reference.py fixtures fixtures <tmp>`
  3. `tools/compare_outputs.py fixtures fixtures <tmp>`

  It stops at the first failure (`set -euo pipefail`), and its exit code is the failing step's exit code. Outputs go to a temp dir that's deleted on exit, so nothing is left in the repo. If the interpreter is missing, it prints the setup command and exits 2.
- **`README.md`** had only a title. It now has the one-time venv setup and `./check.sh`.

No Python code changed. `tools/` is still stdlib-only, so it also runs on system `python3`.

## Verification

| Check | Result |
|---|---|
| `./check.sh` | 21 tests OK; 17/17 fixtures equal; PASS; exit 0 |
| Extra row appended to `F01/expected/r1.csv` (then reverted) | exit 1 |
| `PYTHON=/nonexistent ./check.sh` | setup hint printed, exit 2 |

## Not done

- No CI config yet. When there is one, it should run `./check.sh`. `evidence/gate1.json` (§8 item 6) is a separate task.
