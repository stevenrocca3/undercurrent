# F03: exact duplicate across two files

F01 (hour 0) plus an hour-1 file whose **first** line is a byte-for-byte copy of hour 0's **fourth** line.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T01:00:00Z`. Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz` (6 lines), `2026-09-01-1.json.gz` (2 lines).

## Input lines

| file | line | id | content | intent |
|---|---|---|---|---|
| hour 0 | 1-6 | 1001-1006 | F01 baseline, unchanged | baseline |
| hour 1 | 1 | 1004 | identical bytes to hour 0 line 4 (WatchEvent `started`, carol, repo 502, created 00:20:00) | cross-file duplicate |
| hour 1 | 2 | 3001 | PushEvent, carol, repo 502, created 01:10:00 | an ordinary hour-1 event, so hour 1 is not empty after dedup |

**Trap:** the copy is at line 1 and the original at line 4. Dedup must keep the smallest `(source_file_hour, source_line)`, which is (hour 0, line 4). An implementation that compares `source_line` alone keeps (hour 1, line 1) and attributes the WatchEvent to hour 01 in r2.

The hour-1 copy has created_at 00:20, which is not before hour 1 minus 1h (00:00). So it would not be late anyway, and it is discarded.

## Expected outputs, derived

- **r1:** 6 + 2 = **8** canonical before dedup; Q* = 0.
- **r3:** distinct ids: 1001-1006 and 3001 = **7**. duplicate_count = **1** (hour 1 line 1). Identical bytes: conflict_count = **0**.
- **r2:** hour 00 as F01 (Issues 1, Push 2, Watch 3). Hour 01: only 3001 survives, so PushEvent = **1**. There is no hour-01 WatchEvent row.
- **r4:** same as F01: 501 = 2, 502 = **1** (not 2).
- **r5:** the kept 1004 has `available_at` 07:00, and 3001 is not a star. Same as F01: 501 = 2, 502 = 1.
- **registry:** hour 00 `present`, hour 01 `present`. **flags:** all 0.
