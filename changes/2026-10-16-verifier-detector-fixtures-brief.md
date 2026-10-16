# Brief: verifier detector fixtures (03 §8)

**Why:** Steven asked for the verifier to start the detector fixtures while Gate 2 runs. Fixtures written against the draft are also the first real test of 03's wording, before v1.0.

**What:** `briefs/verifier-detector-fixtures.md`.
- **Location:** `fixtures/detector/Dnn-*`, so the 01 runners don't pick them up.
- **Format:** `fixture.json` gives a requested range plus cutoffs. Every hour with events is pinned in `available_at.csv`, so the expected outputs don't change when Gate 2 changes `L`.
- **Expected outputs:** `features.csv` and `labels.csv` only (03 §8, S12).
- **Cases:** 11, covering 03 §8's list plus S3, S7 thresholds, S8, S9 near-misses, S13 and no survivorship.
- **Where 03 is silent:** the verifier opens a gap from G37 on.

**Where it lives:** PR #42, with the draft spec. The verifier needs 03 on `main`, so Steven merges #42 as a draft (the file's status says "not approved"), or the verifier works from branch `spec-03`.
