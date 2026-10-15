# F06: missing required field

F01 plus 5 lines: 4 that must be quarantined as Q2, and 1 that must **not** be.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 11 lines.

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | (none) | WatchEvent `started`, erin 205, repo 501, 00:45:00, **no `id` key** | Q2. It would be a star on 501, so if it leaks through, r4 shows 501 = 3. |
| 8 | 6002 | PushEvent, alice, `"repo":{"name":"acme/rocket"}` (**no `repo.id`**), 00:50:00 | Q2 (nested required field) |
| 9 | 6003 | **no `type` key** AND `"created_at":"not-a-date"` | Q2, **not** Q3: precedence Q1 > Q2 > Q3 > Q4, first match wins (SPEC-GAPS G1) |
| 10 | 6004 | PushEvent, `"actor":{"id":206}` (**no `login`**), no `org`, repo 502, 00:55:00 | must be **canonical**. `actor.login` and `org` are nullable and not in the Q2 list. |
| 11 | 6005 | PushEvent, alice, repo 501, 00:58:00, **no `payload` key** | Q2 (G14, decided 2026-10-14: `public` and `payload` are required) |

## Expected outputs, derived

- **r1:** Q2 = lines 7, 8, 9, 11 = **4**. canonical = lines 1-6 and 10 = **7**. Q1 = Q3 = Q4 = 0. 7 + 4 = 11.
- **r2:** hour 00: PushEvent = lines 1, 3, 10 = **3**; WatchEvent = lines 2, 4, 6 = **3**; IssuesEvent = **1**.
- **r3:** distinct ids among canonical records: 1001-1006 and 6004 = **7**; 0 duplicates; 0 conflicts. Ids 6002, 6003 and 6005 belong to quarantined lines and are not counted.
- **r4 / r5:** same as F01 (501 = 2, 502 = 1). The quarantined line 7 star is excluded.
- **registry:** `present`. **flags:** all 0 (line 10 at 00:55 is in range, type PushEvent).
