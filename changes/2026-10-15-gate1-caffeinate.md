# Gate 1 workflow: keep the Mac awake during the run

**File:** `.github/workflows/gate1.yml`

**What happened.** The first Gate 1 run, [38815747393](https://github.com/stevenrocca3/undercurrent/actions/runs/38815747393), failed with "The self-hosted runner lost communication with the server." No check had failed: fixtures had passed 27/27, and the reference run was 14 minutes into the month.

**Cause.** `pmset -g log` shows `18:28:56 Entering Sleep state due to 'Idle Sleep'` while on AC power. The system sleep setting is 1 minute. The load sampler has no samples between 18:29 and 18:44. The job's processes were stopped afterwards; nothing they wrote could be CI evidence.

**Fix.** `gate1.sh` now runs under `caffeinate -i`, which blocks idle system sleep for the life of the command only. The machine's power settings are unchanged. Closing the lid still sleeps a MacBook, so keep it open (and on power) during a run.
