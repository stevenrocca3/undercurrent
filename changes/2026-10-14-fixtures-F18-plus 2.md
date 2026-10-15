# Change note: fixtures F18–F27 for spec v0.4–v0.6 rules

**Date:** 2026-10-14
**Author:** Verifier Agent (independent of reference and pipeline implementations)
**Status:** Committed locally; reference comparison run after commit per independence protocol

## Summary

Ten new synthetic fixtures (`F18` through `F27`) were authored from `01-event-semantics.md` v0.6, `fixtures/README.md`, and `fixtures/SPEC-GAPS.md`, covering edge cases decided in spec v0.4–v0.6 that were previously covered only by probes.

Expected outputs were hand-derived and authored from prose specifications before running any checks, adhering strictly to §6 and §7 independence guidelines.

## What was added

1. **`F18-q1-non-object-and-bytes`** (pins G13):
   - Q1 quarantine for valid JSON that is not an object (`[1, 2]`, `42`, `"x"`).
   - Empty line between two good lines quarantined as Q1.
   - Non-UTF-8 raw bytes quarantined as Q1.
2. **`F19-q2-null-and-missing`** (pins G14, G16):
   - Q2 quarantine for required fields present as JSON `null` (`id: null`, `payload: null`, `repo.id: null`).
   - Missing required field `public` quarantined as Q2.
   - Empty repo object `repo: {}` missing `repo.id` quarantined as Q2.
3. **`F20-q4-id-types-and-precedence`** (pins G1, G2):
   - Q4 quarantine for `repo.id` as JSON boolean `true` (catching the Python `isinstance(True, int)` trap).
   - Q4 quarantine for `actor.id` as float `201.0`.
   - Line failing both Q2 (missing `public`) and Q4 (numeric `id`): Q2 wins by precedence ($Q1 > Q2 > Q3 > Q4$).
4. **`F21-q3-timestamp-strictness`** (pins G17, G22):
   - Q3 quarantine for lowercase `z`, lowercase `t`, missing seconds, date only, leap second `:60`, 7 fractional digits, and numeric timestamps.
   - Valid ISO-8601 timestamps: 6 fractional digits (canonical), and `+05:30` offset converting across midnight to previous UTC date `2026-08-31` (visible in r4).
5. **`F22-type-public-payload-wrong-types`** (pins G19):
   - `type`, `public`, and `payload` checked for presence only.
   - Non-string `type` `[1]` stored as its JSON text `"[1]"` and flagged `unrecognized_type = 1` in flags and r2.
6. **`F23-registry-corner-cases`** (pins G12, G20, G21):
   - Hour 0: normal file -> `present`.
   - Hour 1: stream cut inside first line before any complete line -> `unreadable` (0 lines contributed, partial bytes discarded).
   - Hour 2: complete gzip member + trailing non-gzip bytes -> `truncated` (complete line kept).
   - Hour 3: 0-byte file -> `unreadable`.
   - Hour 4: valid gzip of empty content -> `present` (0 lines contributed).
   - Hour 5: two concatenated gzip members -> `present` (all lines decoded).
   - Hour 6: full stream with corrupted CRC trailer -> `truncated` (complete line kept).
7. **`F24-line-endings-and-cr`** (pins G3):
   - Duplicate pair where one line ends with `\r\n` and one with `\n`. Because `record_hash` excludes `\r` and `\n`, hashes match and `conflict_count = 0`.
   - Last line of a complete file without a trailing `\n` successfully recovered and parsed as canonical.
8. **`F25-hours-outside-requested-range`** (pins G18):
   - Hour files outside `requested_hours` (`2026-09-01-0.json.gz` and `2026-09-01-2.json.gz`) are ignored; only hour 1 is registered and processed.
9. **`F26-flags-from-kept-occurrence`** (pins G9):
   - Flags evaluated over kept occurrences only: event `26001` kept in Hour 0 is flagged `future_skewed` relative to Hour 0, despite its discarded duplicate in Hour 2 not being future-skewed relative to Hour 2. Kept occurrence `26002` in Hour 0 is not late, despite its discarded duplicate in Hour 2 being late relative to Hour 2.
10. **`F27-r5-boundary-conditions`** (pins G10, G11):
    - Cutoff $t = \text{2026-09-01T07:00:00Z}$. Lookback $[t - 7\text{d}, t) = [\text{2026-08-25T07:00:00Z}, \text{2026-09-01T07:00:00Z})$.
    - `available_at == t` included ($available\_at \le t$).
    - `event_time == t - 7d` included (lookback inclusive on left).
    - `event_time == t` strictly excluded (lookback exclusive on right).

## New OPEN Gaps Raised (for Steven to decide)

- **G23 (OPEN):** `repo.id` / `actor.id` outside 64-bit signed integer range (`[-2^63, 2^63 - 1]`).
- **G24 (OPEN):** CSV escaping and quoting rules (§6) when cell contents contain commas, double quotes, or newlines.
- **G25 (OPEN):** Invalid UTF-8 bytes in canonical fields.

## Proposed Edit to Spec §7 Table (Proposal Only)

```markdown
| ID | Case |
|---|---|
| F18 | valid JSON non-object, empty lines, bad UTF-8 bytes (Q1) |
| F19 | required fields present as null, missing public, empty repo object (Q2) |
| F20 | Q4 ID types (bool repo.id, float actor.id) and Q2 vs Q4 precedence |
| F21 | Q3 timestamp strictness and valid ISO-8601 variations |
| F22 | type, public, and payload with non-standard JSON types |
| F23 | missing-hour registry corner cases across seven hours |
| F24 | CRLF line endings excluded from record_hash and file without trailing LF |
| F25 | hour files outside requested range are ignored |
| F26 | flags evaluated from kept occurrence hour after deduplication |
| F27 | R5 point-in-time boundary conditions: event_time == t, event_time == t - 7d, available_at == t |
```
