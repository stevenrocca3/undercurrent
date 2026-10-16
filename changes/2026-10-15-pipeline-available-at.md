# Pipeline: `--available-at` manifest (live ingestion step 1)

**Why:** `briefs/pipeline-live-ingestion.md` step 1. Implements 02 §8 (manifest format), 01 §4 (`available_at` rules) and 01 §1 / 02 §5.3 (registry evidence columns).

**What changed**
- `pipeline/canon.py`: `read_manifest(path)` reads the 02 §8 CSV, parsing `available_at` with the existing §2 Q3 instant parser (offset required, up to µs). `available_at(hour, manifest)` returns the manifest value, or the §4 backfill `h + 1h + L`. `CanonStore.load_hour` now takes `available_at` instead of computing it.
- `pipeline/__main__.py`: `run --available-at FILE`. `fixtures` mode reads `available_at.csv` beside each `fixture.json` when present. `registry_evidence.csv` gains `http_status` (empty, since there is no HTTP here) and `available_at`.
- `pipeline/ingest.py`: `format_instant` (seconds, plus `.ffffff` only when there's a fraction) for the evidence column.
- `pipeline/test_available_at.py` (6 tests): offsets and fractions, the error cases, unlisted hours → backfill, a manifest equal to backfill leaves every compared file byte-identical (F27 copy), a far-future manifest empties R5 and shows in the evidence, and `run --available-at` rejects a bad file. Added to `check.sh`.
- `fixtures/SPEC-GAPS.md`: G33 (OPEN), manifest validation corners.
- Merged `origin/main` (fast-forward to `3bf6b51`; Steven ran it). `reference/` stays outside the sparse checkout.

**Proof**
```
.venv/bin/python -m unittest -q pipeline/test_available_at.py pipeline/test_ingest.py pipeline/test_canon.py pipeline/test_dedup.py pipeline/test_replay.py
Ran 27 tests in 3.874s
OK
.venv/bin/python -m pipeline fixtures fixtures /tmp/pipeline_out
.venv/bin/python tools/compare_outputs.py fixtures fixtures /tmp/pipeline_out | grep -v '^ok ' | tail -2
27/27 fixtures equal
PASS
```

**Open**
- G33 (provisional choices above).
- The brief asks for `--available-at FILE` on `fixtures` too. I read that as the per-fixture `available_at.csv` (02 §8), and added no flag there, because one manifest shared by every fixture has no meaning. Steven to confirm.
- No verifier manifest fixtures yet (02 §8.3), so only the unit tests exercise this.
