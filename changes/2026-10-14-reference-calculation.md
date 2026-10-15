# Change note: reference calculation R1–R7

**Date:** 2026-10-14
**Files:** new `reference/reference.py`, `requirements.txt` (`duckdb==1.5.6`) and `.gitignore`
**Spec:** `01-event-semantics.md` v0.4 → v0.5 (§6 authorship)
**Decided by:** Steven: the agent writes the reference, and §6 changes accordingly
**Status:** awaiting Steven's review. Steven must still be able to explain each output (§6).

## Spec change (§6)

```diff
-**Owner and author: Steven, by hand.**
+**Owner: Steven. Author: the reference agent** (the main Claude Code session), which never writes pipeline code.
+**Independence rule.** The pipeline must be written by a different agent. Neither may read the other's
+code while writing its own; both build only from this document and the fixtures.
-- One Python file, or SQL run in DuckDB.
+- One Python file. Python handles per-line parsing and quarantine; DuckDB handles deduplication and aggregation, on disk.
-- Roughly 200 lines or fewer.
+- Roughly 250 lines or fewer.
```

**Why the independence rule matters now:** the R1–R7 comparison only catches bugs if two different authors made different mistakes. With an agent as the reference author, the pipeline's author must be someone else, and must not see this code.

**Why the line limit changed:** the script is 224 lines of code. The extra lines are mostly truncated-gzip handling (R6) and the strict quarantine checks.

## Design

```text
for each requested hour                          # Python, streaming per hour
  read_hour(path) -> status, lines                 §1 registry (R6)
    zlib.decompressobj(wbits=31), multi-member
    on error: re-feed the chunk byte by byte, so output before the error is never lost
  for each line: classify -> Q1..Q4 | canonical    §2 (R1), first match wins
    canonical row -> temp CSV -> DuckDB table `canon`
DuckDB (on-disk file, 3 GB memory cap, spills to temp)
  ranked = row_number() over (partition by event_id order by hour, line)    §3
  kept   = ranked where rn = 1
  R2 R3 R4 R5 R7 = SQL over kept / ranked
```

Why DuckDB: a month is about 70M events, and holding the deduplication state in Python memory would need more than 10 GB on an 8 GB machine.

## Evidence

**Fixtures:** `reference.py fixtures` followed by `compare_outputs.py fixtures` gives **17/17 fixtures equal**. (F09 first crashed on an empty hour; fixed by giving DuckDB the CSV format explicitly.)

**Edge cases no fixture covers**, probed directly. All behave as written in v0.5:

| Input | Result |
|---|---|
| null `id`; missing `public`; null `payload` | Q2 |
| `[1,2]`, `42`, empty line, invalid UTF-8 | Q1 |
| bool `repo.id`, float `actor.id`, `repo.id` = 2^63 | Q4 |
| `...00z` (lowercase), no seconds, date only, `23:59:60`, numeric `created_at` | Q3 |
| string `org.id` | canonical |
| multi-member gzip | present, all lines |
| CRLF line | present; `\r` excluded from the hash |
| last line without `\n` (complete stream) | a normal line |
| 0-byte file | unreadable |
| valid gzip of empty content | present, 0 lines |

**Bug found and fixed during probing.** On a CRC error, zlib discards the output of the failing call. A small fully-decoded file with a bad CRC came out `unreadable` instead of `truncated`, and on large files the result depended on read-chunk boundaries. Fixed with a byte-by-byte re-feed from a saved decompressor copy. Verified identical results (`truncated`, 200,000 lines) at chunk sizes of 1 KB, 64 KB, 1 MB and 16 MB.

**Real data:**

| Run | Result |
|---|---|
| `2026-09-15-15` (busiest local hour) | 81,142 lines, 5.3 s, 870 MB peak |
| `2026-09-15T15` → `2026-09-20T03` (109 hours, 2 local) | 190,273 lines, 8.5 s, ~1 GB peak; 107 hours `missing`, correctly |
| same range, run twice | identical output (comparator PASS) |

The line total matches an independent `json.loads` type count of the same file (81,142).

**Real-data finding:** `2026-09-15-15` has 6 **ForkEvents with `repo: {}`** (no `repo.id`), and 5 of them are also `public: false`. They are correctly Q2. Expect them to show up in BigQuery reconciliation (§5.2) as `parse_or_schema` differences if BigQuery keeps them.

## Gaps found while writing it (provisional choice in the code; Steven decides)

| ID | Gap | Provisional behaviour |
|---|---|---|
| G19 | `type`, `public` or `payload` present but the wrong JSON type (e.g. `type: [1]`, `public: "yes"`) | Not quarantined. `event_type` is stored as the JSON text and flagged `unrecognized_type`; `public` and `payload` are not type-checked. |
| G20 | A truncated stream whose only bytes form a partial first line (no complete line) | `unreadable`; the partial bytes are not counted as Q1 |
| G21 | Non-gzip bytes after a complete gzip member | `truncated` (`gzip -d` would warn and succeed) |
| G22 | Q3 strictness | Uppercase `T`/`Z` only, at most 6 fractional digits, leap second rejected. GH Archive uses `YYYY-MM-DDTHH:MM:SSZ`, so this is latent. |

## Before Gate 1 can run on the month

- **R5 cutoffs for September are undefined.** §8 compares R5 for the month but names no cutoffs.
- **Disk:** a month of GH Archive is roughly 30 GB compressed (two sampled hours: 16 MB and 62 MB). This machine has about 31 GB free. Process it from an external drive, or download and delete hour by hour.
- **Run time:** about 5 s per busy hour, so roughly an hour for the month.

## Not changed

Fixtures, comparator logic, and §1–§5 and §7–§8 of the spec.
