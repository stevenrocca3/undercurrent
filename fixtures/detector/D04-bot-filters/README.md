# D04: bot filters

The one-hour input contains eight explicit target-repo events and three generated filler groups (all dated May 24, within both relevant windows). Every hour with events is listed in the manifest.

## Input lines

| Group | Intent |
|---|---|
| D04-A target events plus 999 filler PushEvents | Actor 41 (`normal-a`) touches exactly 100 repos and makes 1,001 events. The repo threshold is not exceeded, so this actor is not a rate bot. |
| D04-B target events plus 998 filler PushEvents | Actor 42 (`normal-b`) touches 101 repos and makes exactly 1,000 events. The event threshold is not exceeded, so this actor is not a rate bot. |
| D04-C target events plus 999 filler PushEvents | Actor 43 (`rate-runner`) touches 101 repos and makes 1,001 events; both strict thresholds are exceeded, so it is a rate bot. |
| D04-D target events | Actor 44 (`release[bot]`) is a login-suffix bot. |

The eight target events give each actor one PushEvent and one started WatchEvent on repo 9000. Each filler group uses its own private repos: A has 99 fillers with 11 events in the first 9 and 10 in the other 90; B has 100 fillers with 10 in the first 98 and 9 in the last 2; C has 100 fillers with 10 in the first 99 and 9 in the last. The filler repos of non-bots are excluded as single-author; the rate-bot-only filler repos are not candidates.

## Expected outputs, derived

On repo 9000, only actors 41 and 42 survive bot filtering. They yield two distinct stargazers, two contributors, two new feature contributors and two pushes; all are outside 7d, so both acceleration ratios are `0.0`. The two bots' stars and pushes do not count. The repo has no future contributions (`n_new = 0`, `y = 0`). All other ratio denominators are zero.
