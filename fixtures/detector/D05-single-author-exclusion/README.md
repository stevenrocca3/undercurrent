# D05: single-author exclusion

## Input lines

| Event | Intent |
|---|---|
| D0501 PushEvent by actor 51 on repo 801 | Repo 801 has exactly one non-bot actor in the 30d window and is excluded from `C(t)`. |
| D0502 PushEvent by actor 52 on repo 802 | Establishes a second repo candidate actor and one contributor. |
| D0503 started WatchEvent by actor 53 on repo 802 | This actor only stars the repo; the second actor restores repo 802 to `C(t)`. |

All events are eight days before `t`, in the 30d window and outside 7d.

## Expected outputs, derived

G38's provisional row scope omits repo 801. Repo 802 has one stargazer and one contributor, both outside 7d, so both acceleration ratios are `0.0`; the feature new-contributor count is one. There is no future contribution, so its label is zero.
