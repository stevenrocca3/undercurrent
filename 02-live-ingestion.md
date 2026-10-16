# 02 — Live Ingestion

**Status:** Approved v0.7 · 2026-10-16
**Owner:** Steven (approves all changes)
**Depends on:** `01-event-semantics.md` v0.13. Everything in 01 still holds. This document only adds what changes when files are downloaded as they are published, instead of read from a finished archive.

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
- **Giving up.** An hour still not available **`D = 24` hours** after its due time becomes `missing` in the registry (L2), unless an incomplete version was found (§4). This holds even when the fetcher was down and never tried the hour before `D` (G34). The fetcher keeps trying once an hour for 7 days after that, so a late file is still archived and logged.
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
- If the deadline `D` passes with only incomplete versions, the **last** one is ingested with its 01 §1 status (`truncated` or `unreadable`), with `available_at` set to the moment the deadline passed.
- This matches backfill behaviour, where whatever file exists is used (L3, G34).

**Clock.** The fetcher's clock must be NTP-synchronised. The clock log (§5.4) records the clock source and the offset reported at fetcher start, and every 24 h after that.

---

## 5. Records

### 5.1 Archive

`archive/YYYY-MM-DD-H/<sha256>.json.gz`. Files are never modified or deleted while their hour is inside the retention window. **Retention (L4):** every file is kept until it has been ingested and its month has passed a Gate 2 run; then only the manifest (name, SHA-256, size) is kept. That is the same recoverability argument as 01 G32: the file can be re-downloaded and proven identical by its hash.

### 5.2 Fetch log

Append-only CSV or table, one row per attempt:

`source_file_hour, attempt_at, http_status, bytes, sha256, last_modified, etag, decode_status, outcome, error, available_at`

- `attempt_at` is the UTC time the request was sent.
- `decode_status` is the 01 §1 status, empty unless HTTP 200.
- `available_at` is filled on `success` rows and on `deadline` rows that used a version; empty otherwise.
- `outcome` is one of:
  - `pending`: 404, before or after `D`
  - `success`
  - `incomplete`: 200 but truncated or unreadable
  - `error`: network, 429, 5xx
  - `late`: a complete file found after `D`; archived, never ingested live
  - `deadline`: written when `D` passes without a success. No request is made, and `attempt_at` is the deadline. The row carries the last incomplete version's `sha256`, `bytes` and `decode_status`, or leaves them empty when there was none, in which case the hour is `missing`.
  - `republished`: the +24 h recheck found new content (§6)
  - `unchanged`: the recheck got 304 or the same SHA-256
- **An hour's final outcome** is its `success` or `deadline` row; exactly one exists per tracked hour (§8.4). (G34)

### 5.4 Clock log

`clock.csv`, append-only: `checked_at, source, offset_seconds, error`. One row at fetcher start and every 24 h after. `offset_seconds` is signed (positive means the local clock is ahead) and empty when the offset could not be read, with the reason in `error`. The delay report (§7) gives these offsets. (G34)

### 5.3 Registry evidence (change to 01 §1)

Live runs add `http_status` and `available_at` columns to `registry_evidence.csv`, as 01 §1 already anticipates. Backfill rows leave `http_status` empty and fill in the computed `available_at`. **A 01 version bump comes with this document's approval.**

---

## 6. Ingesting into the pipeline

- **Same code path as replay.** Live ingestion is the existing replay mode (01 §4), fed hour by hour as files succeed, with each hour's observed `available_at`. No second ingestion path is written.
- **Which file per hour.** The fetch log's final outcome (§5.2) decides: the `success` file, the `deadline` version, or none (`missing`). `late` and `republished` files are archived but never ingested, so replay takes its hours from the fetch log or manifest, never from a listing of the archive (G34).
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
  - **The Gate 2 window started at hour 2026-10-16T06:00:00Z**, the fetcher's first tracked hour on the VM. Its 336th hour is 2026-10-30T05:00:00Z, due 06:00Z that day. An hour that hasn't succeeded gets its final outcome at `D`, so every hour is final by 2026-10-31T06:00:00Z at the latest.
  - With 336 samples, the p99 rests on only about 3 hours above it, so it is a thin estimate. Rounding up to the next whole hour and the `+ P` measurement error both push `L` the safe way. The report gives the max alongside the p99, so an outlier is visible.
- **Report.** `evidence/delay-report.json` (`tools/delay_report.py`) contains:
  - window start and end
  - hours tracked; succeeded; missing; ingested truncated; republished
  - delay min, p50, p90, p99, max, in seconds
  - `P`, and the clock offsets
- **Percentiles** are nearest-rank: the value at rank ⌈q·n⌉ of the sorted delays, so every percentile is an observed delay (G35).
- **New `L`.** The observed p99 delay, rounded **up** to a whole hour (`⌈p99 / 1 h⌉`; an exact whole hour stays as it is, G35), applied through 01 §10 change control (01 §4).
  - The `+ P` measurement error is already on the conservative side.
  - Changing `L` changes every backfill `available_at`, so it invalidates detector evaluations made under the old value (01 §4). Gate 1 outputs R1–R4, R6 and R7 do not depend on `L`; R5 does.
  - **Gate 1 is re-run** after `L` changes, so the evidence matches the spec.

---

## 8. Verification

Live data cannot be verified by re-reading a finished archive alone, because `available_at` was observed, not computed. Verification therefore keeps the two-author design from 01 §6, with one addition: a per-hour **`available_at` manifest** (`source_file_hour, available_at`), exported from the fetch log. It is the only live-specific input.

**Manifest format.** A CSV with header `source_file_hour,available_at` and one row per hour.
- `source_file_hour` uses the 01 §6 timestamp format.
- `available_at` is an instant in the 01 §2 `Q3` form: `YYYY-MM-DDTHH:MM:SS[.f{1,6}](Z|±HH:MM)`, uppercase `T` and `Z`, a valid instant, e.g. `2026-10-16T01:03:12.5Z`. Any offset is accepted and converted to UTC.
- **Errors (G33):** the run stops, without writing outputs, on a header other than exactly `source_file_hour,available_at`, an hour listed twice, or a value not in that form (no offset, a space or lowercase separator, the compact form, 7+ fractional digits).
- Listed hours outside the requested range are ignored. An `available_at` earlier than the hour's due time is used as given; it would show a clock fault, and the fetch log (§5.2) is where to catch that.
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

Gate 2 does not require the fetcher to have been running the whole time. Downtime shorter than `D` shows up as late `available_at` values; downtime past `D` makes the hour `missing` (§3). Both are reported in the delay report, never hidden.

---

## 10. Where the fetcher runs

The fetcher has to run without gaps for 14+ days, and `available_at` is only as good as its clock and uptime. The Gate 1 machine, a laptop, idle-slept during a CI run (`changes/2026-10-15-gate1-caffeinate.md`), so it is unsuitable as is. **Host (L8): option A.**

| Option | Cost | Uptime / clock | Notes |
|---|---|---|---|
| **A. Small always-free cloud VM** (Oracle Cloud Always Free, `VM.Standard.A1.Flex` 1 OCPU / 6 GB) | $0 within the free-tier limits | high; NTP managed | enough for fetching and a rolling archive (a month is about 19 GB; 200 GB free), not for running the pipeline. The pipeline runs on the Mac from the archive. **Recommended.** |
| B. This Mac, with sleep disabled | $0 | breaks when the lid closes, at reboots, or offline | fine for a trial run, not for Gate 2 evidence |
| C. GitHub Actions `schedule` | $0 | scheduled runs can start very late or be skipped | unsuitable: the delay would measure the scheduler, not GH Archive |

Option A was first planned on Google Cloud (`e2-micro`), but Google's billing could not be set up, so it runs on Oracle Cloud (v0.5). A Free Tier account there cannot be billed unless it is upgraded to Pay As You Go; a $1 budget alert is part of the setup anyway. Oracle may stop an idle Always Free VM after 7 days; whether to upgrade before the window to avoid that is decided in `briefs/steven-fetcher-vm-setup.md` step 7.

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
| L8 | fetcher host | always-free cloud VM, $1 budget alert; Oracle Cloud Always Free (was GCP `e2-micro`) | 2026-10-15, v0.2; provider 2026-10-16, v0.5 |
| — | manifest format; unlisted hours; fixture file | §8: CSV `source_file_hour,available_at`, offset required, µs precision; unlisted hours are backfill; fixtures use `available_at.csv` | 2026-10-15, v0.3 |
| G34 | fetch-log rows | §5.2 adds an `available_at` column and outcomes `deadline`, `republished` and `unchanged`, and `pending` covers any 404; §5.4 adds a separate `clock.csv`; the last incomplete version is used at `D` whatever its status; downtime past `D` means `missing`; the fetch log, not the archive, decides which file is ingested | 2026-10-16, v0.6 |
| G35 | delay percentiles; rounding `L` | nearest-rank; `L = ⌈p99 / 1 h⌉` | 2026-10-16, v0.7 |
| — | Gate 2 window start | hour 2026-10-16T06:00:00Z (the VM fetcher's first tracked hour) | 2026-10-16, v0.7 |
| G33 | manifest validation | strict 01 §2 `Q3` instant form, any offset; a repeated hour, bad header or bad value is an error; out-of-range hours ignored; an early `available_at` used as given | 2026-10-15, v0.4 |

No open decisions remain in this document.
