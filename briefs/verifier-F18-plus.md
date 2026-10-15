# Brief: verifier agent: fixtures F18+

**From:** Steven (owner). Drafted 2026-10-14 by the reference agent from the spec only.
**For:** the verifier agent (§7). You write fixtures and nothing else: no pipeline code, no reference code.
**Spec:** `01-event-semantics.md` v0.6. It is authoritative. If this brief and the spec disagree, the spec wins; tell Steven.

## Goal

Add fixtures for the rules decided in spec v0.4–v0.6 that no fixture covers yet. These include G13, G14, G16, G18, G19–G22 and G9/G11 in `fixtures/SPEC-GAPS.md`. Today these rules are checked only by throwaway probes, and the pipeline (not yet written) will be held to them by fixtures alone.

## Independence rules (hard)

- **Do not read** `reference/` or these change notes:
  - `changes/2026-10-14-reference-*.md`
  - `changes/2026-10-14-tidy-reference-and-tests.md`
  - `changes/2026-10-14-refactor-proposal-shared-contract.md`
  
  They describe how the reference behaves. Your expected outputs must come from the spec, not from the reference.
- **Do not run** `reference/reference.py` or `./check.sh` until your expected outputs are written and committed.
- When you do run `./check.sh` and the reference disagrees with your expected output, **do not change your expected output to match**. Report the disagreement to Steven with your derivation. Either side might be wrong, and catching that is the reason both exist.

## Conventions (same as F01–F17, see `fixtures/README.md`)

- Each fixture is **F01 plus one anomaly** wherever possible, so expected outputs are F01's plus a small delta.
- Inputs are written by `fixtures/generate_inputs.py` from literal lines only. Byte-level cases (CRC damage, trailing garbage, multi-member, CRLF) get a small named helper, as `write_truncated_gz` does for F16.
- Each fixture has a `README.md` that lists every input line and its intent and derives every expected number in prose. Expected CSVs are written by hand; no code computes them.
- Add each fixture to the index in `fixtures/README.md`, and to its "Depends" line in `SPEC-GAPS.md`.

## Cases to cover

You choose how to group them into fixtures; about one fixture per row is a reasonable split. Each "Spec" entry points to the rule you derive the expected output from.

| # | Case | Inputs to include | Spec |
|---|---|---|---|
| 1 | Valid JSON that isn't an object; empty line; bad UTF-8 | `[1,2]`, `42`, `"x"`, an empty line between two good lines, a line with invalid UTF-8 bytes | §2 Q1, G13 |
| 2 | Required field present as `null`; `public` missing | `"id":null`, `"payload":null`, `"repo":{"id":null,…}`, no `public` key, `"repo":{}` (seen in real data) | §2 Q2, G14, G16 |
| 3 | More Q4 types | bool `repo.id`, float `actor.id` (`201.0`), a line that fails Q2 *and* Q4 (Q2 wins) | §2 Q4, G1 |
| 4 | Q3 strictness | lowercase `z`; lowercase `t`; no seconds; date only; `23:59:60`; 7 fractional digits; 6 fractional digits (valid); numeric `created_at`; `+05:30` offset that crosses into the previous UTC date (valid, check r4's date) | §2 Q3, G22 |
| 5 | `type` / `public` / `payload` with the wrong JSON type | `"type":[1]`, `"public":"yes"`, `"payload":"x"`. These are canonical, not quarantined. A non-string `type` is stored as its JSON text and flagged `unrecognized_type`; check r2 and flags. | §2 last paragraphs, G19 |
| 6 | Registry statuses, one hour each | a gzip stream cut inside its first line (no complete line); complete gzip member + trailing non-gzip bytes; a 0-byte file; valid gzip of empty content; two concatenated gzip members; a full stream with a corrupted CRC trailer | §1 registry table, G12, G20, G21 |
| 7 | Line endings | the same event once with a CRLF ending and once with LF (a duplicate pair, so `\r` exclusion shows up in `conflict_count`); last line of a complete file without a trailing `\n` | §2 line handling, G3 |
| 8 | File outside the requested range | an hour file just before and just after `requested_hours` | §1 last line, G18 |
| 9 | Flags use the kept occurrence | a duplicate whose kept copy is late (or future-skewed) relative to its own hour, but would not be relative to the discarded copy's hour | §4 flags, G9 |
| 10 | `event_time == t` in R5 | a star exactly at a cutoff (excluded), one exactly at `t − 7d` (included), one with `available_at == t` (included) | §4 point-in-time rule, G10, G11 |

## Gaps I can see already: raise these, don't guess

The spec does not settle these. If a case needs one, choose an input that avoids it, or record it in `SPEC-GAPS.md` as **G23+ (OPEN)** for Steven to decide:

- **`repo.id` / `actor.id` outside int64** (e.g. `2^63`). §2 says the type is int64 and Q4 requires an integer, but doesn't say what an integer that doesn't fit is.
- **CSV quoting.** §6 doesn't say how a cell containing `,` or `"` is quoted. That matters for case 5 if the non-string `type` has a comma (`{"a":1,"b":2}`). Use `[1]` unless Steven rules on quoting.
- **Invalid UTF-8 in r2.** A canonical line whose `type` contains invalid UTF-8 would put non-UTF-8 bytes in a CSV. Keep bad UTF-8 to the Q1 case.

## Deliverables

1. `fixtures/F18-…` onward: `fixture.json`, `README.md`, `input/`, `expected/`.
2. `generate_inputs.py` updated, still deterministic. Existing F01–F17 inputs must stay byte-identical: check `git diff --stat fixtures/F0* fixtures/F1[0-7]*` shows nothing.
3. `fixtures/README.md` index and `SPEC-GAPS.md` updated.
4. A proposed edit to the §7 table adding the new rows, **as a proposal**: only Steven merges spec changes (§10).
5. A change note `changes/YYYY-MM-DD-fixtures-F18-plus.md`: what was added, which gaps each fixture pins, and any new OPEN gaps.
6. After committing expected outputs, the `./check.sh` result, with every disagreement listed (see the independence rules).

## Standing rules (Steven)

- Every change gets its own note in `changes/`.
- No over-coding. Keep `generate_inputs.py` as plain literal lines, adding helpers only for byte-level cases.
