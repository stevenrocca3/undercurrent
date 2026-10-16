# Live-ingestion briefs, spec 02 v0.3 manifest format

**Files:** `briefs/pipeline-live-ingestion.md`, `briefs/verifier-live-fixtures.md` (new), `02-live-ingestion.md`, `.geminiignore`; the pipeline clone's sparse-checkout (not in the repo).

**Briefs.** Both are written from the specs only.
- **Pipeline agent:** `--available-at`, the fetcher, live mode, then deployment to the VM, in four steps with a stop after each. It owns fetcher tests against a local HTTP server.
- **Verifier:** at least five fixtures for 02 §8.3, using the next free F numbers, since the G28/G30/G31 fixtures may be in flight.

**02 v0.3 (pending Steven's approval in this PR).** §8 now states the `available_at` manifest format. Both implementations need it to agree:
- a CSV with header `source_file_hour,available_at`
- `available_at` needs an explicit offset and allows µs precision
- **hours not listed are backfill**
- fixtures carry the manifest as `available_at.csv` next to `fixture.json`

The two authors implement it separately from this text.

**Independence.** `.geminiignore` and the pipeline clone's sparse-checkout now hide `changes/*-reference-*.md`, not just the 2026-10-14 ones, so new notes about the reference stay hidden from both agents.
