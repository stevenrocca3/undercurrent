# F17: unreadable hour

Two hours are requested. Hour 0 is the normal F01 file. Hour 1 has the right name but is **not gzip at all**: it is one plain, uncompressed JSON line.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T01:00:00Z`. Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz` (6 lines, gzip), `2026-09-01-1.json.gz` (189 raw bytes, not gzip).
- Depends on SPEC-GAPS G12 (decided): unreadable = not gzip, or fails before yielding any line.

## Input lines

| file | line | id | content | intent |
|---|---|---|---|---|
| hour 0 | 1-6 | 1001-1006 | F01 baseline, gzip | baseline |
| hour 1 | (raw bytes) | 17001 | `{"id":"17001","type":"WatchEvent",...,"repo":{"id":501,...},...,"created_at":"2026-09-01T01:10:00Z"}\n`, **uncompressed** | **trap:** perfectly good JSON. A reader that falls back to plain text when gzip fails would count a star on 501. |

Verified: `gzip -dc` says "not in gzip format". Python `gzip.open(...).readline()` raises `BadGzipFile: Not a gzipped file (b'{"')` before yielding any line.

## Expected outputs, derived

- **registry:** 00 `present`, 01 **`unreadable`**.
- **r1:** hour 1 contributes no lines (not even a Q1). canonical = **6**; Q* = 0.
- **r2:** only hour 00, as F01. No hour-01 rows.
- **r3:** 6, 0, 0.
- **r4 / r5:** same as F01: 501 = **2** (not 3), 502 = 1.
- **flags:** all 0.
