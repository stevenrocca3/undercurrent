# F05: malformed JSON line

F01 with a truncated JSON line **inserted at line 4**, in the middle of the file, so later lines must still be processed.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 7 lines.

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1 | 1001 | B1 | baseline |
| 2 | 1002 | B2 | baseline |
| 3 | 1003 | B3 | baseline |
| 4 | (5001) | `{"id":"5001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":50` : the object stops mid-way | Q1 |
| 5 | 1004 | B4 | baseline (now at line 5) |
| 6 | 1005 | B5 | baseline (now at line 6) |
| 7 | 1006 | B6 | baseline (now at line 7) |

## Expected outputs, derived

- **r1:** line 4 is not valid JSON, so Q1 = **1**. The other 6 are canonical = **6**. 6 + 1 = 7 input lines.
- **r2, r3, r4, r5:** identical to F01. Id 5001 never becomes an event, so r3 has 6 distinct ids.
- **registry:** `present`. A bad line does not make the file `unreadable` or `truncated`: the gzip stream decodes fully. **flags:** all 0.
