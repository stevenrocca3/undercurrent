# 02 — Live Ingestion

**Status:** Approved v0.3 · 2026-10-15
**Owner:** Steven (approves all changes)
**Depends on:** `01-event-semantics.md` v0.12. Everything in 01 still holds. This document only adds what changes when files are downloaded as they are published, instead of read from a finished archive.

> Agents: same rules as 01. This document is authoritative. All decisions are recorded in §12; changes go through 01 §10 change control.

---

## 1. Purpose

Live ingestion has two jobs:

1. **Keep the canonical tables current.** New GH Archive hours enter the pipeline soon after they are published, with `available_at` observed rather than assumed (01 §4).
2. **Measure the publication delay.** 01 §4 fixes the backfill lag at `L = 6h` "until live ingestion has measured the real delay distribution". This document defines that measurement and how its result replaces `L`.

**Out of scope:**
- the GitHub Events API, or any source other than `data.gharchive.org`
- alerting and dashboards
- the detector (Document 03)

---

## 2. Terms

| Term | Meaning |
|---|---|
| hour `h` | a GH Archive hour, `[h, h+1h)`. Its file is `YYYY-MM-DD-H.json.gz` (01 §1). |
| due time | `h + 1h`, the earliest moment the file could be complete |
| attempt | one HTTP request for one hour's file |
| fetcher | the process that makes attempts and stores files. It is separate from the pipeline, which reads only what the fetcher has stored. |
| archive | the fetcher's immutable local copy of every downloaded file |
| fetch log | an append-only record of every attempt (§5) |
| delay | `available_at − due time`, per hour (§7) |

---

## 3. Fetch schedule

- **Hours tracked.** From the live start hour `h0` onward, every hour is tracked. Hours before `h0` are backfill and keep the 01 §4 formula.
- **First attempt.** At the due time.
- **Poll interval.** While an hour's file is not yet available (HTTP 404), it is retried every **`P = 5` minutes** (L1).
  - The interval bounds how precise the measurement can be: an observed `available_at` is late by up to `P`, never early. So the measured delay is conservative.
  - At `P = 5`, a pending hour costs 12 requests per hour.
- **Giving up.** An hour still not available **`D = 24` hours** after its due time becomes `missing` in the registry (L2). The fetcher keeps trying once an hour for 7 days after that, so a late file is still archived and logged.
  - A file found after `D` is archived and logged, but the hour stays `missing` for live runs.
  - Picking such a file up later is a backfill, under the backfill `available_at` rule. It is never a silent status change.
- **Politeness.**
  - at most one request in flight at a time
  - a descriptive `User-Agent` that includes a contact address
  - HTTP 429 and 5xx back off exponentially from 1 min up to `P`, and are logged like any other attempt

---

## 4. When a file is "available"

An attempt **succeeds** only when all of these hold:

1. HTTP status 200, and the body was received in full: `Content-Length` matched where it was sent.
2. The body was written to a temporary file, then renamed into the archive. A partial download never sits under the final name.
3. The file decodes fully under 01 §1, with registry status `present`.

**`available_at`** for the hour is the fetcher's UTC clock reading when step 3 completes for the **first** successful attempt (01 §4: "first successfully downloaded and validated").

- It is recorded in the fetch log and the registry evidence.
- Every canonical row from that file carries it.

**A decodable but `truncated` or `unreadable` file is not a success.**
- It is archived under its SHA-256 and logged with its status.
- Polling continues, because the source may still be mid-upload.
- If the deadline `D` passes with only truncated versions, the **last** truncated version is ingested as `truncated`, as in 01 §1, with `available_at` set to the moment the deadline passed.
- This matches backfill behaviour, where a truncated file is used (L3).

**Clock.** The fetcher's clock must be NTP-synchronised. The fetch log records the clock source and the offset reported at fetcher start, and every 24 h after that.

---

## 5. Records

### 5.1 Archive

`archive/YYYY-MM-DD-H/<sha256>.json.gz`. Files are never modified or deleted while their hour is inside the retention window. **Retention (L4):** every file is kept until it has been ingested and its month has passed a Gate 2 run; then only the manifest (name, SHA-256, size) is kept. That is the same recoverability argument as 01 G32: the file can be re-downloaded and proven identical by its hash.

### 5.2 Fetch log

Append-only CSV or table, one row per attempt:

`source_file_hour, attempt_at, http_status, bytes, sha256, last_modified, etag, decode_status, outcome, error`

- `attempt_at` is the UTC time the request was sent.
- `decode_status` is the 01 §1 status, empty unless HTTP 200.
- `outcome` is one of `pending` (404 before `D`), `success`, `incomplete` (200 but truncated or unreadable), `error` (network, 429, 5xx), or `late` (found after `D`).

### 5.3 Registry evidence (change to 01 §1)

Live runs add `http_status` and `available_at` columns to `registry_evidence.csv`, as 01 §1 already anticipates. Backfill rows leave `http_status` empty and fill in the computed `available_at`. **A 01 version bump comes with this document's approval.**

---

## 6. Ingesting into the pipeline

- **Same code path as replay.** Live ingestion is the existing replay mode (01 §4), fed hour by hour as files succeed, with each hour's observed `available_at`. No second ingestion path is written.
- **Order.** Hours are ingested in `source_file_hour` order. If hour `h` is pending while `h+1` has already succeeded, `h+1` waits until `h` succeeds or reaches `D`. This keeps live identical to replay.
  - The cost: one slow hour delays the next ones by up to `D`.
  - Strict order is decided (L5). Ingesting out of order would need a proof that deduplication's "smallest `(source_file_hour, source_line)`" result does not depend on arrival order; revisit only if measured delays make strict order hurt.
- **Re-published files.**
  - The fetcher re-requests each succeeded hour once at `available_at + 24h`, using `If-None-Match` with the stored `etag`.
  - If the content changed (a new SHA-256), it is archived and logged as `outcome = republished`.
  - The canonical tables keep the **first** version. Changing them would rewrite history behind a cutoff that already passed, which breaks the point-in-time rule.
  - Republished hours are counted and reported.
  - One recheck at +24 h (L6) measures how often republication happens before more requests are spent on it.

---

## 7. Measuring the delay and replacing `L`

- **Per hour.** `delay = available_at − due time`, for every hour with outcome `success`. Hours that ended `missing` or ingested-truncated are counted separately, never folded into the distribution.
- **Window.** At least **14 consecutive days** (336 hours) of live ingestion (L7). Each weekday appears twice.
  - With 336 samples, the p99 rests on only about 3 hours above it, so it is a thin estimate. Rounding up to the next whole hour and the `+ P` measurement error both push `L` the safe way. The report gives the max alongside the p99, so an outlier is visible.
- **Report.** `evidence/delay-report.json` contains:
  - window start and end
  - hours tracked; succeeded; missing; ingested truncated; republished
  - delay min, p50, p90, p99, max, in seconds
  - `P`, and the clock offsets
- **New `L`.** The observed p99 delay, rounded **up** to the next whole hour, applied through 01 §10 change control (01 §4).
  - The `+ P` measurement error is already on the conservative side.
  - Changing `L` changes every backfill `available_at`, so it invalidates detector evaluations made under the old value (01 §4). Gate 1 outputs R1–R4, R6 and R7 do not depend on `L`; R5 does.
  - **Gate 1 is re-run** after `L` changes, so the evidence matches the spec.

---

## 8. Verification

Live data cannot be verified by re-reading a finished archive alone, because `available_at` was observed, not computed. Verification therefore keeps the two-author design from 01 §6, with one addition: a per-hour **`available_at` manifest** (`source_file_hour, available_at`), exported from the fetch log. It is the only live-specific input.

**Manifest format.** A CSV with header `source_file_hour,available_at` and one row per hour.
- `source_file_hour` uses the 01 §6 timestamp format.
- `available_at` is ISO-8601 with an explicit UTC offset and up to microsecond precision, e.g. `2026-10-16T01:03:12.5Z`. A value without an offset is an error.
- Hours the manifest does not list use the 01 §4 backfill rule; these are hours before `h0`.
- In fixtures, the manifest is the file `available_at.csv` next to `fixture.json`. When it is absent, every hour is backfill.

1. **Live = replay.** Replaying the archived files in order, with the manifest's `available_at`, produces canonical tables byte-identical to the live tables (01 §4 rule, same excluded fields).
2. **Pipeline = reference.** The reference calculation, given the archived files and the manifest, produces R1–R7 exactly equal to the live pipeline's.
   - The reference gains an `--available-at FILE` option; the pipeline gains the equivalent.
   - The two authors implement it separately, from this section and new fixtures.
3. **Fixtures (verifier, 01 §7).** New cases:
   - the manifest overrides the backfill formula
   - an R5 cutoff falls between a late hour's due time and its `available_at`, so it is excluded
   - an ingested truncated hour carries the deadline as its `available_at`
   - a republished hour keeps the first version
4. **Fetch log consistency.** Every tracked hour has exactly one final outcome; every `success` row's SHA-256 matches an archived file; and every archived file is referenced by a row.

---

## 9. Gate 2: live ingestion acceptance

Gate 2 passes only if **all** of the following hold over one window of at least 14 days (§7):

1. Every tracked hour has a registry status and a final fetch-log outcome; no hour is left unaccounted for.
2. Live = replay (§8.1), byte-identical.
3. Pipeline = reference on R1–R7 with the `available_at` manifest (§8.2), and every new fixture passes in both implementations.
4. Fetch log consistency (§8.4) holds.
5. `evidence/delay-report.json` exists (§7), along with a proposed `L`.
6. `evidence/gate2.json` exists, generated by CI only, with the same fields as `gate1.json` plus the fetch log's SHA-256 and the manifest.

Gate 2 does not require the fetcher to have been running the whole time. Downtime shows up as late `available_at` values and is reported in the delay report. It is not hidden.

---

## 10. Where the fetcher runs

The fetcher has to run without gaps for 14+ days, and `available_at` is only as good as its clock and uptime. The Gate 1 machine, a laptop, idle-slept during a CI run (`changes/2026-10-15-gate1-caffeinate.md`), so it is unsuitable as is. **Host (L8): option A.**

| Option | Cost | Uptime / clock | Notes |
|---|---|---|---|
| **A. Small always-free cloud VM** (e.g. GCP `e2-micro` in a free-tier US region) | $0 within the free-tier limits | high; NTP managed | 1 GB RAM and 30 GB disk: enough for fetching and a rolling archive (a month is about 19 GB), not for running the pipeline. The pipeline runs on the Mac from the archive. **Recommended.** |
| B. This Mac, with sleep disabled | $0 | breaks when the lid closes, at reboots, or offline | fine for a trial run, not for Gate 2 evidence |
| C. GitHub Actions `schedule` | $0 | scheduled runs can start very late or be skipped | unsuitable: the delay would measure the scheduler, not GH Archive |

Option A needs a billing account on the Google Cloud project; the BigQuery sandbox project has none. Staying inside the always-free limits costs nothing, but a card must be on file, so a budget alert at $1 is part of the setup.

---

## 11. Changes made to 01 (v0.13) with this approval

- **§1 Registry evidence:** add `http_status` and `available_at` columns for live runs (§5.3).
- **§4 `available_at`:** point *Live ingestion* at 02 §4. This adds the definition of a success and the truncated-at-deadline case.
- **§9:** points to the L1–L8 decisions in 02 §12.
- Version bumped to v0.13.

---

## 12. Decisions

| ID | Question | Resolution | Decided |
|---|---|---|---|
| L1 | poll interval `P` | 5 min | 2026-10-15, v0.2 |
| L2 | give-up deadline `D` | 24 h (recommended 48 h) | 2026-10-15, v0.2 |
| L3 | truncated at the deadline: ingest or `missing` | ingest the last truncated version as `truncated`; `available_at` = the deadline | 2026-10-15, v0.2 |
| L4 | archive retention | until the month passes Gate 2, then manifest only | 2026-10-15, v0.2 |
| L5 | hour order | strict `source_file_hour` order | 2026-10-15, v0.2 |
| L6 | republication recheck | once, at `available_at` + 24 h | 2026-10-15, v0.2 |
| L7 | measurement window | 14 days (recommended 28) | 2026-10-15, v0.2 |
| L8 | fetcher host | always-free cloud VM (e.g. GCP `e2-micro`), $1 budget alert | 2026-10-15, v0.2 |
| — | manifest format; unlisted hours; fixture file | §8: CSV `source_file_hour,available_at`, offset required, µs precision; unlisted hours are backfill; fixtures use `available_at.csv` | 2026-10-15, v0.3 (pending approval in PR) |

No open decisions remain in this document.
