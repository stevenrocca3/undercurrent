# Fetcher cross-check and G34 decided (02 v0.6)

**Why:** the pipeline agent finished live step 2, the fetcher (`886bdf8`, its note is `2026-10-16-pipeline-fetcher.md`), and raised G34. Steven approved G34 as recommended.

**Cross-check:** black-box only; I didn't read the fetcher's code.
- **Real fetch:** `python -m pipeline.fetcher run` ran for 150 s on the Mac against real GH Archive, tracking hours 2026-10-16T02–05.
  - Hours 02–04 were fetched, archived and logged `success`.
  - Hour 05 was not yet due, so it had no row.
- **Hashes:** each archived file's SHA-256 equals its file name and its fetch-log `sha256`.
- **Manifest:** `fetcher manifest` exported 3 rows in the G33 form.
- **Both implementations:** reference and pipeline run on those 3 hours with that manifest give equal R1–R7 (`compare_outputs` PASS).
- **Full `./check.sh`:** passes on `main` + `886bdf8` (a fast-forward), reference side included. The pipeline agent couldn't run it, because its checkout hides `reference/`.
- **Numbers:** in `BENCHMARKS.md` (Fetcher host table).
  - `Last-Modified` was h + 1 h 05 m 04 s on all three hours. That's a header, not a measurement; the 14-day window gives the real delay.

**G34 decision (02 v0.6, §3, §4, §5.2, new §5.4, §6, §9, §12; SPEC-GAPS G34):** the pipeline's provisional rules, except clock offsets.
- Clock offsets go to a separate `clock.csv` instead of `outcome = clock` rows.
- `republished` is now in the outcome list.
- An hour's final outcome is defined as its `success` or `deadline` row.
- §9 says downtime past `D` means `missing`.
- 02 now depends on 01 v0.13, fixing a stale v0.12 reference.

**Brief:** pipeline step 2 now says to move the clock rows to `clock.csv` (02 §5.4) at the start of step 3. Step 3 feeds each hour's final outcome.

**Open:**
- **Archive layout vs input layout:** the fetcher stores `archive/HOUR/<sha256>.json.gz`, but both implementations read flat `YYYY-MM-DD-H.json.gz`. For this check I bridged them with symlinks.
  - Plan for Gate 2: a neutral `tools/` script that builds the flat input from the fetch log's final outcomes (reference side, step 3).
- **macOS has no `chronyc`,** so the Mac's clock row said "offset unavailable". The VM has `chronyc`.
