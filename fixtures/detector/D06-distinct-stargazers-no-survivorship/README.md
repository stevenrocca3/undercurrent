# D06: distinct stargazers and no survivorship bias

## Input lines

| Event | Intent |
|---|---|
| D0601-D0603 started WatchEvents by actor 61 on repo 803 | Three gross star events by one actor; count that actor once. |
| D0604 started WatchEvent by actor 62 on repo 803 | A second non-bot actor prevents single-author exclusion. |

All events occur eight days before `t`; the repo has no input after the cutoff.

## Expected outputs, derived

Repo 803 remains in `C(t)` despite being silent after `t`. Its four gross events represent two distinct stargazers; none are in 7d, so `stars_7d = 0`, `stars_30d = 2`, and `star_accel = 0.0`. It has no contributors or new label contributors, giving `n_new = 0`, `y = 0`; all other count features are zero and their zero-denominator ratios null.
