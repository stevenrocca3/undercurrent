# F15: Q4, ID field of the wrong JSON type

F01 plus three Q4 lines, one per ID field, and one line with a wrong-typed `org.id` that must **not** be Q4.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 10 lines.
- Depends on SPEC-GAPS G2: `id` must be a JSON string; `actor.id` and `repo.id` must be JSON integers; `org.id` never triggers Q4 (a wrong type is stored as `org_id = null`).

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | `15001` (**JSON number**) | PushEvent, alice, repo 501, 00:45:00 | Q4: id is never cast to string |
| 8 | 15002 | WatchEvent `started`, erin 205, **`"repo":{"id":"501",...}`**, 00:50:00 | Q4. A would-be star on 501, so if it leaks, r4 shows 501 = 3. |
| 9 | 15003 | PushEvent, **`"actor":{"id":"201",...}`**, repo 502, 00:55:00 | Q4 |
| 10 | 15004 | PushEvent, alice, repo 502, 00:58:00, **`"org":{"id":"901",...}`** | **canonical**: org is optional, so G2 says its type cannot cause Q4 |

## Expected outputs, derived

- **r1:** Q4 = lines 7, 8, 9 = **3**. canonical = lines 1-6 and 10 = **7**. 7 + 3 = 10.
- **r2:** hour 00: Issues **1**, Push = 1, 3, 10 = **3**, Watch = 2, 4, 6 = **3**.
- **r3:** 7 distinct (1001-1006, 15004), 0, 0.
- **r4 / r5:** same as F01: 501 = 2, 502 = 1.
- **registry:** `present`. **flags:** all 0.

The canonical value of line 10's `org_id` (null) is not visible in any R-output.
