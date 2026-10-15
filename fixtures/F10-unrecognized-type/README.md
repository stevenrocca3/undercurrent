# F10: unrecognized event type

F01 plus one event with an unknown type and one with a rare but **recognized** type.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 8 lines.
- Recognized types are exactly the lines of `../event_types.txt` (SPEC-GAPS G4).

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 10001 | type **`MysteryEvent`**, alice, repo 501, 00:50:00 | not in `event_types.txt`: kept **and** flagged |
| 8 | 10002 | type **`GollumEvent`**, bob, repo 502, 00:55:00 | rare but listed, so **not** flagged |

## Expected outputs, derived

- **r1:** canonical = **8**; Q* = 0. An unrecognized type is not a quarantine reason.
- **r2:** hour 00 rows in byte order of event_type: GollumEvent **1**, IssuesEvent **1**, MysteryEvent **1**, PushEvent **2**, WatchEvent **3**. MysteryEvent must appear: "kept and flagged" (§2).
- **r3:** 8, 0, 0.
- **r4 / r5:** same as F01 (neither new line is a star).
- **registry:** `present`.
- **flags:** unrecognized_type = **1**, late = 0, future_skewed = 0.
