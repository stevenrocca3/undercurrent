# F18: valid JSON that is not an object, empty lines, and bad UTF-8

F01 plus lines testing Q1 quarantine rules (§2, SPEC-GAPS G13):
- Valid JSON that is not an object (`[1, 2]`, `42`, `"x"`)
- An empty line between two good lines (`""`)
- A line containing invalid UTF-8 bytes

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 13 lines.
- Depends on SPEC-GAPS G13 (decided): valid JSON that is not an object, and empty lines, are Q1.

## Input lines

| line | content | status / intent |
|---|---|---|
| 1-6 | B1-B6 | F01 baseline |
| 7 | `[1, 2]` | valid JSON array, not an object -> Q1 |
| 8 | `42` | valid JSON integer, not an object -> Q1 |
| 9 | `"x"` | valid JSON string, not an object -> Q1 |
| 10 | 18001 (PushEvent, alice, 501, 00:50:00Z) | good canonical line |
| 11 | `""` (empty line) | empty line between two good lines -> Q1 |
| 12 | 18002 (PushEvent, alice, 501, 00:51:00Z) | good canonical line |
| 13 | raw bytes with invalid UTF-8 (`b'{"id":"18003",\xff\xfe}'`) | cannot decode as UTF-8 / JSON -> Q1 |

## Expected outputs, derived

- **r1:** 
  - canonical: lines 1-6 (B1..B6) + line 10 (18001) + line 12 (18002) = **8**.
  - Q1: lines 7, 8, 9, 11, 13 = **5**.
  - Q2, Q3, Q4: 0.
  - Total: 8 + 5 = 13 lines.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 4 (B1, B3, 18001, 18002)
    - WatchEvent: 3 (B2, B4, B6)
- **r3:** 8 distinct IDs (1001-1006, 18001, 18002), 0 duplicates, 0 conflicts.
- **r4:** stars unchanged from F01: 501 = **2**, 502 = **1**.
- **r5:** stars unchanged from F01: 501 = **2**, 502 = **1**.
- **registry:** `present`.
- **flags:** all 0.
