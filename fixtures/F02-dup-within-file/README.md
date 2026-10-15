# F02: exact duplicate within one file

F01 plus line 7, a byte-for-byte copy of line 2 (a star).

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 7 lines.

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline B1..B6, unchanged | baseline |
| 7 | 1002 | identical bytes to line 2 (WatchEvent `started`, bob, repo 501, 00:10:00) | the duplicate |

## Expected outputs, derived

- **r1:** both copies are valid lines and become canonical records before dedup: canonical = 6 + 1 = **7**; Q* = 0.
- **r3:** distinct ids = 6. Id 1002 appears twice; keep line 2 (smaller `source_line`), discard line 7: duplicate_count = **1**. Same bytes, so same `record_hash`: conflict_count = **0**.
- **r2:** after dedup it is the same as F01 (Issues 1, Push 2, Watch 3). If WatchEvent shows 4, dedup did not run.
- **r4:** same as F01. Repo 501 = **2**, not 3. The duplicated event is a star, so this also checks that r4 runs after dedup.
- **r5:** same as F01: 501 = 2, 502 = 1.
- **registry:** hour 00 `present`. **flags:** all 0.
