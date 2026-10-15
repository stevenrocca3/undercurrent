# F25: hour files outside requested range are ignored

Only hour `2026-09-01T01:00:00Z` is requested. The input directory contains files for hour 0, hour 1, and hour 2. Per §1 and SPEC-GAPS G18, files outside the requested hour range are completely ignored:
- Hour 0 (`2026-09-01-0.json.gz`) and Hour 2 (`2026-09-01-2.json.gz`) contain star events that must NOT be counted in r4 or r5.
- The registry must contain exactly one row: `2026-09-01T01:00:00Z,present`. Hours 0 and 2 must not appear in `registry.csv`.

- Requested hours: `2026-09-01T01:00:00Z` to `2026-09-01T01:00:00Z` (1 hour). Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz`, `2026-09-01-1.json.gz`, `2026-09-01-2.json.gz`.
- Depends on SPEC-GAPS G18 (files outside requested range are ignored).

## Input lines

| file | lines | intent |
|---|---|---|
| `2026-09-01-0.json.gz` | B1..B6 (includes WatchEvents on 501, 502) | outside requested range -> ignored |
| `2026-09-01-1.json.gz` | line 1: 25001 (PushEvent, 501, 01:10:00Z)<br>line 2: 25002 (WatchEvent `started`, 501, 01:20:00Z) | requested hour -> processed |
| `2026-09-01-2.json.gz` | 9001 (PushEvent), 9002 (WatchEvent `started`, 501) | outside requested range -> ignored |

## Expected outputs, derived

- **registry:** exactly one row:
  - `2026-09-01T01:00:00Z,present`
- **r1:** canonical = **2** (lines 25001, 25002); Q1..Q4 = 0.
- **r2:**
  - 2026-09-01T01:00:00Z:
    - PushEvent: 1
    - WatchEvent: 1
- **r3:** 2 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:** 501 = **1** (line 25002 on 2026-09-01). Stars in hour 0 and hour 2 are ignored.
- **r5:** Cutoff `2026-09-02T00:00:00Z`. `available_at` = 01:00 + 7h = `08:00:00Z` <= t.
  - `2026-09-02T00:00:00Z,501,1`
- **flags:** all 0.
