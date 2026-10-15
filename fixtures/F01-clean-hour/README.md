# F01: clean hour, mixed event types

Baseline. Every other fixture is "F01 plus one anomaly". Check this one carefully first: the other fixtures' expected outputs are F01's numbers plus a small delta.

- Requested hours: `2026-09-01T00:00:00Z` only.
- Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 6 lines. `source_file_hour` = `2026-09-01T00:00:00Z`.

## Input lines (the "baseline", B1 to B6)

| line | id | type | actor | repo | created_at | intent |
|---|---|---|---|---|---|---|
| 1 | 1001 | PushEvent | 201 alice | 501 acme/rocket | 2026-09-01T00:05:00Z | baseline; only line with `org` (901) |
| 2 | 1002 | WatchEvent `started` | 202 bob | 501 acme/rocket | 2026-09-01T00:10:00Z | baseline star |
| 3 | 1003 | PushEvent | 201 alice | 502 acme/zephyr | 2026-09-01T00:15:00Z | baseline |
| 4 | 1004 | WatchEvent `started` | 203 carol | 502 acme/zephyr | 2026-09-01T00:20:00Z | baseline star |
| 5 | 1005 | IssuesEvent `opened` | 202 bob | 502 acme/zephyr | 2026-09-01T00:30:00Z | has `payload.action` but is not a star |
| 6 | 1006 | WatchEvent `started` | 204 dave | 501 acme/rocket | 2026-09-01T00:40:00Z | baseline star |

Exact bytes: `B1`..`B6` in `../generate_inputs.py`.

## Expected outputs, derived

- **r1:** all 6 lines are valid JSON, have every required field, parseable `created_at`, correct ID types. canonical = 6; Q1..Q4 = 0.
- **r2:** hour 00: PushEvent = lines 1, 3 = **2**; WatchEvent = lines 2, 4, 6 = **3**; IssuesEvent = line 5 = **1**.
- **r3:** 6 distinct ids (1001..1006), 0 duplicates, 0 conflicts.
- **r4:** stars are lines 2, 4, 6. Repo 501: lines 2, 6 = **2**. Repo 502: line 4 = **1**. All on 2026-09-01. Line 5 has an action (`opened`) but is not a WatchEvent, so it does not count.
- **r5:** `available_at` for every line = 00:00 + 1h + 6h = `2026-09-01T07:00:00Z`. Cutoff t = `2026-09-02T00:00:00Z`; window `[2026-08-26T00:00:00Z, 2026-09-02T00:00:00Z)`. All stars are inside it and 07:00 <= t. Repo 501 = **2**, 502 = **1**.
- **registry:** hour 00 file exists and decodes: `present`.
- **flags:** late bound = 2026-08-31T23:00:00Z, future bound = 2026-09-01T02:00:00Z. Every `created_at` is between 00:05 and 00:40, so late = 0, future_skewed = 0. All types (Push, Watch, Issues) are in `event_types.txt`, so unrecognized_type = 0.
