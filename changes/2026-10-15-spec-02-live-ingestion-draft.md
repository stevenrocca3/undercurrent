# Spec 02 draft: live ingestion

**File:** `02-live-ingestion.md` (new, Draft v0.1). Nothing else changes until it is approved. §11 lists the edits to 01 that come with approval.

**Why now.** Gate 1 has passed. 01 §1 and §4 already point at live ingestion: an `http_status` column, an observed `available_at`, and replacing `L = 6h` with a measured p99. Nothing defined how any of that works.

**What it defines:**
- **Fetch schedule** (§3): first attempt at the due time `h+1h`, poll every `P` minutes, `missing` after `D` hours.
- **Success** (§4): HTTP 200, full body, temp-file-then-rename, decodes as `present`. That is when `available_at` is stamped.
- **Records** (§5): the archive, an append-only fetch log, and the registry evidence columns.
- **Ingestion** (§6): the existing replay mode, fed in strict hour order. A republished file never rewrites what is already ingested.
- **Delay measurement** (§7): 28 days, with p99 rounded up becoming the new `L`.
- **Verification** (§8): live = replay; pipeline = reference given an `available_at` manifest; new fixtures; fetch log consistency.
- **Gate 2** (§9): 6 criteria, mirroring Gate 1.
- **Host** (§10): recommends an always-free cloud VM. The laptop idle-slept during Gate 1, and GitHub's scheduler would add its own delay to the measurement.

**Lessons from Gate 1 written in:**
- download to a temp file, then rename (`2026-09-06-20` was a partial download)
- the host must not sleep (run 38815747393)
- R5 depends on `L`, so Gate 1 is re-run after `L` changes

**Open for Steven:** OPEN-L1 to L8 (§12). Each has a recommendation.
