# F32: mixed backfill and live availability

Hour 00 is listed in `available_at.csv` with observed availability 07:00. Hour 01 is omitted and therefore uses backfill availability 08:00. The single cutoff, 07:30, exercises both rules: the live hour's star is available, while the backfill hour's star is not.

## Input lines

| hour / line | event | repo | event time | intent |
|---|---|---|---|---|
| 00 / 1 | 32001, WatchEvent started | 501 | 00:20 | included using its manifest time |
| 01 / 1 | 32002, WatchEvent started | 502 | 01:20 | excluded using the hour-01 backfill time of 08:00 |

## Expected outputs, derived

Both lines are canonical and distinct (r1 canonical = 2; r3 = 2/0/0), one WatchEvent per hour, and one star each for repos 501 and 502 on 2026-09-01. Both files are `present`; all flags are zero. At cutoff 07:30, repo 501's live line is available and within the R5 event-time window; repo 502's backfill line is not available. Thus R5 contains only repo 501 = 1.
