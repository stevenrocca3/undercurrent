# Setup for Steven: the fetcher VM (02 §10, L8)

**For:** Steven. This is the one-time setup that step 4 of `briefs/pipeline-live-ingestion.md` needs. Allow about 20 minutes. Commands start with `!` so they run inside the Claude session; drop the `!` in a normal terminal.

**What you get:** one always-free `e2-micro` VM (2 shared vCPUs, 1 GB RAM, 30 GB standard disk) in a free-tier US region, with a $1 budget alert.

## Cost: read first

- **Free:** the e2-micro VM and the 30 GB standard disk, in `us-central1`, `us-west1` or `us-east1`. Downloads *into* the VM (ingress) are free.
- **Probably not free: the external IPv4 address.** Google bills in-use IPv4 addresses at about $0.005/hour (~$3.65/month) since February 2024, and the sources found don't confirm whether the free tier covers it. The VM needs outbound internet to reach `data.gharchive.org`. Step 6 checks the real bill after 48 h; if the IP is charged and you want $0, tell me and I'll write the IPv6-only variant.
- **Outbound traffic** (VM → internet, e.g. copying the archive to the Mac) is free for the first 1 GB/month, and costs a few cents per GB after that. 14 days of archive is about 9 GB, so copy it with `gcloud compute scp` once at the end, or plan on ~$1.
- **The budget alert only emails you; it does not stop spending.** To stop all compute cost, stop the VM (step 7).

## 1. Turn on billing for the project

This step needs a card on file. The sandbox project `genial-upgrade-511700-s1` has none.

1. console.cloud.google.com → **Billing** → **Link a billing account** → create one (card required).
2. Make sure it is linked to `genial-upgrade-511700-s1`. BigQuery stays inside its 1 TB/month free query allowance; leaving the sandbox only removes the sandbox limits.

## 2. The $1 budget alert

console.cloud.google.com → **Billing** → **Budgets & alerts** → **Create budget**:
- Scope: project `genial-upgrade-511700-s1`, all services.
- Amount: **Specified amount, $1**.
- Thresholds: 50%, 90% and 100% of actual spend, plus 100% of **forecasted** spend. Email goes to billing admins, which is you.

## 3. Create the VM

```
! ~/google-cloud-sdk/bin/gcloud services enable compute.googleapis.com
! ~/google-cloud-sdk/bin/gcloud compute instances create undercurrent-fetcher \
    --zone=us-central1-a --machine-type=e2-micro \
    --image-family=debian-12 --image-project=debian-cloud \
    --boot-disk-size=30GB --boot-disk-type=pd-standard
```

- **Keep these values:** `pd-standard` and 30 GB are the free disk; a balanced or SSD disk, or more than 30 GB, is billed.
- **Image:** if `debian-12` is gone by then, use the newest `debian-*` family that `gcloud compute images list --filter=family~debian` shows.

## 4. Check the clock and log in

```
! ~/google-cloud-sdk/bin/gcloud compute ssh undercurrent-fetcher --zone=us-central1-a --command "chronyc tracking | head -5; python3 --version; df -h /"
```

- `gcloud compute ssh` creates an SSH key the first time; accept the prompts.
- **Clock:** GCE VMs sync time from Google's metadata server through `chrony` by default. `System time` should be well under a millisecond, and 02 §4 wants that offset recorded.
- **Python:** Debian 12 ships Python 3.11. Whether the fetcher needs anything newer is the pipeline agent's call in step 4.

## 5. Hand over to the pipeline agent

Tell it: *"The VM is up: `undercurrent-fetcher`, zone `us-central1-a`, reach it with `~/google-cloud-sdk/bin/gcloud compute ssh undercurrent-fetcher --zone=us-central1-a`. Do step 4 of `briefs/pipeline-live-ingestion.md`. Contact address for the User-Agent: <your email>."*

Choose the address you're happy for GH Archive's operators to see.

## 6. After 48 hours: check the real cost

console.cloud.google.com → **Billing** → **Reports**. Filter by project, group by **SKU**, and look at the last 2 days. Expect $0.00 for `E2 Micro` and `Storage PD Capacity`. If `External IP` shows a charge, it is the ~$3.65/month IPv4 fee; see Cost above.

## 7. Stopping and deleting

- **Stop (keeps the disk, stops compute):** `gcloud compute instances stop undercurrent-fetcher --zone=us-central1-a`
- **Delete everything (after Gate 2 and after copying the archive off):** `gcloud compute instances delete undercurrent-fetcher --zone=us-central1-a`

Sources for the cost notes: [DoIT on external IP charges](https://www.doit.com/blog/no-more-free-external-ips-on-google-cloud-how-much-will-it-cost-you), [Google VPC external IP pricing notice](https://cloud.google.com/vpc/pricing-announce-external-ips), [Google community thread on e2-micro free tier charges](https://discuss.google.dev/t/charged-95-for-compute-engine-e2-micro-despite-free-tier-usage/192936).
