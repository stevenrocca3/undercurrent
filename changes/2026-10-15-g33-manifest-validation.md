# G33 decided: `available_at` manifest validation (spec 02 v0.4)

**Files:** `02-live-ingestion.md` (v0.3 → v0.4), `fixtures/SPEC-GAPS.md`, `reference/reference.py` (347 → 348 lines), `tools/test_manifest_errors.py` (new), `check.sh`.

**Decision.** Steven: "approve G33 as recommended", i.e. the pipeline's provisional rule.
- **Errors:** the run stops, without writing outputs, on a header other than `source_file_hour,available_at`, an hour listed twice, or an `available_at` not in the 01 §2 Q3 instant form.
- **Accepted:** any offset, converted to UTC.
- **Ignored:** listed hours outside the requested range.
- **Used as given:** an `available_at` earlier than the due time.

02 §8 now spells this out, and §12 records G33 and marks v0.3 approved (PR #25).

**Reference.**
- `parse_ts` now requires the Q3 pattern it already had (`RFC3339.fullmatch`) before `fromisoformat`, so 7-digit fractions, a space separator and the compact form are rejected.
- `read_manifest` checks the exact header and rejects an hour listed twice.
- Before this, it accepted all four of the cases the black-box probe found (`2026-10-15-live-step1-cross-check.md`).

**Keeping both implementations to it.**
- `tools/test_manifest_errors.py` runs both CLIs on F12's input with 7 bad manifests (each must exit non-zero with no CSV written) and 4 good edge cases (both must exit 0 with R1–R7 equal).
- It is black-box and imports neither implementation. It replaces the fixture idea, because the fixture format has no way to expect a failure.
- It is in `check.sh`.

**Proof.** `./check.sh`: 35 tool tests OK (2 new), 27/27 fixtures for the reference, 27 pipeline tests OK, 27/27 fixtures for the pipeline. The pipeline's `--available-at` (`6aea713`) is already on `main`, so the test runs against the real pipeline.
