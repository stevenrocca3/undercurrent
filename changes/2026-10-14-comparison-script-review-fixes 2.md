# Change note: comparison script, review follow-up

**Date:** 2026-10-14
**Files:** `tools/compare_outputs.py`, `tools/test_compare_outputs.py`
**Spec:** no change (stays v0.4)
**Status:** awaiting Steven's review

## Why

A review raised three points about `compare_outputs.py`. Each one was checked against the code and probed directly. **All three already held; no comparison logic changed.** What was missing was tests that pin the behaviour down and wording that leaves no ambiguity.

| Review point | Finding | Change |
|---|---|---|
| Sort must use UTF-8 byte or default `list.sort()` order on both sides | Already true. Python's `str` sort orders by Unicode code point, which is identical to UTF-8 byte order and independent of locale. Both sides are sorted in the same process, so environments can't differ. | Docstring states it. Test `test_sort_is_code_point_order`. |
| Header must be compared before sorting, never sorted into the rows | Already true. `read_csv_lines` returns `lines[0]` as the header, and only `lines[1:]` is sorted. | Docstring states it. Test `test_header_never_sorted_into_rows`: a file whose header was moved into the body fails with "header differs". |
| "Empty file fails" must mean 0 bytes, not a header-only file | Already true. A header-only file (`header\n`) is valid with zero rows; only a 0-byte file is rejected. This matters because r2, r4 and r5 can legitimately have no rows. | The error message now says "0-byte file … (a header-only file is valid: zero rows)". Tests `test_header_only_files_pass`, `test_header_only_vs_rows_fails`, `test_zero_byte_file_fails`. |

One more test was added while checking encodings: `test_invalid_utf8_fails_cleanly`. Invalid UTF-8 reports `FAIL … actual file invalid` instead of crashing. This already worked, because `UnicodeDecodeError` is a subclass of `ValueError`; the test pins it.

## Correction to the previous note

`2026-10-14-comparison-script.md` said "an empty file fails". Read it as **"a 0-byte file fails"**. A header-only file passes when both sides are header-only.

## Tests

`python3 -m unittest tools/test_compare_outputs.py`: 20 tests (was 14), all passing on 2026-10-14.
