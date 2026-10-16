# Brief: pipeline author: live ingestion (Gate 2)

**From:** Steven (owner). Drafted 2026-10-15 by the reference agent from the specs only.
**For:** the pipeline agent (the same session that built the Gate 1 pipeline).
**Spec:** `02-live-ingestion.md` v0.3 and `01-event-semantics.md` v0.13. They are authoritative. If this brief and the specs disagree, the specs win; tell Steven.

## When to start

Now, for steps 1–3. Step 4 needs the VM, which Steven is setting up (02 §10, L8). Steps 1–3 run on the Mac against a local test server and the September archive.

## Independence rules (unchanged, hard)

Read `briefs/pipeline-author.md` § Independence. In short: never read `reference/`, never read `changes/*-reference-*.md`, and import nothing from `reference/`. The reference is adding its own `--available-at` support from the same §8 text, independently. Where 02 is silent, add a `G` gap to `fixtures/SPEC-GAPS.md` (OPEN, with your provisional choice) and flag it to Steven. Don't guess silently.

## What to build

1. **`--available-at FILE`** on `run` and `fixtures`, implementing the manifest format in 02 §8.
   - Every canonical row gets its hour's `available_at`. Listed hours take the manifest value; unlisted hours get the 01 §4 backfill value. R5 uses it.
   - `fixtures` mode reads `available_at.csv` next to a fixture's `fixture.json` when one is present.
   - Registry evidence gains `http_status` (empty here) and `available_at` (01 §1).
   - Fixtures that use the manifest are coming from the verifier (02 §8.3). Until they land, test with your own unit tests. Don't write fixtures yourself.
2. **The fetcher** (02 §3–§5), a separate process from the pipeline:
   - **Schedule:** first attempt at the due time `h+1h`; `P = 5 min` polling on 404; `D = 24 h` deadline, then hourly attempts for 7 more days.
   - **Network behaviour:** one request in flight at a time; a descriptive User-Agent (Steven supplies the contact address); exponential backoff on 429 and 5xx.
   - **Success** is HTTP 200, a full body, temp file then rename, and a full decode as `present` (01 §1). `available_at` is stamped when validation finishes.
   - **Truncated files:** a decodable but truncated file is archived and polling continues. At the deadline, the last truncated version is used (L3).
   - **Records:**
     - the archive: `archive/YYYY-MM-DD-H/<sha256>.json.gz`
     - the append-only fetch log, with the exact columns and `outcome` values in 02 §5.2
     - one recheck at `available_at + 24h` using `If-None-Match`, logging `republished` when the content changed
   - **Manifest export:** the fetch log exports the `available_at` manifest.
   - **State:** it must survive a restart without losing or duplicating fetch-log rows. Keep the state in the fetch log itself.
   - **Clock:** record the NTP offset at start and every 24 h (02 §4).
3. **Live mode** (02 §6): feed succeeded hours, in strict `source_file_hour` order, into your existing replay path with their observed `available_at`. An hour waits for every earlier hour to succeed or pass `D`.
   - The canonical tables keep the first version of a republished file.
   - Live tables must be byte-identical to a replay of the archive using the exported manifest (02 §8.1).
4. **Deploy** the fetcher on the VM once Steven has it running, and start the 14-day window (L7). The pipeline itself runs on the Mac from a copy of the archive.

## Tests you own

- **Fetcher unit tests against a local `http.server`** with scripted responses: 404 then 200; 200 truncated, then 200 complete; a connection dropped mid-body (no final-name file may appear); 429 and 500 backoff; the deadline passing with only a truncated version; a restart mid-hour; a republished file at +24 h.
- **Live vs replay** on a few September hours, fed through the fetcher from a local server that serves `~/undercurrent-data/gharchive/` with artificial delays.
- Add your tests to `check.sh` beside your existing ones.

## Not yours

- Fixtures (the verifier).
- The reference's `--available-at` (the reference agent).
- The delay report and Gate 2 evidence tooling, which go in `tools/` and come later.

## Reporting

- Same rules as before: a change note per step, BENCHMARKS rows for anything measured (whether the machine was idle, and how it was measured), and a report of 10 lines or fewer.
- Stop after each numbered step for Steven's review.
