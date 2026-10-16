# Fetcher VM moves from Google Cloud to Oracle Cloud (02 v0.5)

**Why:** Google's billing flagged Steven's card as possible fraud, so the GCP `e2-micro` plan (02 §10, L8) couldn't be set up. Steven compared Oracle, Azure and AWS and chose **Oracle Cloud Always Free**:
- A Free Tier account there can't be billed unless it is upgraded to Pay As You Go.
- Its free VM (up to 4 ARM cores / 24 GB, 200 GB disk) is larger than GCP's.
- Steven has created the account (2026-10-16).

**What changed:**
- `briefs/steven-fetcher-vm-setup.md`: rewritten for Oracle.
  - Steps: budget alert, region, SSH key, Always Free VM (`VM.Standard.A1.Flex` 1 OCPU / 6 GB, Ubuntu 24.04, fallback `E2.1.Micro`), clock check, handover, idle-reclaim decision, cost check, teardown.
- `02-live-ingestion.md` v0.5, §10 and L8:
  - The provider is now Oracle; the decision itself (an always-free cloud VM with a $1 budget alert) is unchanged.
  - Notes Oracle's idle-reclaim rule.
- `briefs/pipeline-live-ingestion.md`: step 4 names the Oracle Ubuntu VM.
- `changes/README.md`: removed a duplicated G33 line and filled in #30 for agents-md (tidy).

**Proof:** documentation only. `./check.sh` was not affected (no code changed).

**Open:**
- **Idle reclaim (guide step 7):** Oracle can stop a VM that's idle for 7 days. Steven decides before the 14-day window whether to upgrade to Pay As You Go to avoid it. Recommendation: upgrade, with the budget alert in place.
- **Clock offset:** to be recorded from guide step 5 once the VM exists (02 §4).
