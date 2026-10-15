# F24: CRLF line endings excluded from record_hash and file without trailing LF

F01 plus lines testing line ending normalization and final line recovery (§2, SPEC-GAPS G3):
- The same event once with a CRLF ending (`\r\n`) and once with LF (`\n`): a duplicate pair. Per §2, `record_hash` excludes trailing `\n` and `\r`. If `\r` is correctly excluded, both occurrences have identical `record_hash`, so `conflict_count` is 0. If `\r` were incorrectly included in the hash, `conflict_count` would be 1.
- The last line of a complete file without a trailing `\n`: recovered as a valid line and parsed as canonical.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 9 lines.
- Depends on SPEC-GAPS G3 (`record_hash` excludes trailing `\n` and `\r`).

## Input lines

| line | id | content / line ending | status / intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 24001 | PushEvent, 501, ends with `\r\n` | canonical; kept occurrence |
| 8 | 24001 | PushEvent, 501, ends with `\n` | duplicate of line 7; conflict = 0 |
| 9 | 24002 | PushEvent, 501, ends without `\n` | canonical; recovered from EOF |

## Expected outputs, derived

- **r1:** lines 1-6 (B1..B6) + line 7 (24001) + line 8 (24001 before dedup) + line 9 (24002) = **9**. Q1..Q4 = 0.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 4 (B1, B3, 24001 kept, 24002)
    - WatchEvent: 3 (B2, B4, B6)
- **r3:** 8 distinct IDs (1001..1006, 24001, 24002), duplicate_count = **1** (line 8), conflict_count = **0** (raw bytes without `\r` and `\n` match line 7).
- **r4:** unchanged from F01: 501 = **2**, 502 = **1**.
- **r5:** unchanged from F01: 501 = **2**, 502 = **1**.
- **registry:** `present`.
- **flags:** all 0.
