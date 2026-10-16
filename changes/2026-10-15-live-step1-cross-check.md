# Live ingestion step 1: cross-check of `--available-at`, G33 findings, VM guide

**Files:** `BENCHMARKS.md`, `briefs/steven-fetcher-vm-setup.md` (new).

## Cross-check: pipeline `6aea713` vs reference, black box

Both implementations got the same manifest. The pipeline was run from the clone, and its code was not read.

- **F12 input**, with my probe manifest: hour 02 observed early (03:04:05.5Z), and hour 01 observed 1 µs after the 08:00 cutoff. **PASS**: all 7 files equal.
- **Real week** 2026-09-15 → 21 (168 hours, 14.96M lines):
  - The manifest lists every other hour (84), at a random 0–40 h after the due time, with microseconds. The other 84 hours are backfill.
  - 28 cutoffs, every 6 h from 09-15T06 to 09-22T00.
  - **PASS**: all 7 files equal.
  - **Not vacuous**: against a backfill-only reference run, the manifest changes **162,814 R5 rows** (1,369,608 rows vs 1,432,476).
  - Times: reference 426.26 s, pipeline 110.61 s. The machine was not confirmed idle; the timings are not the point of this run.

## G33: where the two implementations disagree

Same F12 input, one malformed manifest per row:

| manifest | reference | pipeline |
|---|---|---|
| 7 fractional digits | accepts, truncates to µs | error |
| hour listed twice | accepts, last wins | error |
| space instead of `T` | accepts | error |
| compact `20260901T030000Z` | accepts | error |
| `+02:00` offset | accepts, converts | accepts, converts (same R5) |
| hour outside the requested range | ignored | ignored (same R5) |
| `available_at` < `h + 1h` | used as given | used as given (same R5) |
| lowercase `t`/`z` | error | error |
| wrong header | error | error |

**What it means.** The reference parses with Python's `datetime.fromisoformat`, which accepts more than 02 §8's "ISO-8601 with an explicit offset, up to µs". The pipeline's provisional G33 matches the spec's wording more closely.

**Recommendation for Steven: approve G33 as the pipeline proposed.**
- These are errors: a repeated hour, a bad header, and a value not in the 01 §2 Q3 instant form (`T`, `Z` or `±HH:MM`, 1–6 fractional digits).
- Any offset is accepted.
- Out-of-range hours are ignored.
- An early `available_at` is used as given.

On approval, the reference switches to the Q3 pattern it already has, plus a repeated-hour check. The verifier should then add a fixture or two for the error cases, so both implementations are held to the decision.

**The `fixtures` flag question** (from the pipeline's note). The pipeline agent is right: `fixtures` mode needs no `--available-at` flag, because each fixture brings its own `available_at.csv`. The brief's wording, "on `run` and `fixtures`", was loose; the reference does the same as the pipeline.

## VM guide

`briefs/steven-fetcher-vm-setup.md` is Steven's one-time setup for 02 §10 (L8):
- billing link
- the $1 budget alert
- an `e2-micro` in `us-central1-a` with a 30 GB `pd-standard` disk
- clock and SSH check
- the handover line for the pipeline agent
- a cost check after 48 h
- stop and delete commands

**Cost caveat, found while writing it.** The VM and disk are free, but an in-use external IPv4 address has been billed at about $0.005/h (~$3.65/month) since February 2024, and current free-tier wording on that couldn't be confirmed. The guide says so, and offers an IPv6-only variant if the 48-hour bill shows the charge.
