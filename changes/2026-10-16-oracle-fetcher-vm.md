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
- ~~Idle reclaim (guide step 7)~~ **Decided 2026-10-16:** Steven upgraded to Pay As You Go, so idle reclaim no longer applies. The budget is $1 a month, with an email alert at 50% ($0.50). The bill still has to be checked after 48 h (guide step 8).
- **The VM (built 2026-10-16):**
  - Setup: `VM.Standard.E2.1.Micro` in us-ashburn-1 AD-1 (A1 was out of capacity), Oracle Linux 9.8, user `opc`, 498 MiB RAM, 30 GB root.
  - Clock: synchronized to Oracle NTP, offset 0.000000619 s (recorded in `BENCHMARKS.md`).
  - **Incident:** my `dnf check-update` ran it out of memory, and SSH timed out until Steven rebooted it from the console. `dnf-makecache.timer` is now disabled so this can't recur during the window.
  - **Trade-off:** security updates are now manual and must happen outside the window.
- **Python on the VM:** 3.9.25 (OL9 default). Whether the fetcher needs a newer one, and how to install it on this little memory, is the pipeline agent's call at step 4.
