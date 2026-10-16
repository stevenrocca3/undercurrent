# Brief: verifier: detector fixtures (03 §8)

**From:** Steven (owner). Drafted 2026-10-16 by the scrum master from the specs only.
**For:** the verifier (Copilot, in `~/undercurrent-verifier`, on a `verifier-*` branch). Per 01 §7, the verifier writes fixtures and never pipeline or reference code.
**Spec:** `03-signals-and-backtest.md` **Draft v0.4** (§2–§6 and §8), with `01-event-semantics.md` v0.13 (§4 point-in-time rule, §6 CSV rules) and `02-live-ingestion.md` v0.8 (§8 manifest format). 03 isn't approved yet, so these fixtures are also its first test: every place where 03 is silent or ambiguous is a finding, not a guess.

## Where they go

- `fixtures/detector/D01-*`, `D02-*`, …: a new folder with its own numbering.
  - The 01 fixture runners only pick up folders that hold a `fixture.json` directly in `fixtures/`, so these won't run as R1–R7 fixtures.
  - Add a `fixtures/detector/README.md` index, in the same style as `fixtures/README.md`.
- Each fixture has `input/`, `fixture.json`, `available_at.csv`, `README.md` and `expected/`.
- **`fixture.json`:** `{"id", "title", "first_hour", "last_hour", "cutoffs": [...]}`.
  - `first_hour`..`last_hour` is the requested range; `input/` holds only the hours that have events.
  - 03's constants are fixed (`H` = 90 d, horizon 30 d, the 7 d and 30 d windows), so a fixture's range has to span them. Don't scale them down.
- **`available_at.csv`:** list **every hour that has events** (02 §8 format). Then no expected output depends on `L`, which Gate 2 is about to change.
- **`expected/`:** `features.csv` and `labels.csv` only, with the columns of 03 §8 under the 01 §6 CSV rules. `scores.csv`, `eval.csv` and `leaderboard.csv` are out of scope.
- Build inputs in `generate_inputs.py` as before: literal events, and small loops where a case needs volume (the bot-by-rate case).

## Cases (at least one fixture each)

1. **Window edges, features:** events at exactly `t − 7d`, `t − 30d` (included) and `t` (excluded) (03 §2, 01 §4).
2. **Window edges, labels:** events at exactly `t` (included) and `t + 30d` (excluded). Plus an event inside the label window whose `available_at` is after `t_L`: it doesn't count (03 §3.2).
3. **Newness (`H`):** one actor who contributed only before `t − H` counts as new. One who contributed inside `[t − H, t)` doesn't (03 §3.1).
4. **What counts as contributing (S3):**
   - Counts: `PushEvent`, `PullRequestEvent opened`, `IssuesEvent closed`, `PullRequestReviewEvent created`.
   - Doesn't count: `IssueCommentEvent`, `PullRequestEvent closed`, `IssuesEvent opened`.
5. **Bots (S7):**
   - one actor whose login ends in `[bot]`
   - one bot by rate: more than 100 repos **and** more than 1,000 events in 30 d
   - one actor just under each rate threshold, who isn't a bot
   - Show a bot removed from both a contributor count and a stargazer count.
6. **Single-author repo (S8):** a repo with one non-bot actor in `[t − 30d, t)` is excluded from `C(t)`, so it has no row in either file. A second actor who only starred it brings it back in.
7. **Distinct stargazers (S13):** one actor starring a repo several times in a window counts once.
8. **Star burst (S9):**
   - one burst hour (≥ 50 star events, ≥ 50% of the repo's 30 d stars)
   - a near-miss hour at 49 stars, which isn't a burst
   - a stargazer who also starred outside the burst hour, who stays in `stars_30d`
9. **Label ties and the floor (S6):**
   - a cutoff where several repos tie at `θ`: all positive, so there are more than `K₁` positives
   - a cutoff where `θ < 3`, so the floor decides and no repo below 3 is positive
10. **Point-in-time trap:** an event with `event_time < t` but `available_at > t` inside a feature window, excluded at `t`.
11. **No survivorship:** a repo active before `t` and silent after it stays in `C(t)`, with `n_new = 0` and `y = 0`.

Ratio features with a zero denominator are empty (null) in the CSV. If 03 or 01 §6 doesn't say how a null is written, that's a finding.

## Rules

- **Expected outputs are hand-derived** from the spec, with the reasoning in each README. Never generate them by running code.
- **Independence:** as before. Don't read `pipeline/`, `reference/` or `changes/*-reference-*.md`.
- **Where 03 is silent:** add a `G` entry (next free number, currently G37) to `fixtures/SPEC-GAPS.md`, marked OPEN, with your provisional choice. List each one in your report.
- Neither implementation computes 03 outputs yet, so there's nothing to run them against. `./check.sh` must still pass, which proves the new folder doesn't disturb the 01 fixtures.

## Done when

- The fixtures, READMEs and the index are committed on your `verifier-*` branch, and a PR is open.
- A report of 10 lines or fewer, through Steven: the D numbers, the cases each covers, the `./check.sh` result, and the new G entries. Stop there for review.
