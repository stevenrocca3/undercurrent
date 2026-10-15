# F07: late event

F01 plus one late star and one row exactly on the late boundary.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 8 lines. `source_file_hour` = 2026-09-01T00:00:00Z.
- Late rule (§4): `event_time < source_file_hour − 1h` = `event_time < 2026-08-31T23:00:00Z` (strict).

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 7001 | WatchEvent `started`, erin 205, repo 501, created **2026-08-31T22:59:59Z** | late: 1 s before the bound. It also lands on a **different UTC date** (Aug 31) from its file (Sep 1). |
| 8 | 7002 | PushEvent, alice, repo 502, created **2026-08-31T23:00:00Z** | exactly on the bound, so **not** late (strict `<`) |

## Expected outputs, derived

- **r1:** canonical = **8**; Q* = 0. Late events are kept, not quarantined.
- **r2:** attributed by `source_file_hour` (hour 00), not by event_time. Push = 1, 3, 8 = **3**; Watch = 2, 4, 6, 7 = **4**; Issues = **1**.
- **r3:** 8 distinct, 0, 0.
- **r4:** by UTC date of **event_time**. 7001 goes to (501, **2026-08-31**) = 1. Rows: (501, 2026-08-31, 1), (501, 2026-09-01, 2), (502, 2026-09-01, 1).
- **r5:** t = 2026-09-02T00:00:00Z, window starts 2026-08-26T00:00:00Z, so 22:59:59 on Aug 31 is inside. `available_at` = 07:00 on Sep 1, <= t. Repo 501 = 2 + 1 = **3**, 502 = **1**.
- **registry:** `present`.
- **flags:** late = **1** (line 7 only), future_skewed = 0, unrecognized_type = 0.
