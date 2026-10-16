# D02: label-window edges, newness and label availability

At `t = 2026-06-01T00:00:00Z`, the label freezes at `t_L = 2026-07-01T07:00:00Z`. The requested span begins one hour before `t−90d` to hold the intentionally old actor's history.

## Input lines

| Source hour / event | Intent |
|---|---|
| Mar 2 hour 23, D0201 | Actor 11 pushes one second before `t−90d`; this does not make the later actor an existing contributor in `[t−90d,t)`. |
| May 17 hour 00, D0202 | Actor 12 contributes inside `[t−90d,t)` and in the 30d feature window. |
| May 24 hour 00, D0203 | Actor 13 stars; supplies a second non-bot actor and makes repo 702 a candidate. |
| June 1 hour 00, D0204 | Actor 11 contributes exactly at `t`; included in the label and is new. |
| June 2 hour 00, D0205 | Actor 12 contributes in the label window but is not new because of D0202. |
| June 21 hour 00, D0207 | Actor 15's event is in the label window, but its manifest availability is one hour after `t_L`; excluded. |
| July 1 hour 00, D0206 | Actor 14 contributes exactly at `t+30d`; excluded by the half-open label window, despite availability exactly at `t_L`. |

## Expected outputs, derived

Repo 702 has two non-bot actors before `t`, so it remains a candidate. Its only feature-window contributor is actor 12 (outside 7d); its one star is also outside 7d. Therefore both acceleration ratios are zero, both 7d counts are zero, and `new_contributors_30d = 1`. In the frozen label window, only actor 11 is new: `n_new = 1`, below the floor of 3, so `y = 0`.
