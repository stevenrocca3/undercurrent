# F04: conflicting duplicate (same id, different content)

F01 plus line 7: id `1002` again, but for a **different repo**.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 7 lines.

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline, unchanged | baseline |
| 7 | 1002 | WatchEvent `started`, bob, **repo 502 acme/zephyr**, created 00:10:00. The only difference from line 2 is the repo (line 2 is 501 acme/rocket). | conflicting duplicate |

The difference was chosen to be **visible in r4**. If the wrong occurrence is kept, r4 becomes 501 = 1, 502 = 2 instead of 501 = 2, 502 = 1.

## Expected outputs, derived

- **r1:** canonical = **7**; Q* = 0.
- **r3:** distinct ids = 6. Line 7 is discarded (line 2 is earlier): duplicate_count = **1**. Its bytes differ from line 2, so its `record_hash` differs: conflict_count = **1**.
- **r2:** same as F01 (both occurrences are WatchEvent, and only one is kept).
- **r4:** keep line 2 (repo 501). Same as F01: 501 = **2**, 502 = **1**.
- **r5:** same as F01: 501 = 2, 502 = 1.
- **registry:** `present`. **flags:** all 0.

The `conflicts` table (both rows logged) is not part of this CSV contract. See SPEC-GAPS G7.
