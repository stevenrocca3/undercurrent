# Live-ingestion fixtures F28-F32

**Status:** not pushed

F28-F32 were added for 02 §8.3:
- F28 tests manifest availability overriding backfill in both directions, including microsecond precision.
- F29 tests an R5 cutoff before and exactly at a late hour's observed availability.
- F30 tests a truncated hour becoming available at its 24-hour deadline.
- F31 tests the retained first-version file and its observed availability; republish recheck behavior requires a fetcher-level test.
- F32 tests a cutoff that combines manifest-based live availability with backfill availability.

Expected outputs were derived by hand from the spec. Fixed `requested_hours` in F29-F31 to use the required inclusive `[h, h]` pair.

Proof: `./check.sh` passed; both comparisons reported `32/32 fixtures equal`.
