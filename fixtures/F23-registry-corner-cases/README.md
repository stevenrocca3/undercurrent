# F23: missing-hour registry corner cases across seven hours

Hours 0..6 requested. Hour 0 is the normal F01 baseline. Hours 1..6 test each distinct registry status and decompression condition specified in §1 (and SPEC-GAPS G12, G20, G21):
- Hour 0: normal gzip file -> `present`
- Hour 1: gzip stream cut inside its first line (no complete line decoded) -> `unreadable` (contributes no lines; partial bytes are discarded, not Q1)
- Hour 2: complete gzip member + trailing non-gzip bytes -> `truncated` (complete line kept)
- Hour 3: 0-byte file -> `unreadable` (contributes no lines)
- Hour 4: valid gzip of empty content (`gzip.compress(b"")`) -> `present` (contributes 0 lines)
- Hour 5: two concatenated valid gzip members -> `present` (both members decoded)
- Hour 6: full stream with a corrupted CRC trailer -> `truncated` (complete line kept)

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T06:00:00Z` (7 hours). Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: 7 files `2026-09-01-0.json.gz` through `2026-09-01-6.json.gz`.
- Depends on SPEC-GAPS G12 (registry statuses), G20 (trailing non-gzip bytes), G21 (multi-member gzip).

## Input lines per file

| hour | file | status | contents | intent |
|---|---|---|---|---|
| 0 | `2026-09-01-0.json.gz` | `present` | BASE (6 lines, B1..B6) | baseline |
| 1 | `2026-09-01-1.json.gz` | `unreadable` | cut before first `\n` | decompression fails before yielding any complete line -> unreadable |
| 2 | `2026-09-01-2.json.gz` | `truncated` | line 23201 (PushEvent, 501) + trailing non-gzip bytes | trailing non-gzip bytes after complete member -> truncated |
| 3 | `2026-09-01-3.json.gz` | `unreadable` | 0 bytes | 0-byte file is not gzip -> unreadable |
| 4 | `2026-09-01-4.json.gz` | `present` | empty gzip (`gzip.compress(b"")`) | valid empty gzip stream -> present |
| 5 | `2026-09-01-5.json.gz` | `present` | member 1: line 23501 (PushEvent, 501); member 2: line 23502 (PushEvent, 502) | concatenated gzip members -> present |
| 6 | `2026-09-01-6.json.gz` | `truncated` | line 23601 (PushEvent, 501), corrupted CRC trailer | CRC error after complete line -> truncated |

## Expected outputs, derived

- **registry:**
  - `2026-09-01T00:00:00Z,present`
  - `2026-09-01T01:00:00Z,unreadable`
  - `2026-09-01T02:00:00Z,truncated`
  - `2026-09-01T03:00:00Z,unreadable`
  - `2026-09-01T04:00:00Z,present`
  - `2026-09-01T05:00:00Z,present`
  - `2026-09-01T06:00:00Z,truncated`
- **r1:**
  - Canonical: Hour 0 (6) + Hour 2 (1) + Hour 5 (2) + Hour 6 (1) = **10**.
  - Q1..Q4: 0.
- **r2:**
  - Hour 0: IssuesEvent = 1, PushEvent = 2, WatchEvent = 3
  - Hour 2: PushEvent = 1 (23201)
  - Hour 5: PushEvent = 2 (23501, 23502)
  - Hour 6: PushEvent = 1 (23601)
  - (Hours 1, 3, 4 yield 0 lines, so no rows).
- **r3:** 10 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:** None of the added lines are WatchEvents. Stars unchanged from F01: 501 = **2**, 502 = **1**.
- **r5:** Stars unchanged from F01: 501 = **2**, 502 = **1**.
- **flags:** All event times are normal for their respective hour files. All types are PushEvent/WatchEvent/IssuesEvent. All flags are 0.
