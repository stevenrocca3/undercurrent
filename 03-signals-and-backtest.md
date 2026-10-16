# 03 — Signals, Target and Backtest

**Status:** Draft v0.2 · 2026-10-16 (not approved). v0.1 drafted by the pipeline agent; v0.2 review edits by the scrum master.
**Owner:** Steven (approves all changes)
**Depends on:** `01-event-semantics.md` v0.13 (canonical events, point-in-time rule) and `02-live-ingestion.md` v0.8 (`available_at`, `L`). Everything in 01 and 02 still holds. This document defines what is computed **from** canonical events: the prediction target, the signals, the noise filters, and how the signals are judged against history.

> Agents: same rules as 01. Once approved, this document is authoritative. Decisions are recorded in §9 (S1–S13); while the status is Draft, every S row is provisional. Changes go through 01 §10 change control.

---

## 1. Purpose and scope

**Question.** As of a cutoff `t`, which public repositories will gain the most **new active contributors** over the next 30 days?

**User (V1).** Steven as the internal analyst; early technical investors second. The output is a ranked, explainable leaderboard: each row shows the signal values behind its rank. There is **no 0–100 "score"**: one can't be calibrated without labelled ground truth (S1).

**Source (V1).** GH Archive only, through the 01 canonical tables. No GitHub API calls, no other sources (S2).

**What canon-v1 can and can't see.** Every signal here is built from these canon-v1 fields: `event_type`, `payload_action`, `actor_id`, `actor_login`, `repo_id`, `event_time`, `available_at`. `payload_raw` is null in Gate 1 runs (01 §2, G32), so V1 can't use anything that lives deeper in the payload:

| Wanted | Needs | V1 |
|---|---|---|
| commits per push | `payload.size` | no; count `PushEvent`s instead |
| PR merged vs closed unmerged | `payload.pull_request.merged` | no; count closes only |
| issue response or close time | `payload.issue.number`, to pair an open with its close | no |
| stargazer account age, followers | GitHub API | no (S2) |

Each of these needs its own decision record: storing selected payload fields changes G32, and anything else changes S2.

## 2. Terms

- **Cutoff `t`.** The instant a prediction is made. Features obey the 01 §4 point-in-time rule at `t`: `available_at ≤ t` and `event_time < t`.
- **Window `[a, b)`.** Records with `a ≤ event_time < b`.
- **Contribution event.** A canonical event that shows someone doing work on a repo (S3):
  - `PushEvent` (any action),
  - `PullRequestEvent` with `payload_action = 'opened'`,
  - `IssuesEvent` with `payload_action = 'closed'`,
  - `PullRequestReviewEvent` with `payload_action = 'created'`.
  - `IssueCommentEvent` does **not** count: a comment is cheap and easy to spam (S3).
- **Contributor of `r` in `W`.** A non-bot actor (§4.1) with at least one contribution event to `r` in window `W`, counted by distinct `actor_id`.
- **Star event.** `WatchEvent` with `payload_action = 'started'`: a gross event, never net (01 §1).
- **Stargazers of `r` in `W`.** Distinct non-bot `actor_id`s with a star event to `r` in `W`. This is the "unique stargazers" aggregation 01 §3 leaves to this document. One actor starring twice counts once (S13).
- **History horizon `H`.** How far back "new" looks: 90 days (S4).
- **Horizon.** 30 days (S5).

## 3. Target

### 3.1 Definition

For repo `r` and cutoff `t`:

- `N_new(r, t)` = number of distinct non-bot actors who are contributors of `r` in `[t, t + 30d)` and were **not** contributors of `r` in `[t − H, t)`.
- **Candidate set `C(t)`.** Repos with at least one non-bot event of any type in `[t − 30d, t)` under the point-in-time rule, minus the exclusions of §4. Repos first seen after `t` can't be ranked at `t`, so they aren't candidates.
- **Label.** Sort `C(t)` by `N_new` descending, then `repo_id` ascending. Let `K₁ = ⌈0.01 · |C(t)|⌉` and `θ = N_new` of the `K₁`-th repo. Then `y(r, t) = 1` iff `N_new(r, t) ≥ max(θ, 3)` (S6). Repos tied at `θ` are all positive, so the positive count can exceed `K₁`.

The floor of 3 stops the top 1% from being decided by single new contributors when activity is low.

**Measured (proxy, September 2026; `BENCHMARKS.md`).** No cutoff with a full `H` and horizon fits in the one processed month, so this used a half-month split: candidates are repos with ≥ 2 non-bot actors in Sep 1–15, and `N_new` is counted over Sep 16–30.
- There are 188,960 candidates; 148,664 have `N_new = 0`, 4,776 have ≥ 3, and the maximum is 180.
- The top-1% `θ` is **4**, so the floor doesn't bind. Without the single-author exclusion, the p99 of a whole month's contributors over all 6.95M active repos is 2, and the floor would bind.
- **Re-measure `θ` at the first real cutoff** (§7.1), before the first test cutoff is scored (§6.5).

### 3.2 When a label is known

A label uses future data, so it gets its own freeze time `t_L = t + 30d + 1h + L` (with `L = 6h` today, `t + 30d + 7h`).

- `N_new` uses records with `available_at ≤ t_L`.
- The "not a contributor before `t`" check uses every record in `[t − H, t)` with `available_at ≤ t_L`. That is part of the label, not a feature.

If `L` changes (01 §4, 02 §7), every label and evaluation computed under the old `L` is invalid and is recomputed.

## 4. Noise filters and exclusions

Filters run as of `t` and use only data that obeys the point-in-time rule. They are fixed rules, not learned, so they can't leak.

### 4.1 Bots (S7)

An actor is a bot at `t` if either is true:

1. `actor_login` ends with `[bot]` (case-sensitive) on any of its events in `[t − H, t)`. This is a classification, not a join; `actor_login` is still never joined on (01 §2).
2. In `[t − 30d, t)` the actor made events to more than 100 distinct repos **and** more than 1,000 events in total.

Bots are removed from every contributor count and every star count, in features and in labels. For labels, the bot rule is evaluated with data as of `t_L`. Rule 1 looks at `[t − H, t + 30d)`, and rule 2 counts the label window `[t, t + 30d)`.

### 4.2 Single-author repos (S8)

A repo is single-author at `t` if it had exactly one distinct non-bot actor across **all** event types (stars included) in `[t − 30d, t)`. Single-author repos are excluded from `C(t)`.

**Known cost.** A solo project that is about to take off looks exactly like this. So every evaluation also reports how many positives the filter would have removed: compute `y` with the filter switched off and count those repos.

### 4.3 Star bursts (S9)

A repo's hour `h` is a **burst** if, within `[t − 30d, t)`:

- that hour has at least 50 non-bot star events, **and**
- the hour holds at least 50% of the repo's non-bot star events in the window.

Stargazers whose only star events in the window fall in burst hours are left out of the cleaned star features (§5), and counted separately as `burst_stargazers_30d`. The repo itself stays in `C(t)`. Without account age (S2), a burst can't be told apart from a real launch; this filter only stops one hour from driving the star signals.

## 5. Signals (features)

Every feature is computed as of `t` under the point-in-time rule, per `repo_id`, after the bot filter. A window `[t − d, t)` includes `t − d` (01 §4). "7d" and "30d" mean `[t − 7d, t)` and `[t − 30d, t)`. A ratio is null when its denominator is 0.

| Feature | Definition |
|---|---|
| `stars_7d`, `stars_30d` | stargazers (§2), burst-only stargazers excluded (§4.3) |
| `star_accel` | `stars_7d / (stars_30d · 7/30)` |
| `burst_stargazers_30d` | stargazers whose only star events in 30d are in burst hours (§4.3) |
| `contributors_7d`, `contributors_30d` | distinct contributors |
| `new_contributors_30d` | contributors in 30d who were not contributors in `[t − H, t − 30d)` |
| `contributor_accel` | `contributors_7d / (contributors_30d · 7/30)` |
| `pushes_30d` | `PushEvent` count |
| `prs_opened_30d`, `prs_closed_30d` | `PullRequestEvent` with action `opened` / `closed` |
| `pr_close_ratio` | `prs_closed_30d / prs_opened_30d` |
| `issues_opened_30d`, `issues_closed_30d` | `IssuesEvent` with action `opened` / `closed` |
| `issue_close_ratio` | `issues_closed_30d / issues_opened_30d` |
| `releases_30d` | `ReleaseEvent` with action `published` |
| `forks_30d` | `ForkEvent` count |

`first_seen_days` (repo age) was dropped in v0.2. With history starting at the backfill's first day, most repos would be censored, so it carried almost no information. Revisit it in V2 with a longer history.

`new_contributors_30d` is the feature version of the target, one window back. It is the obvious persistence baseline and is reported as one (§7.2).

## 6. Point-in-time and leakage rules

1. **Features** obey 01 §4 at `t`. That rule is already covered by fixture F12; §8 adds fixtures for the windows defined here.
2. **Labels** use only `[t, t + 30d)` and the newness check of §3.2, frozen at `t_L`.
3. **No future in the candidate set.** `C(t)` and every filter use data as of `t`. A repo that is deleted, renamed or goes quiet after `t` stays in `C(t)` (no survivorship bias). Identity is `repo_id` (01 §1).
4. **Training embargo.** A model scored at test cutoff `t*` may be trained only on cutoffs `t` with `t_L(t) ≤ t*`. Every fitted value (scalers, percentile thresholds, model weights) is fitted on those cutoffs only.
5. **No tuning on the test set.** Thresholds in §4 and §9 are fixed before the first test cutoff is scored. Changing one after looking at test results needs a decision record, and the evaluation is rerun on later cutoffs only.
6. **Fixed `L`.** Every number in one evaluation uses one value of `L`.

## 7. Backtest design

### 7.1 Data needed

One cutoff needs data from `t − H` (newness) to `t_L` (label), so 90 + 30 days plus 7 h. Gate 1 processed one month (September 2026), which is **not enough for a single cutoff**. V1 needs a backfill (S10):

- **Proposed:** 2026-03-01 → 2026-10-01 (7 months), processed by the pipeline in batch mode with the 01 §4 historical `available_at` rule. The first cutoff with a full `H` is 2026-05-30, and the last with a label frozen by 2026-10-01 is 2026-08-31 17:00Z. The weekly Monday cutoffs are 2026-06-01 → 2026-08-31.
- **Disk: the activity table is the plan.** Canonical tables run about 4.3 GB per month (BENCHMARKS). Seven months would be about 30 GB, against 27 GB free on 2026-10-16, and the live copy is growing.
  - Each month is reduced to an **activity table** with one row per `(source_file_hour, available_at, repo_id, actor_id, event_type, payload_action)`, plus a `n_events` count. Then that month's `canon.duckdb` is dropped.
  - It keeps the hour and `available_at`, so the point-in-time rule still applies exactly, and actor identity, so distinct counts still work.
  - Two side tables carry the rest: per actor, whether a login ends in `[bot]` (§4.1); per repo, the latest `repo_name` with its `available_at` (§8).
  - It is a deterministic function of the canonical tables, so it falls under S12 too.
- **Timing against Gate 2.** The backfill's `available_at` uses `L`. Gate 2 (02 §7, §9) is expected to change `L` after 2026-10-31, and that invalidates every label and evaluation (§3.2, §6.6). So code, fixtures and the activity-table tooling are built now, but **the backfill and every backtest run only after the new `L` is approved**.

### 7.2 Protocol

- **Cutoffs.** Weekly, Monday 00:00Z, over the range above (14 cutoffs for the proposed backfill). Successive label windows overlap, so cutoffs are not independent. Headline numbers are means over cutoffs, reported with the per-cutoff minimum and maximum.
- **Walk-forward.** Cutoffs are scored in time order under the §6.4 embargo. The first 4 scoreable cutoffs train only and are never reported as test results.
- **Models.**
  - `B0` random order: expected Precision@K = base rate.
  - `B1` star-only: rank by `stars_7d` (stargazers).
  - `B2` star-only: rank by `stars_30d` (stargazers).
  - `B3` persistence: rank by `new_contributors_30d`.
  - `M1` contributor heuristic: rank by `contributor_accel · contributors_7d`.
  - `M2` logistic regression on all §5 features (`log1p` on counts, null → 0 plus a missing indicator), trained walk-forward.
- **Ties** in any ranking break by `repo_id` ascending, so results are reproducible.

### 7.3 Success metrics

Per test cutoff, over `C(t)`:

- **Precision@K** for K = 25, 100, 500.
- **Recall@K** for the same K.
- **AUROC.**
- **Average precision (PR-AUC).** With a base rate near 1%, AUROC alone flatters every model; PR-AUC is the honest one.
- **Base rate** `|y = 1| / |C(t)|`, and the §4.2 filter-loss count.

**V1 passes (pre-registered, S11)** if, on the test cutoffs, `M1` or `M2` beats **`B*`**, the stronger of `B1` (stars) and `B3` (persistence) by mean Precision@100:

1. mean Precision@100 at least **1.5× `B*`**'s, and
2. higher Precision@100 than `B*` on **at least 75%** of test cutoffs, and
3. mean AUROC above `B*`'s.

Beating stars alone isn't enough. A model that loses to persistence is only finding repos that are "already growing", not making a forecast.

## 8. Outputs and fixtures

Output CSVs follow 01 §6's CSV rules (RFC 4180, LF line endings, sorted by key):

| File | Columns |
|---|---|
| `features.csv` | `cutoff,repo_id,` + the §5 features in table order |
| `labels.csv` | `cutoff,repo_id,n_new,y` |
| `scores.csv` | `cutoff,model,repo_id,rank` |
| `eval.csv` | `cutoff,model,metric,value` |
| `leaderboard.csv` | `cutoff,rank,repo_id,repo_name,` + the §5 features (`repo_name` is the latest non-null name as of `t`, display only) |

`features.csv` and `labels.csv` are deterministic functions of the canonical tables. Like R1–R7, they can be produced by two independent implementations and compared byte for byte (S12). The fixtures to add are:

- the window edges for features and labels,
- an actor who is a contributor before `t − H` (counts as new) and one inside `[t − H, t)` (doesn't),
- a bot by login and a bot by rate,
- a single-author repo,
- a burst hour,
- a tie at `θ`, and a cutoff where `θ < 3`,
- an event with `event_time < t` but `available_at > t`, in a feature window.

## 9. Decisions

All provisional until Steven approves v1.0.

| ID | Question | Provisional resolution |
|---|---|---|
| S1 | output form | ranked leaderboard with signal values; no calibrated score in V1 |
| S2 | sources | GH Archive only; no GitHub API |
| S3 | what counts as contributing | `PushEvent`; `PullRequestEvent` `opened`; `IssuesEvent` `closed`; `PullRequestReviewEvent` `created`. Not `IssueCommentEvent`. **Agreed by Steven 2026-10-16** |
| S4 | newness horizon `H` | 90 days |
| S5 | target horizon | 30 days (90 days in V2) |
| S6 | positive label | top 1% of `C(t)` by `N_new`, ties included, floor `N_new ≥ 3`. Proxy `θ` = 4 (§3.1); re-measure at the first real cutoff |
| S7 | bots | `[bot]` login suffix, or > 100 repos and > 1,000 events in 30 d |
| S8 | single-author repos | excluded from `C(t)`; the filter's loss of positives reported every run |
| S9 | star bursts | hour with ≥ 50 stars and ≥ 50% of the repo's 30 d stars; its stars removed from star features only |
| S10 | backfill | 2026-03-01 → 2026-10-01, batch mode, historical `available_at`, reduced to the activity table month by month; run only after Gate 2's `L` is approved (§7.1) |
| S11 | V1 pass bar | §7.3: against `B*` = the stronger of `B1` and `B3`: Precision@100 ≥ 1.5× `B*`, wins on ≥ 75% of cutoffs, AUROC > `B*`. **Agreed by Steven 2026-10-16** |
| S12 | independent implementations for `features.csv` and `labels.csv` | yes, as in 01 §6 |
| S13 | star counting | distinct non-bot stargazers per window, not gross star events |
