# F28: manifest overrides backfill in both directions

Two one-line star files use observed availability values on opposite sides of their backfill times. `available_at.csv` lists hour 00 as `2026-09-01T06:59:58.5Z` (earlier than 07:00 backfill) and hour 01 as `2026-09-01T09:00:00.123456Z` (later than 08:00 backfill). The cutoffs are 06:59:59, between hour 00's manifest value and backfill, and 08:30, between hour 01's backfill and manifest value. The microsecond-precision value is accepted as observed.

## Input lines

| hour / line | event | repo | event time | intent |
|---|---|---|---|---|
| 00 / 1 | 28001, WatchEvent started | 501 | 00:10 | included in R5 at both cutoffs due to the earlier manifest value |
| 01 / 1 | 28002, WatchEvent started | 502 | 01:10 | excluded at 08:30 because the later manifest value is after the cutoff |

## Expected outputs, derived

Both records are canonical and distinct, giving r1 canonical = 2, r3 = 2/0/0, and one WatchEvent in each source hour. Each repo has one star on 2026-09-01 in r4. At 06:59:59, only hour 00 is available and its event time is before the cutoff, so r5 has repo 501 = 1. At 08:30, hour 01's manifest time is still in the future, so only repo 501 remains in r5. Both requested files decode completely, so both registry rows are `present`; all flags are zero.
