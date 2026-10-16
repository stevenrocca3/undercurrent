# Setup for Steven: the fetcher VM on Oracle Cloud (02 §10, L8)

**For:** Steven. This is the one-time setup that step 4 of `briefs/pipeline-live-ingestion.md` needs. Allow about 30 minutes. Everything except steps 3 and 5 happens in the Oracle web console (cloud.oracle.com). Commands starting with `!` run inside the Claude session; drop the `!` in a normal terminal.

**What you get:** one Always Free VM running Ubuntu, with an SSH key that only your Mac has, and a $1 budget alert.

## Cost: read first

- **The rule:** a Free Tier account **cannot be billed unless you click "Upgrade to Pay As You Go."** If you do nothing after the 30-day trial, you keep the Always Free services.
- **The trap is the $300 trial credit.** For the first 30 days it lets you create paid resources without warning. Anything not Always Free is stopped at day 30 and later deleted, so a paid VM would vanish in the middle of the 14-day window.
  - **Only choose options labelled "Always Free-eligible."**
- **Always Free limits that matter here:**
  - Ampere A1 (ARM): 4 OCPUs and 24 GB RAM in total.
  - or up to two `VM.Standard.E2.1.Micro` (AMD) VMs.
  - 200 GB of block storage in total, boot volumes included.
  - 10 TB of outbound traffic a month.
  - Our needs: about 9 GB of archive over 14 days, and a few kB per poll.
- **Idle reclaim:** Oracle can stop an Always Free VM that is idle over 7 days (95th-percentile CPU, network, and on A1 memory, all under 20%). The fetcher is that idle. See step 7: this is a decision to make **before** the 14-day window starts, not now.

## 1. The $1 budget alert

On a Free Tier account it should never fire. It is a tripwire in case something paid gets created.

1. Console menu → **Billing & Cost Management** → **Budgets** → **Create Budget**.
2. Fill in:
   - **Target:** compartment, the root compartment (your tenancy name).
   - **Schedule:** monthly.
   - **Amount:** 1.
3. Alert rule:
   - **Type:** Actual spend.
   - **Threshold:** 100% of the budget.
   - **Email:** your address.
4. Add a second alert rule, **Forecast spend**, at 100%.

## 2. Check your region

The home region was fixed at signup. Top bar → region name. Tell me which one it is; it doesn't change anything below.

## 3. Make an SSH key on the Mac

```
! ssh-keygen -t ed25519 -f ~/.ssh/undercurrent_oci -N "" -C undercurrent-fetcher
! cat ~/.ssh/undercurrent_oci.pub
```

You'll paste the `.pub` line (the public half) into Oracle. The private file `~/.ssh/undercurrent_oci` never leaves the Mac.

## 4. Create the VM

Console menu → **Compute** → **Instances** → **Create instance**.

**Basics**
- **Name:** `undercurrent-fetcher`.
- **Placement:** leave the availability domain as is.
  - If you get **"Out of capacity,"** try another availability domain.
  - If none works, use the AMD shape below.

**Image and shape**
- **Image:** Change image → **Canonical Ubuntu** → **24.04** (the plain one, not Minimal).
- **Shape:** Change shape → **Ampere** → `VM.Standard.A1.Flex` → **1 OCPU, 6 GB memory**. It must show **Always Free-eligible**.
  - **Fallback:** Specialty and previous generation → `VM.Standard.E2.1.Micro`, also Always Free-eligible.
  - One OCPU is plenty, and it leaves the rest of the free allowance unused.

**Networking**
- **Create new virtual cloud network** and **Create new public subnet**, with the defaults.
- **Automatically assign public IPv4 address:** on. This is free on Oracle.

**SSH keys:** **Paste public keys** → paste the line from step 3.

**Boot volume:** leave the default size (about 47 GB). Don't tick "Specify a custom size" above 200 GB, and don't enable "in-transit encryption" or anything marked paid.

**Create.** Wait for the state to become **Running**, then copy its **Public IP address**.

## 5. Log in and check the clock

Replace `IP` with the public IP:

```
! ssh -i ~/.ssh/undercurrent_oci -o StrictHostKeyChecking=accept-new ubuntu@IP "timedatectl; chronyc tracking 2>/dev/null | head -5; python3 --version; df -h /; nproc; free -h"
```

- **Clock:** `System clock synchronized: yes` is required. 02 §4 wants the offset recorded, so paste me the output.
  - If it says `no`, tell me before going further.
- **Python:** Ubuntu 24.04 ships 3.12. Whether the fetcher needs anything newer is the pipeline agent's call in step 4.
- **Updates:** Ubuntu installs security updates automatically (`unattended-upgrades`). Inbound access is SSH only, by key.

## 6. Hand over to the pipeline agent (later, at its step 4)

Tell it: *"The VM is up: `ssh -i ~/.ssh/undercurrent_oci ubuntu@IP` (Ubuntu 24.04, Oracle Always Free). Do step 4 of `briefs/pipeline-live-ingestion.md`. Contact address for the User-Agent: <your email>."*

Choose the address you're happy for GH Archive's operators to see.

## 7. Before the 14-day window: idle reclaim

Oracle may stop an idle Always Free VM after 7 days, which would put a gap in the measurement. Choose one before the window starts:

| | Stay on Free Tier | Upgrade to Pay As You Go |
|---|---|---|
| Can you be billed? | no | only for non-Always-Free resources; the budget alert catches any within a day |
| Idle reclaim | can happen | does not apply |
| Gaps | a reclaim stops the VM; the gap shows as late `available_at` (02 §9) and the window has to restart | none from Oracle |

**My recommendation: upgrade just before the window,** with the budget alert from step 1 in place, and check the bill after 48 hours (step 8). A reclaim at day 8 would cost a week of measurement. Upgrading may put a small temporary hold on the card.

## 8. After 48 hours: check the real cost

Billing & Cost Management → **Cost Analysis** → last 7 days, grouped by service. Expect **0.00**. Anything else, tell me with the service name.

## 9. Stopping and deleting

- **Stop:** Compute → Instances → `undercurrent-fetcher` → **Stop**. The disk is kept.
- **Delete everything** (after Gate 2, and after copying the archive off): Instance → **Terminate**, tick **Permanently delete the attached boot volume**.
