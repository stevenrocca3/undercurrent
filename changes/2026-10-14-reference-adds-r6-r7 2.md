# Change note: reference calculation adds R6 (registry) and R7 (flags)

**Date:** 2026-10-14
**Document:** `01-event-semantics.md` (v0.3 → v0.4)
**Decided by:** Steven (owner)
**Status:** proposed, awaiting owner review and merge (§10)

## Why

§8 requires every fixture to pass in **both** the pipeline and the reference. The fixtures carry `registry.csv` and `flags.csv`, but v0.3 §6 only asked the reference for R1–R5. That would have left those two outputs checked against one implementation only. Steven chose to have the reference compute them too.

## What changed

- **§6:** two outputs added to the reference calculation:
  - R6, the missing-hour registry: one status per requested hour.
  - R7, flag counts: `late`, `future_skewed`, `unrecognized_type`.
- **§6 CSV contract:** gains `registry.csv` (R6) and `flags.csv` (R7). `flags` always lists all its rows, as `r1` and `r3` do.
- **§7:** the fixture note now just says fixtures carry expected R1–R7. The fixture files are unchanged.
- **§8, criterion 2:** pipeline and reference must be exactly equal on **R1–R7** for September 2026 (was R1–R5).

## Effects

- **More work in the reference script.** It now needs:
  - gzip error handling that tells `unreadable` from `truncated`, using `zlib.decompressobj(wbits=31)`, because iterating over `gzip.open()` drops the partial line (see §1 and F16);
  - the event-type list;
  - the late and future-skew rules.
- The "roughly 200 lines" guideline in §6 is unchanged, but the script may now exceed it. Revisit if it does.
- Over the full month, R6 is the registry for all 720 hours, so the reference's registry must match the pipeline's exactly.
