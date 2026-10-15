# Change note: fixtures F01–F17 and spec v0.3

**Date:** 2026-10-14
**Documents:** `01-event-semantics.md` (v0.2 → v0.3), new `fixtures/`
**Decided by:** Steven (owner): G1–G18 accepted, G14 → Q2, G12 definitions plus F14–F17, G4 checked against real data
**Status:** proposed, awaiting owner review and merge (§10). Nothing committed.

## Why

§7 requires fixtures with hand-checked expected outputs committed **before** any pipeline component they test. Writing them exposed 18 places where doc 01 was silent (`fixtures/SPEC-GAPS.md`, G1–G18). Without a written answer for each one, the pipeline and the reference calculation could each be "correct" and still disagree.

## Who did what

- **Fixtures:** written by a separate verifier subagent that writes no pipeline code (Python + DuckDB project).
- **Expected CSVs:** written by hand from prose in each fixture's README; no code computes them. `generate_inputs.py` only writes input files from literals, and is deterministic (two runs give byte-identical output).
- **Independent spot-checks by the main session** (re-derived from the decoded inputs): F03, F12 (all three cutoffs), F14, F16, F17.
- **Still to do: Steven hand-checks every fixture**, as §7 requires. Start with F12, F16 and F03.

## New files

```
fixtures/
  README.md            index + CSV conventions
  SPEC-GAPS.md         G1–G18, all marked DECIDED 2026-10-14
  event_types.txt      16 recognized types
  generate_inputs.py   writes every input/*.json.gz
  F01 … F17/           fixture.json, README.md, input/, expected/{r1..r5,registry,flags}.csv
```

F01 is a 6-line baseline. Every other fixture reuses it byte for byte and adds one anomaly.

| ID | Case | Key expectation |
|---|---|---|
| F01 | clean hour | canonical 6; stars 501=2, 502=1 |
| F02 | duplicate within one file | r3 6,1,0; r4 unchanged |
| F03 | duplicate across files | kept occurrence is hour 0 line 4; r3 7,1,0 |
| F04 | conflicting duplicate | r3 6,1,1; first copy kept |
| F05 | malformed JSON | Q1=1; registry stays `present` |
| F06 | missing required fields | Q2=4 (no id / no repo.id / no type+bad date / **no payload**) |
| F07 | late event (plus exact-boundary non-late) | late=1; r4 gets a 2026-08-31 row |
| F08 | future-skewed (plus exact-boundary) | future_skewed=1 |
| F09 | missing hour | registry present/missing/present |
| F10 | unrecognized type | `MysteryEvent` flagged; `GollumEvent` not |
| F11 | repo renamed, old name reused | grouped by `repo_id`, not name |
| F12 | point-in-time trap, 3 cutoffs | `available_at = t` counted; `> t` excluded; `t−7d` inclusive |
| F13 | repeated stars from one actor | each counted; 501=4 |
| F14 | Q3 bad timestamp; Q3 beats Q4; a numeric offset converts to UTC | Q3=2 |
| F15 | Q4 wrong ID types; bad `org.id` stays canonical | Q4=3 |
| F16 | truncated gzip | registry `truncated`; canonical 4; partial line 5 is Q1 |
| F17 | non-gzip file | registry `unreadable`; contributes nothing |

## Spec changes, v0.2 → v0.3, by section

- **§1:** the registry status tests (missing / unreadable / truncated / present) are now a table (G12). Files outside the requested hours are ignored (G18). A new note says readers must recover the partial last line of a truncated stream: iterating over Python's `gzip.open()` raises `EOFError` without returning it, so use `zlib.decompressobj(wbits=31)` instead.
- **§2:**
  - The recognized event-type list is added (G4). It was checked against two real hours, `2026-09-15-15` and `2026-09-20-3` (~200k events), which contained exactly these 16 types and no others.
  - Line definition: an empty line counts as a line. `record_hash` excludes the trailing `\n`/`\r` (G3).
  - Quarantine checks now have a precedence: first match wins, Q1 → Q4 (G1).
  - Q1 now also covers JSON that isn't an object (G13).
  - **Q2 now also covers `public` and `payload`** (G14), and a JSON null counts as missing (G16).
  - Q3 now means not RFC 3339 with `Z` or a numeric offset (G17).
  - Q4 types are spelled out (G2). A badly typed `org.id` becomes null instead of quarantining the line.
- **§3:** definitions of `duplicate_count` and `conflict_count` added. The `conflicts` table is outside the output contract (G6, G7).
- **§4:** the point-in-time rule's boundaries are spelled out: `available_at ≤ t` inclusive, `event_time < t`, and lookback windows include `t − d` (G10, G11). Flags are counted on kept occurrences (G9).
- **§6:** R1, R2 and R3 definitions tightened (G5, G6). Star definition added (G15). The CSV contract is added: columns, formats, and rows sorted by every column (G8).
- **§7:** F14–F17 added. Notes where fixtures live and the `registry.csv` / `flags.csv` format.

**§3 and §4 changed.** Gate 1 has not run yet, so nothing needs re-running. After Gate 1, changes like these would force a re-run.

## Open question, not yet decided

§8 says every fixture must pass in **both** the pipeline and the reference. The fixtures also expect `registry.csv` and `flags.csv`, but §6 only requires the reference to produce R1–R5. Either the reference also produces registry and flags (more work for Steven), or the reference is checked on R1–R5 only and registry/flags are checked against the pipeline alone.

## Gaps no fixture covers yet

- A missing `public` field.
- A JSON-null required field (G16).
- Non-object JSON and empty lines (G13).
- `event_time == t` (G11).
- Flags on duplicate events (G9).

All of these are candidates for later fixtures.
