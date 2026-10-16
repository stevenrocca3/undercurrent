# D09: label floor

## Input lines

| Source hour / line group | Intent |
|---|---|
| May 24 hour 00, D0901-D0904 | Two pre-cutoff non-bot stargazers on each of repos 807 and 808; establishes two eligible candidates without prior contributions. |
| June 2 hour 00, D09-A-1..2 | Two new PushEvent contributors to repo 807. |
| June 2 hour 00, D09-B-1 | One new PushEvent contributor to repo 808. |

All future events are available by `t_L`, and all three actors are new to their repo.

## Expected outputs, derived

With two candidates, `K₁ = 1`; the top repo has `N_new = 2`, so `θ = 2 < 3`. The label condition is `N_new ≥ max(2,3) = 3`; neither candidate is positive. The two feature rows have two 30d stars each, no 7d stars or feature-window contributions, and zero other event counts.
