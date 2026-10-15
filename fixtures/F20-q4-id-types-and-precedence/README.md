# F20: Q4 ID field types (bool repo.id, float actor.id) and Q2 vs Q4 precedence

F01 plus lines testing Q4 quarantine rules and quarantine precedence (§2, SPEC-GAPS G1, G2):
- `repo.id` is boolean `true` -> Q4 (in JSON, bool is distinct from integer; in Python `isinstance(True, int)` is True, a classic bug trap)
- `actor.id` is float `201.0` -> Q4 (a float is not an integer)
- A line that fails both Q2 (missing `public`) and Q4 (numeric `id`: 20003) -> Q2 wins (precedence: Q1 > Q2 > Q3 > Q4)

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 9 lines.
- Depends on SPEC-GAPS G1 (first match wins, Q1->Q2->Q3->Q4), G2 (actor.id and repo.id must be integers, not float or bool).

## Input lines

| line | id | content / anomaly | status / intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 20001 | `"repo": {"id": true, ...}` | bool repo.id -> Q4 |
| 8 | 20002 | `"actor": {"id": 201.0, ...}` | float actor.id -> Q4 |
| 9 | 20003 | numeric `id`, missing `"public"` | fails Q2 & Q4 -> Q2 wins |

## Expected outputs, derived

- **r1:** canonical = **6**; Q1 = 0; Q2 = line 9 = **1**; Q3 = 0; Q4 = lines 7, 8 = **2**. Total = 9 lines.
- **r2:** identical to F01:
  - 2026-09-01T00:00:00Z,IssuesEvent,1
  - 2026-09-01T00:00:00Z,PushEvent,2
  - 2026-09-01T00:00:00Z,WatchEvent,3
- **r3:** 6 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:** 501 = **2**, 502 = **1**.
- **r5:** 501 = **2**, 502 = **1**.
- **registry:** `present`.
- **flags:** all 0.
