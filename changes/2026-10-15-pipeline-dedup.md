# Change note: pipeline step 3, deduplication

**Date:** 2026-10-15 · **Spec:** v0.9 §3 · **Status:** committed locally on `pipeline`, not pushed
**Files:** `pipeline/dedup.py`, `pipeline/test_dedup.py` (new); `pipeline/__main__.py`, `pipeline/canon.py`, `check.sh`, `fixtures/SPEC-GAPS.md`

## Why
Brief item 3: dedup by `event_id` only, with a `conflicts` table and the r3 counts (§3, §6 R3).

## What changed
- Merged `origin/main` (spec v0.9). In `SPEC-GAPS.md`, G27–G29 are marked DECIDED (v0.9); G26 was already DECIDED (v0.8).
- **G28 check made explicit:** `classify` now checks exactly `id`, string `type`, `actor.login`, `repo.name` and `payload.action`, as §2 v0.9 lists. No behaviour change: the other strings it used to see (`payload_raw`, and a non-string `type`'s raw text) are slices of valid UTF-8, so they can't hold a lone surrogate.
- **`pipeline/dedup.py`** works in DuckDB:
  - `GROUP BY event_id HAVING count(*) > 1` finds repeated IDs. A window over only those rows ranks each ID's occurrences by `(source_file_hour, source_line)`.
  - `duplicates` holds the discarded occurrences, each with its kept occurrence's hour, line and hash.
  - `conflicts` is a view: the duplicates whose `record_hash` differs from the kept one.
  - `events` is a view: `canon` minus `duplicates`.
  - Only the duplicates are copied, so the full table isn't stored twice.
  - r3 = (canon rows − duplicates, duplicates, conflicts).
- **`run`** writes `r3.csv`.
- **`canon.py`:**
  - `SET memory_limit='3GB'`, so a GROUP BY too big for memory spills to disk on the 8 GB machine.
  - `read_json`'s `maximum_object_size` lowered from 1 GiB to 256 MiB, because DuckDB reserves twice that and the 1 GiB setting failed under the new limit. A spooled row over 256 MiB now fails the run loudly.
- **`test_dedup.py`:** the kept occurrence is the smallest `(hour, line)` even when it was loaded later; A/A/B counting; identical bytes count as a duplicate, not a conflict.

## Proof
```
$ .venv/bin/python -m unittest -q tools/test_compare_outputs.py pipeline/test_*.py   → Ran 37 tests, OK
$ .venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
$ .venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok '
  → 0/27 fixtures equal, FAIL. Every FAIL line is "missing in actual" (108 = r2, r4, r5, flags × 27).
    r1, r3 and registry are ok in 27/27.
```
Synthetic 100k-line hour: 7.2 s, 444 MB peak RSS (unchanged from step 2).

## Left open
- **Disk use at month scale hasn't been measured.** `canon` stores `payload_raw` for about 70M rows, and the disk has about 31 GB free. The synthetic hour, which repeats one payload, compresses to 4.5 MB, so it says nothing about real data. This needs measuring on a real hour before the month run.
- **G30 (OPEN, raised by the reference agent):** a non-string `type` as raw text or re-serialized. The pipeline uses raw text, as G30 recommends.
- Categorizing conflicts for the Gate 1 report (§3) is not built.
