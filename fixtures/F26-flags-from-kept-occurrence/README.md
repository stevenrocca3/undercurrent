# F26: flags evaluated from kept occurrence hour after deduplication

Hours 0..2 requested. Tests that flags (`late`, `future_skewed`) are evaluated over kept occurrences only, using the kept occurrence's `source_file_hour` (§4, SPEC-GAPS G9):
- Event `26001` (`created_at = "2026-09-01T02:30:00Z"`) appears in Hour 0 and Hour 2:
  - Kept occurrence is Hour 0 (line 7). Relative to Hour 0 (`2026-09-01T00:00:00Z`), `02:30:00 > 00:00 + 2h`, so it is **future_skewed**.
  - If evaluated relative to the discarded occurrence's hour (Hour 2), `02:30:00 <= 02:00 + 2h`, so it would not be future-skewed.
  - Because flags use the kept occurrence, `future_skewed = 1`.
- Event `26002` (`created_at = "2026-09-01T00:30:00Z"`) appears in Hour 0 and Hour 2:
  - Kept occurrence is Hour 0 (line 8). Relative to Hour 0, `00:30:00 >= 00:00 - 1h`, so it is not late.
  - If evaluated relative to the discarded occurrence's hour (Hour 2), `00:30:00 < 02:00 - 1h = 01:00:00`, so it would wrongly be flagged late.
  - Because flags use the kept occurrence, `late = 0`.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T02:00:00Z` (3 hours). Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz`, `2026-09-01-1.json.gz`, `2026-09-01-2.json.gz`.
- Depends on SPEC-GAPS G9 (flags counted over kept occurrences only, using kept occurrence's source_file_hour).

## Input lines

| file | line | id | created_at | intent |
|---|---|---|---|---|
| `2026-09-01-0.json.gz` | 1-6 | 1001-1006 | B1-B6 | F01 baseline |
| `2026-09-01-0.json.gz` | 7 | 26001 | 02:30:00Z | kept occurrence; future_skewed relative to H0 |
| `2026-09-01-0.json.gz` | 8 | 26002 | 00:30:00Z | kept occurrence; not late relative to H0 |
| `2026-09-01-1.json.gz` | 1 | 26003 | 01:10:00Z | normal event |
| `2026-09-01-2.json.gz` | 1 | 26001 | 02:30:00Z | duplicate copy; discarded |
| `2026-09-01-2.json.gz` | 2 | 26002 | 00:30:00Z | duplicate copy; discarded |

## Expected outputs, derived

- **registry:**
  - `2026-09-01T00:00:00Z,present`
  - `2026-09-01T01:00:00Z,present`
  - `2026-09-01T02:00:00Z,present`
- **r1:** Canonical = 8 (H0) + 1 (H1) + 2 (H2) = **11**. Q1..Q4 = 0.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 4 (B1, B3, 26001, 26002)
    - WatchEvent: 3 (B2, B4, B6)
  - 2026-09-01T01:00:00Z:
    - PushEvent: 1 (26003)
  - (Hour 2 has 0 kept occurrences, so no rows).
- **r3:** 9 distinct IDs, duplicate_count = **2** (H2 lines 1 and 2), conflict_count = **0**.
- **r4:** Unchanged from F01: 501 = **2**, 502 = **1**.
- **r5:** Unchanged from F01: 501 = **2**, 502 = **1**.
- **flags:**
  - `future_skewed,1` (from kept occurrence 26001 in H0)
  - `late,0` (kept occurrence 26002 in H0 is not late)
  - `unrecognized_type,0`
