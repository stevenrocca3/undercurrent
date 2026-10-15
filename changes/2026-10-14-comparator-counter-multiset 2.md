# Change note: comparator uses Counter for row differences

**Date:** 2026-10-14
**Files:** `tools/compare_outputs.py`, `tools/test_compare_outputs.py`
**Spec:** no change
**Status:** suggested by Steven; awaiting review

## What changed

`multiset_minus` switched from a sorted two-pointer merge to a `collections.Counter`.

```diff
-def multiset_minus(a, b):
-    """Rows of sorted list a not matched by a row of sorted list b (duplicates counted)."""
-    out, j = [], 0
-    for row in a:
-        while j < len(b) and b[j] < row:
-            j += 1
-        ...
+def multiset_minus(a, b):
+    """Rows of list a not matched by a row of list b (duplicates counted)."""
+    counts_b = Counter(b)
+    ...
```

## Why

The old version was correct only because both lists were already sorted. That was a hidden precondition, and a future caller passing unsorted lists would get silently wrong diffs. The `Counter` version is correct for any order, shorter, and O(n).

**Behaviour is unchanged.** It only affects which rows are *printed* in a diff; the pass/fail decision is still `sorted(expected) == sorted(actual)`.

## Tests

Added `test_multiset_minus_ignores_order_and_counts_duplicates`: an unsorted input, a duplicate row, and empty lists. That makes 21 tests, all passing.
