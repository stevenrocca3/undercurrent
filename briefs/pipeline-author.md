# Brief: pipeline author: Gate 1 pipeline

**From:** Steven (owner). Drafted 2026-10-14 by the reference agent from the spec only.
**For:** the pipeline agent. Per §6 this must be a different agent from the reference author.
**Spec:** `01-event-semantics.md` v0.6. It is authoritative. If this brief and the spec disagree, the spec wins; tell Steven.

## When to start

**After the verifier's fixtures F18+ are committed** (`briefs/verifier-F18-plus.md`). §7 says expected outputs are committed before the component they test is built. Start once Steven says those fixtures are in.

## Independence rules (hard)

You build from the spec and the fixtures only. Your outputs get compared against an independent reference calculation, and that comparison only catches bugs if you didn't see how the reference does things.

**You may read:**
- `01-event-semantics.md`
- `fixtures/`: every fixture, its README, `SPEC-GAPS.md`, `event_types.txt`, `generate_inputs.py`
- `tools/compare_outputs.py` and its tests (the comparator, which is shared)
- `check.sh`, `README.md`, `requirements.txt`
- `changes/` notes about the spec, fixtures and comparator

**You may not read:** `reference/`, or these change notes:
- `changes/2026-10-14-reference-*.md`
- `changes/2026-10-14-tidy-reference-and-tests.md`
- `changes/2026-10-14-refactor-proposal-shared-contract.md`

**You may not import** from `reference/`, and nothing in `reference/` may import from you.

If the spec is silent on something, don't resolve it by looking at what the reference does. Write it up as a gap (next `G` number in `fixtures/SPEC-GAPS.md`, marked OPEN), choose a provisional behaviour, and flag it to Steven.

## What to build

The pipeline for Gate 1 (§8), covering September 2026. This brief covers §8 criteria **1, 2, 3 and 5**. Source reconciliation against BigQuery (§5.2, criterion 4) and CI evidence (criterion 6) come later in separate briefs. Don't build them yet.

1. **Ingest** GH Archive hour files (§1). Produce the missing-hour registry with all four statuses, including recovery of a truncated stream's final partial line. §1 explains why `gzip.open` iteration isn't enough.
2. **Canonical table `canon-v1`** with every field in §2. Do quarantine in the §2 order (first match wins), into a quarantine table with the §2 schema. Compute `record_hash` exactly as §2 defines it.
3. **Deduplicate** by `event_id` only (§3), with a `conflicts` table. Its schema is up to you; only `conflict_count` is compared.
4. **Time** (§4): `available_at = source_file_hour + 1h + 6h` for backfill; the late and future-skewed flags over kept occurrences; the point-in-time rule for R5.
5. **R1–R7 outputs** in the exact §6 CSV contract (file names, headers, always-present rows, sort order, timestamp format, LF endings). The comparator does exact text comparison after sorting rows, so `7` and `07` differ.
6. **Replay vs batch** (§4, §8 criterion 3): on identical input, both modes give byte-identical canonical tables, compared by content hash after a fixed sort.

### Interface

Provide the same two run modes as the comparator expects, so `check.sh` can drive you exactly as it drives the reference:

```
<pipeline> run INPUT_DIR FIRST_HOUR LAST_HOUR OUT_DIR [--cutoff T ...]   # hours inclusive, e.g. 2026-09-01T00:00:00Z
<pipeline> fixtures FIXTURES_DIR OUT_ROOT                                # each Fxx-*/ (input/ + fixture.json) → OUT_ROOT/Fxx-*/
```

`fixture.json` gives `requested_hours` (an inclusive `[first, last]`) and `cutoffs`. Then:

```
tools/compare_outputs.py fixtures fixtures OUT_ROOT       # must print N/N fixtures equal, PASS
```

Add your fixture run and comparison as extra steps in `check.sh`. Keep the existing steps unchanged.

### Constraints

- Code lives in `pipeline/`. Language and libraries are your choice; add dependencies to `requirements.txt` with exact pins.
- **Scale:** the month is 720 hour files, about 30 GB compressed and roughly 70M events. The dev machine has 8 GB RAM and about 31 GB free disk, so deduplication state must not need to fit in memory, and you can't hold all inputs on disk at once uncompressed.
- **Gate 1 run:** R5 uses 24 cutoffs, `2026-09-08T00:00:00Z` through `2026-10-01T00:00:00Z` daily (§8 criterion 2).

## Done means

1. `./check.sh` passes, including your new steps: every fixture equal for both the pipeline and the reference (§8 criterion 1).
2. Replay vs batch is byte-identical on every fixture, plus at least two real hours, with a test for it.
3. A real-data run over at least a few September hours, compared with `compare_outputs.py dirs` against `reference/reference.py run` on the same hours. You may **run** the reference, as `check.sh` does; you may not **read** it. On a mismatch, report it with your derivation from the spec rather than adjusting your code to match.
4. A change note `changes/YYYY-MM-DD-pipeline-….md`: design, evidence (commands and output), every OPEN gap you raised.
5. Everything stays local, on a branch. Steven reviews before anything is pushed.

## Standing rules (Steven)

- Every change gets its own note in `changes/`.
- No over-coding: build the simplest thing that meets the spec. Tidy files you touch without changing behaviour. Flag larger messes in a separate refactor write-up instead of fixing them on the side.
