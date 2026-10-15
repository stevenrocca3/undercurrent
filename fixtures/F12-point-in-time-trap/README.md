# F12: point-in-time trap

A star whose `event_time` is before cutoff t but whose `available_at` is after t must be excluded from r5. At a later cutoff it is counted. This fixture also covers both inclusive r5 boundaries: `available_at = t` and `event_time = t − 7d`.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T02:00:00Z`.
- Cutoffs: **t1 = `2026-09-01T08:00:00Z`**, **t2 = `2026-09-01T09:00:00Z`**, **t3 = `2026-09-08T00:20:00Z`**.
- Inputs: hour 0 (6 lines), hour 1 (1 line), hour 2 (1 line).
- r5 rule: count star events with `t − 7d <= event_time < t` AND `available_at <= t`. Backfill `available_at = source_file_hour + 1h + 6h`.

## Input lines

| file | line | id | content | available_at | intent |
|---|---|---|---|---|---|
| hour 0 | 1-6 | 1001-1006 | F01 baseline (stars: 1002 → 501 @00:10, 1004 → 502 @00:20, 1006 → 501 @00:40) | 07:00 | baseline |
| hour 1 | 1 | 12001 | WatchEvent `started`, erin 205, repo 502, 01:10:00 | **08:00** | `available_at` **equals** t1, so counted at t1 (`<=`) |
| hour 2 | 1 | 12002 | WatchEvent `started`, frank 206, repo 501, 02:10:00 | **09:00** | **THE TRAP:** event_time 02:10 < t1, but available 09:00 > t1, so excluded at t1 and counted at t2 |

## r5 derived, per cutoff

Star table (all dated 2026-09-01):

| id | repo | event_time | available_at | t1 08:00 | t2 09:00 | t3 Sep 8 00:20 |
|---|---|---|---|---|---|---|
| 1002 | 501 | 00:10 | 07:00 | in | in | **out**: 00:10 < window start 00:20 |
| 1004 | 502 | 00:20 | 07:00 | in | in | **in**: exactly window start, inclusive |
| 1006 | 501 | 00:40 | 07:00 | in | in | in |
| 12001 | 502 | 01:10 | 08:00 | **in** (08:00 <= 08:00) | in | in |
| 12002 | 501 | 02:10 | 09:00 | **out** (09:00 > 08:00) | **in** (09:00 <= 09:00) | in |

- t1 window = [2026-08-25T08:00, 2026-09-01T08:00). Every event_time is inside. 501 = 1002 + 1006 = **2**; 502 = 1004 + 12001 = **2**.
- t2 window = [2026-08-25T09:00, 2026-09-01T09:00). 501 = 1002 + 1006 + 12002 = **3**; 502 = **2**.
- t3 window = [2026-09-01T00:20, 2026-09-08T00:20). Every available_at is far before t3. 501 = 1006 + 12002 = **2**; 502 = 1004 + 12001 = **2**.

Note that t1 and t3 both give (2, 2), but for different reasons (availability at t1, window start at t3). The README table shows which events make up each count.

## Other expected outputs

- **r1:** canonical = **8**; Q* = 0.
- **r2:** hour 00 as F01; hour 01 WatchEvent **1**; hour 02 WatchEvent **1**.
- **r3:** 8, 0, 0.
- **r4:** 501 = 2 + 1 = **3**, 502 = 1 + 1 = **2** (r4 has no cutoff).
- **registry:** 00, 01, 02 all `present`. **flags:** all 0.
