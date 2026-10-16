# Brief: verifier: live-ingestion fixtures (02 §8.3)

**From:** Steven (owner). Drafted 2026-10-15 by the reference agent from the specs only.
**For:** the verifier agent (Gemini CLI). Per 01 §7, the verifier writes fixtures and never pipeline or reference code.
**Spec:** `02-live-ingestion.md` v0.3 (§8 manifest format, §8.3 cases) and `01-event-semantics.md` v0.13 (§4 point-in-time rule, §6 output contract).

## Numbering

Separate G28/G30/G31 fixtures may be in flight. Take the **next free F numbers on `main` when you start**, and list them in your report.

## The new input: `available_at.csv`

A fixture may carry `available_at.csv` next to `fixture.json`, in the 02 §8 format:
- header `source_file_hour,available_at`
- `available_at` has an explicit offset and up to µs precision

Hours it does not list use the backfill rule `source_file_hour + 1h + 6h`. Both implementations pick the file up automatically in `fixtures` mode. Describe the manifest in each fixture's README, and add its creation to `generate_inputs.py` if that is where you build the inputs.

## Cases (at least one fixture each)

1. **The manifest overrides the backfill rule, in both directions.**
   - Hour A is observed earlier than its backfill value, so a cutoff between the two now includes it.
   - Hour B is observed later, so a cutoff between the two now excludes it.
   - Include a non-whole-second `available_at`.
2. **A late hour against an R5 cutoff.** The cutoff `t` falls between the hour's due time `h+1h` and its observed `available_at`, so its stars are excluded at `t` and included at a later cutoff. Include the boundary `available_at == t`: it is included, because `≤ t` (01 §4).
3. **Truncated hour ingested at the deadline (L3).** A truncated input file whose manifest `available_at` equals its deadline `h + 1h + 24h`. The registry says `truncated`, the partial line is `Q1`, and R5 sees its complete lines only from the deadline on.
4. **A republished hour keeps the first version (02 §6).** In fixture form this is simply the first version's file plus its manifest time. State this in the README.
   - The fixture cannot show a second version: the archive serves one file per hour to the pipeline.
   - If you find this case can't be expressed as a fixture, say so and propose a fetcher-level test for the pipeline agent instead.
5. **Mixed backfill and live.** Some hours are listed in the manifest and some are not, and one cutoff depends on both kinds.

Expected outputs are hand-derived from the spec, as before. Never generate them by running either implementation. You may run `./check.sh` afterwards; a mismatch goes to Steven with your derivation.

## Independence

Unchanged from `GEMINI.md`. Don't read `reference/` or `changes/*-reference-*.md`.

## Done when

- The fixtures and READMEs are committed, and `fixtures/README.md` lists them.
- Any spec silence is added to `SPEC-GAPS.md` as OPEN.
- A report of 10 lines or fewer that names the F numbers and the `./check.sh` result. The reference already supports the manifest; the pipeline may not yet, so expect pipeline failures until its step 1 lands.
