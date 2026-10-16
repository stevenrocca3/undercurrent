# F29: late hour R5 availability boundary

The hour-00 file contains one star with event time 00:30. Its `available_at.csv` value is 02:00, later than its due time `h+1h` (01:00).

## Input lines

| hour / line | event | repo | event time | intent |
|---|---|---|---|---|
| 00 / 1 | 29001, WatchEvent started | 501 | 00:30 | before both cutoffs; unavailable at 01:30 and available exactly at 02:00 |

## Expected outputs, derived

The one line is canonical and distinct (r1 canonical = 1; r3 = 1/0/0), is one WatchEvent for hour 00, and is one repo-501 star on 2026-09-01. At cutoff 01:30, `available_at > t`, so R5 has no rows. At cutoff 02:00, `available_at == t` and event time is in `[t−7d,t)`, so R5 has repo 501 = 1. The file is `present`; all flags are zero.
