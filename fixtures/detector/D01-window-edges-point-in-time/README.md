# D01: feature-window edges and point-in-time exclusion

The cutoff is `t = 2026-06-01T00:00:00Z`; requested hours span `t−90d` through `t+30d`. The manifest includes every event hour. The event at `t` is deliberately marked available at `t`, isolating the exclusive `event_time < t` rule. The May 31 event is available after `t`, isolating the `available_at ≤ t` rule.

## Input lines

| Source hour / event | Intent |
|---|---|
| May 2 hour 00, D0101/D0102 ForkEvent | Two actors at exactly `t−30d`; both contribute one fork, establish the candidate, and prevent single-author exclusion. |
| May 25 hour 00, D0103 ReleaseEvent published | Exactly `t−7d`; included in both 7d and 30d release counts. |
| May 31 hour 00, D0105 PushEvent | `event_time < t`, but manifest availability is `t+1h`; excluded from all features and candidate actor count. |
| June 1 hour 00, D0104 PushEvent | Exactly `t` and available at `t`; excluded by the exclusive event-time bound. |

## Expected outputs, derived

Repo 701 is in `C(t)` from the two events at the inclusive 30d boundary. Only the two fork actors and the release actor are visible; there are no stars or contribution events. Thus all ratio denominators are zero, counts are zero except `releases_30d = 1` and `forks_30d = 2`. The label window has no events, so `n_new = 0`, `y = 0`.
