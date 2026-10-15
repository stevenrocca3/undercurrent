# Refactor proposal: cross-file duplication and tooling

**Date:** 2026-10-14
**Status:** proposal only. **Nothing here is done.** Steven decides each item.
**Overall:** the codebase is **not messy yet** (~850 lines across 4 Python files). These items are worth settling now because the pipeline, the next large addition, will copy whatever patterns exist.

## 1. The output contract is written down in four places

The R1–R7 file names, headers and fixed rows (`Q1..Q4,canonical`, `future_skewed,late,unrecognized_type`) are spelled out separately in:

| Where | What |
|---|---|
| `01-event-semantics.md` §6 | the authoritative table |
| `tools/compare_outputs.py` | `OUTPUT_FILES` |
| `reference/reference.py` | headers inline in `write_outputs()` |
| `fixtures/README.md` + 17 × `expected/*.csv` | headers in data |

The pipeline will be a fifth copy. Drift is caught at run time (a header mismatch fails the comparator), so the risk is wasted debugging, not silent error.

**Option A (recommended): leave it.** The spec is the source; the comparator enforces it. A shared module would be imported by both the reference and the pipeline, and that's the coupling the §6 independence rule exists to prevent.
**Option B:** a neutral data file such as `contract/outputs.json` (file → header, fixed rows) that the reference, pipeline and comparator all read. It removes the copies, but the "independent" implementations then share one input that could be wrong for both.

## 2. `event_types.txt` lives in `fixtures/` but is spec data

The reference reads `fixtures/event_types.txt` by relative path, and the pipeline will too. The list belongs to the spec (§2), not to the test data.
**Proposal:** move it to `spec/event_types.txt` (or the repo root) and update §2, the reference and the fixtures README. Low risk; a fixtures re-run proves it.

## 3. Two Python environments

`tools/` runs on system `python3` (stdlib only); `reference/` needs `.venv` (DuckDB). That's easy to get wrong, and it's already in the commands in the PR description.
**Proposal:** run everything through `.venv/bin/python`, and add one `check.sh` (or a `Makefile` target) that runs: comparator tests → reference on fixtures → `compare_outputs.py fixtures`. That's also what CI should run (§8 requires CI-generated evidence).

## 4. The reference's edge-case probes aren't in the repo

The ~20 edge cases checked while writing the reference (null fields, `[1,2]`, bool `repo.id`, CRC error at 4 chunk sizes, multi-member gzip, …) ran as throwaway scripts. Today the only repeatable check on the reference is the 17 fixtures.
**Proposal:** either (a) have the verifier turn them into fixtures F18+ with hand-written expected outputs, which is the §7-consistent route and covers the pipeline too, or (b) add `reference/test_reference.py` unit tests for `classify()` and `read_hour()`. **(a) recommended:** it tests both implementations, and (b) would test only the reference.

## 5. Change notes are piling up per step

Seven notes on 2026-10-14 alone. That's fine for review, but there's no index.
**Proposal:** a one-line-per-note list in `changes/README.md`, or keep relying on the date-prefixed filenames. Optional.

## Suggested order

Items 3 and 4a first: they make every later check one command and give the pipeline more fixtures. Item 2 alongside. Items 1 and 5: decide, likely no action.
