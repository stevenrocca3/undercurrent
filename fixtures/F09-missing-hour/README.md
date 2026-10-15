# F09: missing hour inside the requested range

Three hours are requested. Hours 0 and 2 exist; hour 1 has no file.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T02:00:00Z` (inclusive, so 3 hours). Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz` (6 lines), `2026-09-01-2.json.gz` (2 lines). **No `2026-09-01-1.json.gz`.**

## Input lines

| file | line | id | content | intent |
|---|---|---|---|---|
| hour 0 | 1-6 | 1001-1006 | F01 baseline | baseline |
| hour 2 | 1 | 9001 | PushEvent, alice, repo 501, 02:10:00 | proves hour 2 is processed after the gap |
| hour 2 | 2 | 9002 | WatchEvent `started`, erin 205, repo 501, 02:20:00 | star in hour 2 |

## Expected outputs, derived

- **registry:** 00 `present`, 01 **`missing`**, 02 `present`. Exactly one row per requested hour.
- **r1:** canonical = 6 + 2 = **8**; Q* = 0. A missing file contributes no lines and no quarantine rows.
- **r2:** hour 00 as F01. Hour 02: PushEvent **1**, WatchEvent **1**. **No hour-01 rows**: zero-count rows are omitted in r2.
- **r3:** 8, 0, 0.
- **r4:** 501 = 2 + 1 = **3**, 502 = **1**.
- **r5:** 9002's `available_at` = 02:00 + 7h = 09:00 on Sep 1, <= t. 501 = **3**, 502 = **1**.
- **flags:** all 0 (02:10 and 02:20 are inside hour 2's bounds).
