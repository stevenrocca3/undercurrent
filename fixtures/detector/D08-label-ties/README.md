# D08: tied labels exceed K₁

## Input lines

| Source hour / line group | Intent |
|---|---|
| May 24 hour 00, D0801-D0804 | Two distinct non-bot stargazers on each of repos 805 and 806; establishes two candidates without a prior contribution. |
| June 2 hour 00, D08-A-1..3 and D08-B-1..3 | Three distinct PushEvent contributors arrive for each repo in the label window. |

All events are available by `t_L`. Since each repo has two pre-cutoff non-bot actors, neither is excluded as single-author. Historical stars do not count as contributions, so all six future actors are new.

## Expected outputs, derived

There are two candidates, so `K₁ = ceil(0.01 × 2) = 1`. Both have `N_new = 3`; therefore `θ = 3`, both tie at θ and both are positive. The two expected feature rows each have two 30d stars, zero 7d stars, zero contributors, and zero other event counts; `star_accel = 0.0`, while the contributor and close ratios are null.
