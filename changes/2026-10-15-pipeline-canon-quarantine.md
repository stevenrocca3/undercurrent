# Change note: pipeline step 2, canonical table and quarantine

**Date:** 2026-10-15
**Files:** `pipeline/canon.py`, `pipeline/test_canon.py` (new); `pipeline/__main__.py`, `check.sh`, `fixtures/SPEC-GAPS.md` (edited). Also merged `origin/main` (spec v0.8) into `pipeline`.
**Spec:** v0.8, §2 (and §4 for `available_at`). No spec change.
**Status:** committed locally on `pipeline`, not pushed

## Why

Brief item 2: build the `canon-v1` table with every §2 field, quarantine lines in the §2 order (first match wins) into a table with the §2 schema, and compute `record_hash` exactly as §2 defines it. R1 is the compared output this step makes possible.

## Housekeeping first

- `git fetch origin && git merge origin/main`: a clean merge (`711836d`). It brought in spec v0.8 (G26 decided), the G26 spec change note, and a `.gitignore` rule for iCloud copies. `reference/` is still outside the sparse checkout.
- `fixtures/SPEC-GAPS.md`: G26 marked **DECIDED 2026-10-15 (owner, spec v0.8)**. `registry_evidence.csv` is unchanged.

## What changed

- **`pipeline/canon.py`**
  - `classify(raw, partial)` returns `Q1`..`Q4`, or `canonical` with the parsed fields, checking in §2 order:
    - **Q1:** a partial last line of a truncated hour, whether or not it parses; invalid UTF-8; not exactly one JSON object; `NaN`/`Infinity` (Python's `json` accepts these, JSON doesn't); a byte-order mark; trailing data after the object; nesting too deep for Python's parser. Also a lone surrogate in a stored string (G28, provisional).
    - **Q2:** `id`, `type`, `created_at`, `public`, `payload`, `actor.id` or `repo.id` missing or `null`. An `actor` or `repo` that isn't an object counts as missing its `id`.
    - **Q3:** `created_at` is not a string that fully matches `YYYY-MM-DDTHH:MM:SS[.f{1,6}](Z|±HH:MM)` with ASCII digits only, or it is not a valid instant. Invalid instants are month 13, Feb 30, `:60`, an offset hour above 23 or minute above 59, or a value that falls outside years 1–9999 once converted to UTC. Accepted values are converted to naive UTC with µs precision.
    - **Q4:** `id` is not a string, or `actor.id`/`repo.id` is not a JSON integer in int64 range. A bool is not an integer here.
  - `parse_object` reads the top-level object with the stdlib decoder (same grammar; for duplicate keys the last one wins, as `json.loads` does). It also keeps each top-level value's raw text, so `payload_raw` and a non-string `type` (§2: "its JSON text") are stored exactly as written rather than re-serialized. Re-serializing would also have broken things like `1e400`, which becomes `Infinity`, which isn't JSON.
  - `record_hash` is the SHA-256 hex digest of the line bytes without the `\n` (already stripped by ingest) and without one trailing `\r`.
  - `CanonStore` writes to `OUT_DIR/canon.duckdb`, which holds the tables `canon` (the 18 §2 columns) and `quarantine` (`source_file_hour, source_line, reason_code, raw_line`). `raw_line` is a BLOB because it can be invalid UTF-8. Each hour's rows are spooled to NDJSON next to the database and loaded with one `read_json` insert, so Python holds one row at a time and the tables live on disk.
  - Column notes:
    - All timestamps are `TIMESTAMP` in UTC, µs.
    - `available_at = source_file_hour + 1h + 6h`.
    - `source_last_modified` is null, because local files have no `Last-Modified`.
    - `ingested_at` is the run's start time (G29).
    - `payload_raw` is a `VARCHAR` holding JSON text, not DuckDB's `JSON` type. That type would re-validate the text with a different parser and could reject a line that §2 accepted.
    - `org_id` is null when `org.id` isn't an int64.
- **`pipeline/__main__.py`:** each line is classified and stored, and `r1.csv` is written, with all five rows always present and sorted in byte order (`Q1..Q4,canonical`). The docstring now cites v0.8.
- **`pipeline/test_canon.py`** (9 tests): the cases no fixture covers. They are raw-text keeping, duplicate keys, inputs Python accepts but JSON doesn't, a partial line that would parse, `repo` that isn't an object, `public: false`, more Q3 strictness cases, int64 bounds and bool IDs, wrong-typed optional fields, and that only one trailing `\r` is dropped from the hash.
- **`check.sh`:** the pipeline test step now runs `test_canon.py` as well. The steps before it are unchanged.

## Proof

```
$ .venv/bin/python -m unittest tools/test_compare_outputs.py pipeline/test_ingest.py pipeline/test_canon.py
Ran 36 tests in 0.260s
OK

$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out
...
0/27 fixtures equal
FAIL
```

The overall FAIL is expected at step 2. Counted from the comparator output:

```
r1.csv ok: 27/27
registry.csv ok: 27/27
missing-in-actual lines: 135      # r2, r3, r4, r5, flags × 27: later steps
other FAIL lines: 0
```

I also checked the tables directly against the fixture READMEs:
- In all 27 fixtures, the `canon` row count and the `quarantine` count per reason equal `r1.csv`.
- F21 `+05:30` gives `2026-08-31 23:30:00`, and the 6-digit fraction is kept (`.123456`).
- F14 `-02:00` gives `00:50:00`.
- F22: `type` `[1]` is stored as `[1]`; `"public":"yes"` is canonical with `is_public` null; `"payload":"x"` gives `payload_raw` `"x"`.
- F24: lines 7 (CRLF) and 8 (LF) have the same `record_hash`.
- F16: line 5 is in quarantine as `Q1`, with its 55 raw bytes.
- F18: the invalid-UTF-8 line is kept byte for byte in `raw_line`.
- F15: a string `org.id` gives `org_id` null.

Throughput on a synthetic hour of 100,000 lines of about 1.6 KB (160 MB uncompressed): 7.0 s wall, 466 MB peak RSS. That's about 14k lines/s, so roughly 80 minutes for the month's ~70M lines.

## Left open (told to Steven)

- **G27 (OPEN):** what to store when `public` is not a bool, or when `repo.name`, `actor.login` or `payload.action` is missing or not a string. Provisional: null. This makes `repo_name` and `is_public` nullable even though §2 says they aren't. It doesn't affect R1–R7.
- **G28 (OPEN):** a lone-surrogate escape (`"\ud800"`) in a stored string. Provisional: Q1, following G25's intent.
- **G29 (OPEN):** the pipeline-clock `ingested_at` makes byte-identical replay vs batch impossible over every column. Provisional: one value per run, left out of the replay hash. To be confirmed before step 6.
- Not run on real September hours yet.
- The `conflicts` table, deduplication, and r2–r5 and flags are steps 3–5.
