# F19: required field present as null, missing public key, repo empty object

F01 plus lines testing Q2 quarantine rules (§2, SPEC-GAPS G14, G16):
- `id` present as `null`
- `payload` present as `null`
- `repo.id` present as `null`
- `public` key missing
- `repo` is an empty object (`{}`)

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 11 lines.
- Depends on SPEC-GAPS G14 (missing `public` and `payload` are Q2), G16 (JSON `null` in required fields is Q2).

## Input lines

| line | id | content / anomaly | status / intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | null | `"id": null` | required field null -> Q2 |
| 8 | 19002 | `"payload": null` | required field null -> Q2 |
| 9 | 19003 | `"repo": {"id": null, "name": "acme/rocket"}` | `repo.id` null -> Q2 |
| 10 | 19004 | no `"public"` key | missing required field `public` -> Q2 |
| 11 | 19005 | `"repo": {}` | `repo.id` missing -> Q2 |

## Expected outputs, derived

- **r1:** canonical = **6**; Q2 = **5**; Q1 = 0, Q3 = 0, Q4 = 0. Total = 11 lines.
- **r2:** identical to F01:
  - 2026-09-01T00:00:00Z,IssuesEvent,1
  - 2026-09-01T00:00:00Z,PushEvent,2
  - 2026-09-01T00:00:00Z,WatchEvent,3
- **r3:** 6 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:** 501 = **2**, 502 = **1**.
- **r5:** 501 = **2**, 502 = **1**.
- **registry:** `present`.
- **flags:** all 0.
