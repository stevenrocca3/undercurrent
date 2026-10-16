# Detector fixtures D01-D09

These fixtures hand-check the detector features and labels in `03-signals-and-backtest.md` Draft v0.4 §2-§6 and §8. They use one cutoff, `2026-06-01T00:00:00Z`, with the full 90-day history and 30-day label horizon. Event hours are listed in each fixture's `available_at.csv`, so results do not depend on the historical-lag constant. No detector implementation computes these expected outputs.

The files under `expected/` are only `features.csv` and `labels.csv`; scores, evaluation metrics and leaderboard output are out of scope. The feature row scope and numeric/null cell formats are provisional OPEN gaps G37-G38 in `../SPEC-GAPS.md`. A row with two adjacent commas in a ratio column denotes a null.

| Fixture | Coverage |
|---|---|
| D01-window-edges-point-in-time | Feature windows include `t−7d` and `t−30d`, exclude `t`; unavailable pre-cutoff event excluded |
| D02-label-windows-newness | Label includes `t`, excludes `t+30d`; old actor is new, recent actor is not, late-available event is excluded |
| D03-contribution-actions | S3's four contribution event/action pairs and three non-contributing cases |
| D04-bot-filters | `[bot]` login, rate bot, strict rate near-misses; bots excluded from contributor and stargazer counts |
| D05-single-author-exclusion | Single-author repo omitted; a second actor who only stars restores candidate |
| D06-distinct-stargazers-no-survivorship | Repeated stars count one actor; silent candidate stays with zero label |
| D07-star-burst | Exactly-threshold burst hour, 49-event near miss, shared and burst-only stargazers |
| D08-label-ties | Tie at θ makes positives exceed K₁ |
| D09-label-floor | θ below 3; floor leaves all candidates negative |

Inputs are literal JSON lines (with small deterministic loops only for the rate-bot and burst volumes) in `../generate_inputs.py`. Expected CSVs are hand-derived and explained in each fixture README.
