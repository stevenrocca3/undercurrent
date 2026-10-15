# F14: Q3, created_at fails to parse

F01 plus two lines that go to Q3 and one valid-but-unusual timestamp that must **not** go to Q3.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 9 lines.
- Depends on SPEC-GAPS G1 (precedence), G2 (`id` must be a string), G17 (RFC 3339 with `Z` or numeric offset accepted).

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 14001 | WatchEvent `started`, erin 205, repo 501, created **`2026-13-01T00:45:00Z`** (month 13) | Q3. It would be a star on 501, so if it leaks, r4 shows 501 = 3. |
| 8 | **14002 as a JSON number** | PushEvent, alice, repo 501, created **`not-a-date`** | fails Q3 **and** Q4, so **Q3** (first match in Q1 > Q2 > Q3 > Q4) |
| 9 | 14003 | WatchEvent `started`, frank 206, repo 502, created **`2026-08-31T22:50:00-02:00`** | valid RFC 3339 with offset, so **canonical**; in UTC it is **2026-09-01T00:50:00Z** |

**What line 9 catches:** a reader that drops the offset treats it as 2026-08-31T22:50Z. That would put r4 on (502, 2026-08-31) and flag it late (22:50 < 23:00). Correct UTC conversion gives 00:50 on Sep 1, inside hour 0's bounds, with no flag.

## Expected outputs, derived

- **r1:** Q3 = lines 7, 8 = **2**. canonical = lines 1-6 and 9 = **7**. Q1 = Q2 = Q4 = 0. 7 + 2 = 9.
- **r2:** hour 00: Issues **1**, Push = 1, 3 = **2**, Watch = 2, 4, 6, 9 = **4**.
- **r3:** 7 distinct (1001-1006, 14003), 0, 0.
- **r4:** 501 = **2** (line 7 excluded). 502 = 1004 + 14003 = **2**, both on 2026-09-01.
- **r5:** all available 07:00; 00:50Z is inside the window. 501 = **2**, 502 = **2**.
- **registry:** `present`. **flags:** all 0 (line 9's UTC time 00:50 is between 23:00 the day before and 02:00).
