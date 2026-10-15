# F21: Q3 timestamp strictness and valid ISO-8601 variations

F01 plus lines testing Q3 quarantine rules and ISO-8601 parsing strictness (§2, SPEC-GAPS G17, G22):
- lowercase `z` -> Q3
- lowercase `t` -> Q3
- no seconds (`YYYY-MM-DDTHH:MMZ`) -> Q3
- date only (`YYYY-MM-DD`) -> Q3
- leap second `:60` -> Q3
- 7 fractional digits -> Q3
- numeric `created_at` (Unix epoch number) -> Q3
- 6 fractional digits (valid microseconds) -> canonical
- `+05:30` offset that crosses into the previous UTC date (`2026-09-01T05:00:00+05:30` = `2026-08-31T23:30:00Z`) -> valid, canonical, UTC date `2026-08-31` (visible in r4)

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 15 lines.
- Depends on SPEC-GAPS G17 (created_at formats accepted), G22 (Q3 strictness).

## Input lines

| line | id | content / anomaly | status / intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 21001 | `"created_at": "2026-09-01T00:50:00z"` | lowercase `z` -> Q3 |
| 8 | 21002 | `"created_at": "2026-09-01t00:50:00Z"` | lowercase `t` -> Q3 |
| 9 | 21003 | `"created_at": "2026-09-01T00:50Z"` | missing seconds -> Q3 |
| 10 | 21004 | `"created_at": "2026-09-01"` | date only -> Q3 |
| 11 | 21005 | `"created_at": "2026-09-01T23:59:60Z"` | leap second `:60` -> Q3 |
| 12 | 21006 | `"created_at": "2026-09-01T00:50:00.1234567Z"` | 7 fractional digits -> Q3 |
| 13 | 21007 | `"created_at": 1788220800` | numeric timestamp -> Q3 |
| 14 | 21008 | `"created_at": "2026-09-01T00:50:00.123456Z"`, PushEvent, 501 | 6 fractional digits -> valid canonical |
| 15 | 21009 | `"created_at": "2026-09-01T05:00:00+05:30"`, WatchEvent `started`, 501 | +05:30 offset converts to 2026-08-31T23:30:00Z -> valid canonical |

## Expected outputs, derived

- **r1:** canonical = lines 1-6 (B1..B6) + line 14 (21008) + line 15 (21009) = **8**. Q3 = lines 7..13 = **7**. Q1 = 0, Q2 = 0, Q4 = 0. Total = 15 lines.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 3 (B1, B3, 21008)
    - WatchEvent: 4 (B2, B4, B6, 21009)
- **r3:** 8 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:**
  - 501: line 15 UTC date is 2026-08-31 (1 star); B2 and B6 UTC date is 2026-09-01 (2 stars).
  - 502: B4 UTC date is 2026-09-01 (1 star).
  - Rows:
    - `501,2026-08-31,1`
    - `501,2026-09-01,2`
    - `502,2026-09-01,1`
- **r5:** Cutoff `2026-09-02T00:00:00Z`. Window `[2026-08-26T00:00:00Z, 2026-09-02T00:00:00Z)`. All three stars on 501 (B2, B6, 21009) are within window and `available_at` = 07:00:00Z <= t.
  - `2026-09-02T00:00:00Z,501,3`
  - `2026-09-02T00:00:00Z,502,1`
- **registry:** `present`.
- **flags:** line 15 UTC event_time `2026-08-31T23:30:00Z` is >= `source_file_hour - 1h` (`2026-08-31T23:00:00Z`), so not late. All flags are 0.
