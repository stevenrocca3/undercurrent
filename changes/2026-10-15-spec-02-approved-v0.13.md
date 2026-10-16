# Spec 02 approved (v0.2), spec 01 v0.13

**Files:** `02-live-ingestion.md`, `01-event-semantics.md`

**Steven's decisions.** "Delays should be measured at 14 days, an hour is declared missing after 24 hrs, approve as recommended."

| ID | Resolution |
|---|---|
| L1 poll interval | 5 min |
| L2 give-up deadline `D` | **24 h** (recommended 48 h) |
| L3 truncated at the deadline | ingest the last truncated version; `available_at` = the deadline |
| L4 retention | until the month passes Gate 2, then manifest only |
| L5 order | strict `source_file_hour` order |
| L6 republication | one recheck at +24 h |
| L7 measurement window | **14 days** (recommended 28) |
| L8 host | always-free cloud VM, $1 budget alert |

**02 → v0.2, approved.**
- OPEN markers replaced by the decisions.
- §12 is now a decision table.
- §7, §9 and §10 changed from 28 days to 14 days.

**Consequence of the 14-day window.** With 336 hourly samples, about 3 hours lie above the p99, so it is a thin estimate. §7 now says so. Rounding up to the next whole hour and the `+ P` error both err on the safe side, and the report shows the max next to the p99.

**Consequence of the 24-hour deadline.** A file published more than 24 h late is still archived and logged (`late`), but its hour stays `missing` for live runs. With strict order (L5), a slow hour now holds back later hours by at most 24 h instead of 48 h.

**01 → v0.13**, as 02 §11 listed:
- **§1 registry evidence:** gains `http_status` and `available_at` for live runs.
- **§4:** the *Live ingestion* rule now points to 02 §4.
- **§9:** OPEN-2 notes the 14-day measurement, and a new row records 02's approval.

**What changes:** no code changes, and Gate 1 is unaffected. The §1 and §4 edits only add to live behaviour, and §3 and §4 rules are unchanged for backfill.
