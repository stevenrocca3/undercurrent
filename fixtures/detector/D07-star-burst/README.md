# D07: burst threshold, near miss and shared stargazer

All three event hours are listed in the manifest and are in the 30d window. The 50 events on May 22 are exactly half of the 100 non-bot star events in the window.

## Input lines

| Source hour / line group | Intent |
|---|---|
| May 22 hour 00, D07-B-01..49 | 49 burst-hour stars by actor 71. |
| May 22 hour 00, D07-B-50 | The 50th event in that hour, by actor 72, who stars nowhere else in the window. |
| May 24 hour 00, D07-N-01..20 | 20 non-burst-hour events by actor 71; this actor also starred in the burst hour. |
| May 24 hour 00, D07-N-21..49 | 29 events by actors 92..120; this is a 49-event hour, below the 50-event minimum. |
| May 12 hour 00, D0704 | A second non-burst event by actor 92, already represented in D07-N-21. |

The May 22 hour has 50 of 100 events (exactly 50%) and is a burst. The May 24 hour has only 49 events and is not one. Of the 30 distinct non-burst stargazers, actor 71 also starred in the burst hour; actor 72 is the sole burst-only stargazer. The extra May 12 event repeats actor 92.

## Expected outputs, derived

Burst-only actor 72 is excluded from cleaned stars and counted once in `burst_stargazers_30d`; the other 30 distinct actors remain, so `stars_30d = 30`. All stars are older than 7d, so `stars_7d = 0` and `star_accel = 0.0`. No contributions occur; repo 804 remains a candidate and has label zero.
