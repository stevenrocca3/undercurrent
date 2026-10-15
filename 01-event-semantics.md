# 01 — Canonical Event Semantics and Verification Contract

**Status:** Draft v0.1 · 2026-10-14
**Owner:** Steven (approves all changes)
**Applies to:** every pipeline component, verifier, and evidence artifact

> Agents: this document is authoritative. If code and this document disagree, the code is wrong — or open a change proposal. Agents may propose edits; only the owner merges them. Items marked **OPEN** must be resolved before Gate 1.

---

## 1. Scope and source limitations

**Source.** GH Archive hourly files: `https://data.gharchive.org/YYYY-MM-DD-H.json.gz` (hour not zero-padded, UTC). One JSON object per line, each a public GitHub event.

**In scope.** Events from 2015-01-01 onward (modern Events API schema).
**Gate 1 scope.** One calendar month. **OPEN-1:** which month (suggest a recent complete month).
**Out of scope.** Pre-2015 timeline data (different schema, no stable event IDs). Bringing it in requires a new decision record.

**Known limitations — completeness is never asserted:**

- Public events only; private-repo activity is absent.
- The public Events feed does not guarantee every event is captured. GH Archive has outage windows, missing hours, and occasionally truncated files.
- A "star" is a `WatchEvent` with `payload.action = "started"`. Unstarring emits no event. **All star metrics are gross star events, not net stars.**
- An event's `created_at` can fall outside the hour of the file that contains it.
- Repo and actor names change over time; numeric IDs are the stable keys.
- Bots are not identified or filtered in this document.

**Missing-hour registry.** Every expected hour in scope gets exactly one status: `present`, `missing`, `truncated`, or `unreadable`, with the evidence (HTTP status, byte count, decompression error).

---

## 2. Canonical event schema (`canon-v1`)

| Field | Type | Null | Source | Normalization | Use |
|---|---|---|---|---|---|
| `event_id` | string | no | `id` | kept as string, no trimming or casting | identity |
| `event_type` | string | no | `type` | as-is; unrecognized types kept and flagged | filtering |
| `actor_id` | int64 | no | `actor.id` | — | joins, distinct-actor metrics |
| `actor_login` | string | yes | `actor.login` | raw | display only, never joined on |
| `repo_id` | int64 | no | `repo.id` | — | joins, aggregation |
| `repo_name` | string | no | `repo.name` | raw `owner/name` | display only, never joined on |
| `org_id` | int64 | yes | `org.id` | — | optional grouping |
| `is_public` | bool | no | `public` | — | filtering |
| `payload_action` | string | yes | `payload.action` | as-is | e.g. star detection |
| `payload_raw` | json | no | `payload` | stored uninterpreted | downstream models |
| `event_time` | timestamp(µs, UTC) | no | `created_at` | ISO-8601 → UTC | when GitHub says it happened |
| `source_file_hour` | timestamp(UTC) | no | file name | start of hour | GH Archive bucket |
| `source_line` | int32 | no | line number, 1-based | — | tie-breaking, provenance |
| `available_at` | timestamp(UTC) | no | see §4 | — | point-in-time cutoffs |
| `source_last_modified` | timestamp(UTC) | yes | HTTP `Last-Modified` | — | informational only |
| `ingested_at` | timestamp(UTC) | no | pipeline clock | — | operations only |
| `record_hash` | string | no | SHA-256 of the raw line bytes | — | conflict detection |
| `schema_version` | string | no | pipeline | `"canon-v1"` | migrations |

**Quarantine rules.** A line goes to the quarantine table, with exactly one reason code, if it:

- `Q1` is not valid JSON
- `Q2` is missing `id`, `type`, `repo.id`, `actor.id`, or `created_at`
- `Q3` has a `created_at` that fails to parse
- `Q4` has an ID field of the wrong JSON type

Quarantine schema: `source_file_hour, source_line, reason_code, raw_line`. Quarantined lines are counted, never silently dropped.

---

## 3. Identity and deduplication

- **Event identity is `event_id`.** Nothing else.
- **Duplicate:** the same `event_id` appears more than once, within one file or across files. Keep the occurrence with the smallest `(source_file_hour, source_line)`; count the rest as duplicates.
- **Conflicting duplicate:** the same `event_id` with a different `record_hash`. Keep the first as above and log both to a `conflicts` table. A nonzero conflict count is not a failure, but every conflict must be categorized in the Gate 1 report.
- **No fallback identities in scope.** Records without an `id` are quarantined (`Q2`). Inventing synthetic IDs requires a decision record documenting collision risk.
- **Event deduplication is not business aggregation.** One actor starring the same repo twice produces two distinct events. Metrics such as "unique stargazers" are defined in Document 03 as aggregations — never implemented by deleting events.
- **Never deduplicate on `repo_id` or `actor_id`.**

---

## 4. Time semantics

- All timestamps are UTC with microsecond precision. No local time appears anywhere in storage or computation.
- Hour `h` covers the half-open interval `[h, h + 1h)`.

**Three clocks:**

1. `event_time` — when GitHub says the event happened.
2. `source_file_hour` — which GH Archive bucket the event was in.
3. `available_at` — the earliest time the record could have been known to us.

**`available_at` rules:**

- *Live ingestion:* the time our fetcher first successfully downloaded and validated the file. Observed, not assumed.
- *Historical backfill:* the true publication time was never recorded, and `Last-Modified` can reflect later re-uploads. So `available_at = source_file_hour + 1h + L`, where `L` is a fixed, conservative lag.
  - **OPEN-2:** value of `L`. Proposed: 6h until live ingestion has measured the real delay distribution; then set `L` to the observed p99, rounded up to the next hour. Changing `L` invalidates any detector evaluation run under the old value.
- `source_last_modified` is recorded but never used for cutoffs.

**Point-in-time rule.** A computation "as of cutoff `t`" may use only records with `available_at ≤ t` **and** `event_time < t`. Both conditions are enforced in code and covered by a fixture.

**Flags (records are kept, counts reported):**

- *Late:* `event_time < source_file_hour − 1h`
- *Future-skewed:* `event_time > source_file_hour + 2h`

**Replay.** Replay emits files in `source_file_hour` order with their original `available_at`. On identical input, replay and batch must produce byte-identical canonical tables (compared by content hash after a fixed sort).

---

## 5. Reconciliation contract

Three separate properties. Evidence for one may never be used to satisfy another.

### 5.1 Transformation correctness — hard gate

Given the same input files, pipeline outputs equal the reference calculation's outputs (§6) **exactly**, for every reference metric. Any difference fails the gate.

### 5.2 Source reconciliation — measured, with a tolerance set in advance

Comparison against the public BigQuery GH Archive dataset, which is *derived from the same source* and therefore checks transformation, not coverage.

Metrics:

- event count by `(hour, event_type)`
- distinct `event_id` count by hour
- star-event count by `(repo_id, date)` for the 1,000 repos with the most star events in scope

Every cell outside tolerance gets exactly one category: `missing_hour_ours`, `missing_hour_theirs`, `dedup_policy`, `parse_or_schema`, `time_bucketing`, or `unexplained`.

Pass: all cells within tolerance, or categorized, with **zero** `unexplained` cells outside tolerance.
**OPEN-3:** tolerance. Proposed: ≤ 0.1% relative difference per `(hour, event_type)` cell, set before the first comparison run.

### 5.3 Source completeness — never a gate

Reported, never asserted: the missing-hour registry, known outage windows, and the limitations in §1. No artifact, README, or resume line may claim the dataset is complete.

---

## 6. Reference calculation

**Owner and author: Steven, by hand.** This is the dumbest correct implementation, kept independent of the pipeline.

Constraints:

- One Python file, or SQL run in DuckDB.
- No imports from the pipeline codebase.
- Reads the raw `.json.gz` files directly.
- Roughly 200 lines or fewer. Clarity over speed.

Computes, for a given set of hour files:

| ID | Output |
|---|---|
| R1 | lines parsed; lines quarantined, by reason code |
| R2 | event count by `(source_file_hour, event_type)` after deduplication |
| R3 | distinct `event_id`s, duplicate count, conflict count |
| R4 | star-event count by `(repo_id, UTC date of event_time)` |
| R5 | for a given cutoff `t`: star events per repo with `event_time` in `[t − 7d, t)` and `available_at ≤ t` |

Outputs are CSV files with fixed column order, sorted by all key columns, written to `reference_out/`. The comparison against the pipeline is an exact equality check after sorting — no tolerance, no fuzzy matching. An agent may write the comparison script; Steven reviews it.

**Steven must be able to explain** each output's semantics, run the script, and say what a passing comparison does and does not prove.

---

## 7. Synthetic fixtures

**Owner:** a verifier agent that does not author pipeline code. **Expected outputs are hand-checked by Steven and committed before the pipeline component they test is implemented.**

| ID | Case |
|---|---|
| F1 | clean hour, mixed event types |
| F2 | exact duplicate within one file |
| F3 | exact duplicate across two files |
| F4 | conflicting duplicate (same ID, different content) |
| F5 | malformed JSON line |
| F6 | missing required field |
| F7 | late event |
| F8 | future-skewed event |
| F9 | missing hour inside the requested range |
| F10 | unrecognized event type |
| F11 | repo renamed mid-window (same `repo_id`, new `repo_name`) |
| F12 | point-in-time trap: an event whose `event_time` is before cutoff `t` but whose `available_at` is after it (must be excluded from R5) |
| F13 | unstar-shaped activity: repeated star events from one actor (must count as separate events) |

Negative fixtures for the detector (steady activity that must not trigger) are defined in Document 03.

---

## 8. Gate 1 acceptance criteria

Gate 1 passes only if **all** of the following hold:

1. Every fixture passes in both the pipeline and the reference calculation.
2. Pipeline and reference outputs are exactly equal on R1–R5 for the chosen month.
3. Replay and batch produce byte-identical canonical tables.
4. A source reconciliation report exists with every out-of-tolerance cell categorized and zero `unexplained` cells.
5. A missing-hour registry exists for the full month.
6. An evidence file `evidence/gate1.json` exists containing: commit SHA, config hash, input manifest (file names and SHA-256), every check result, and overall pass/fail. **It is generated by CI only.**

Gate 1 fails if any check above fails, or if any evidence artifact was produced outside CI.

---

## 9. Open decisions (resolve before Gate 1)

| ID | Decision | Proposed default |
|---|---|---|
| OPEN-1 | Gate 1 month | a recent complete month |
| OPEN-2 | Historical availability lag `L` | 6h, recalibrated to measured live p99 |
| OPEN-3 | Source-reconciliation tolerance | ≤ 0.1% per `(hour, event_type)` cell |

---

## 10. Change control

Changes go through a pull request approved by the owner, with a version bump in the header. Changing §3 or §4 after Gate 1 requires re-running Gate 1.
