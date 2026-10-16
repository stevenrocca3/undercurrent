# D03: contribution event/action semantics

All seven events occur in the 30d feature window but outside 7d. Each has a different actor, so the four qualifying cases must yield four contributors, not seven.

## Input lines

| Event | Intent |
|---|---|
| D0301 PushEvent | Counts as a contribution. |
| D0302 PullRequestEvent `opened` | Counts. |
| D0303 IssuesEvent `closed` | Counts. |
| D0304 PullRequestReviewEvent `created` | Counts. |
| D0305 IssueCommentEvent `created` | Does not count. |
| D0306 PullRequestEvent `closed` | Does not count. |
| D0307 IssuesEvent `opened` | Does not count. |

## Expected outputs, derived

All seven actors make the repo non-single-author. The four qualifying events give `contributors_30d = new_contributors_30d = 4`; none fall in 7d, so `contributors_7d = 0` and `contributor_accel = 0.0`. Event-action counts are one each for pushes, PR opened/closed and issues opened/closed; both close ratios are `1.0`. There are no stars, releases or forks. No future contribution gives `n_new = 0`, `y = 0`.
