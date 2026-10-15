# Change note: CI runs check.sh

**Date:** 2026-10-15
**Files:** new `.github/workflows/check.yml`
**Spec:** no change
**Status:** committed on `ci-check`, not pushed

## Why

§8 criterion 6 says Gate 1 evidence counts only if CI generated it. Step one is having CI at all: every push and PR runs the same checks as a local `./check.sh`.

## What changed

A GitHub Actions workflow, triggered on `push` and `pull_request`, that:
- runs on `ubuntu-latest` with Python 3.13 (matching the local `.venv`)
- runs `pip install -r requirements.txt`
- runs `./check.sh` with `PYTHON=python` (the `PYTHON` override was built in for this)

A failing check fails the job. When the pipeline branch merges, its step in `check.sh` runs here automatically.

## Verification

- Locally, `PYTHON=.venv/bin/python ./check.sh` exits 0. That's the same override path CI uses.
- `check.sh` is tracked as executable (mode 100755), so the runner can execute it.
- The workflow itself is only proven by its first run on GitHub.

## Not done yet (later step)

`evidence/gate1.json` (commit SHA, config hash, input manifest with SHA-256, every check result, overall pass/fail). It needs the September input files in CI, about 30 GB, so it needs its own design: where the data comes from, caching, and run time. That gets its own change.
