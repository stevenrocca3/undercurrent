# Change note: output comparison script

**Date:** 2026-10-14
**Files:** new `tools/compare_outputs.py` and `tools/test_compare_outputs.py`
**Spec:** no change to `01-event-semantics.md` (stays v0.4)
**Status:** written by an agent; **Steven reviews** (§6: "An agent may write the comparison script; Steven reviews it.")

## Why

§6 and §8 need an exact-equality check in two places:
- Each fixture's expected outputs vs. what the pipeline or the reference produced from that fixture's input.
- Reference vs. pipeline over September 2026 (Gate 1, criterion 2).

## Usage

```
python3 tools/compare_outputs.py dirs EXPECTED_DIR ACTUAL_DIR
python3 tools/compare_outputs.py fixtures fixtures/ ACTUAL_ROOT   # expects ACTUAL_ROOT/F01-clean-hour/r1.csv, ...
```

Exit code 0 means everything is equal, 1 means any difference, and 2 means a usage error. The script prints `ok`/`FAIL` per file, the differing rows (`-` expected only, `+` actual only, up to 10 each), and an `N/17 fixtures equal` summary.

## What it checks, and what passing means

- It compares the seven outputs: R1–R5, `registry.csv` (R6) and `flags.csv` (R7). Each must exist on both sides; a missing file fails. Extra CSVs on the actual side are listed but don't fail.
- **The header must match exactly.**
- **Rows are compared as exact text after sorting both sides.** This is the "exact equality check after sorting" from §6. Cell text is never normalized: `7` ≠ `07`, and there is no whitespace trimming and no tolerance. Duplicate rows count, so a row produced twice fails.
- **The CSV format is enforced:** LF line endings only (any CR fails), a trailing LF is required, and an empty file fails.

**A pass proves** that the two sides produced identical output text for those seven files.
**A pass does not prove:**
- That either side is correct. Two implementations with the same bug pass.
- Anything about tables outside the contract, such as the `conflicts` table or quarantine contents.
- That the producer wrote rows in sorted order. Row order isn't checked.

## A decision embedded here that you should review

**Row order is not compared.** The §6 contract says rows are "sorted ascending by every column". It doesn't say whether numeric columns sort as numbers (`99` before `501`) or as text (`501` before `99`). Because the comparator sorts both sides itself, that ambiguity can't cause a false failure. The cost is that a producer that writes unsorted output isn't caught. If you want sort order enforced, the spec has to settle numeric vs. text order first.

## Isolation

The script uses the standard library only and imports nothing from the pipeline (and there is no pipeline yet). The tests import only the comparator and read `fixtures/`.

## Tests

`python3 -m unittest tools/test_compare_outputs.py` runs 14 tests, all passing on 2026-10-14. They cover:
- identical outputs;
- reversed row order (passes);
- a changed count, an extra row, a duplicated row;
- a missing file, a renamed header column, CRLF, a missing trailing LF;
- `08` vs `8`;
- an extra file (noted, not failed);
- fixtures mode with all 17 outputs equal, and with no outputs present;
- a usage error.
