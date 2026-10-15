# F22: type, public, and payload with non-standard JSON types

F01 plus lines testing JSON types for `type`, `public`, and `payload` (§2, SPEC-GAPS G19):
- `type` is a JSON array `[1]`: checked for presence only (not quarantined). Stored as its JSON text `"[1]"` and flagged `unrecognized_type`.
- `public` is a string `"yes"`: checked for presence only (not quarantined).
- `payload` is a string `"x"`: checked for presence only (not quarantined).

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 9 lines.
- Depends on SPEC-GAPS G19 (decided): type, public, and payload are checked for presence only; non-string type is stored as JSON text and flagged unrecognized_type.

## Input lines

| line | id | content / anomaly | status / intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 22001 | `"type": [1]` | presence check only -> canonical; stored as `"[1]"`, flagged `unrecognized_type` |
| 8 | 22002 | `"public": "yes"`, PushEvent, 501 | presence check only -> canonical |
| 9 | 22003 | `"payload": "x"`, PushEvent, 502 | presence check only -> canonical |

## Expected outputs, derived

- **r1:** canonical = lines 1-6 (B1..B6) + lines 7, 8, 9 = **9**. Q1..Q4 = 0.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 4 (B1, B3, 22002, 22003)
    - WatchEvent: 3 (B2, B4, B6)
    - `[1]`: 1 (22001)
  - In byte order, `[` (ASCII 91) sorts after `W` (ASCII 87).
- **r3:** 9 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:** unchanged from F01: 501 = **2**, 502 = **1**. (Line 22001 is not a WatchEvent, 22002/22003 are PushEvents).
- **r5:** unchanged from F01: 501 = **2**, 502 = **1**.
- **registry:** `present`.
- **flags:**
  - future_skewed: 0
  - late: 0
  - unrecognized_type: **1** (from line 22001 whose type is `[1]`)
