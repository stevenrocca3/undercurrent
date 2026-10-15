# Gate 1 tooling: evidence run (criterion 6) and source reconciliation (criterion 4)

**Files:** `tools/reconcile.py`, `tools/bigquery/{type_by_hour,ids_by_hour,stars}.sql`, `tools/gate1.sh`, `tools/gate1_evidence.py`, `tools/gate1_config.json`, `.github/workflows/gate1.yml`, `tools/test_reconcile.py`, `tools/test_gate1_evidence.py` (all new), `check.sh` (runs the two new test files).

All of it is neutral tooling in `tools/`. None of it imports pipeline or reference code; it only reads output CSVs and runs the CLIs. §6 independence holds.

## Criterion 4: `tools/reconcile.py` + `tools/bigquery/*.sql`

- **Queries.** Three BigQuery queries, one per §5.2 metric, over `githubarchive.day.2026*`, suffixes `0901`–`0930`:
  - event count by (hour, type)
  - distinct ids by hour
  - star events by (repo, date) for the top 1,000 repos (ties go to the smaller `repo_id`)
- **Hours.** BigQuery has no source-file hour, so `hour` is `created_at` truncated to the hour.
- **`reconcile.py`.** It compares those exports with our `r2`/`r4`/`registry` over the union of keys. Distinct ids by hour is `r2` summed over types, since `r2` counts one kept row per event_id.
- **Tolerance.** ≤ 0.1% (OPEN-3). A cell where `theirs = 0` and `ours ≠ 0` is out.
- **Categories.** Each out-of-tolerance cell gets one category, first match wins:
  1. A human finding in `evidence/reconciliation-categories.csv` (`metric,key,category,reason`). The reason is copied into the report.
  2. `missing_hour_ours`: our registry says the hour is not `present`.
  3. `missing_hour_theirs`: BigQuery has nothing in that hour.
  4. Otherwise `unexplained`.

  `dedup_policy`, `parse_or_schema` and `time_bucketing` are only ever assigned by a person who looked. The tool never guesses them, so it can't hide a real difference.
- **Output.** `reconciliation.csv` (every cell) and `reconciliation.json` (counts and pass). Exit 0 only when no cell is `unexplained`.

## Criterion 6: `.github/workflows/gate1.yml` → `tools/gate1.sh` → `tools/gate1_evidence.py`

- **Trigger and runner.** `workflow_dispatch` only, on a **self-hosted** runner. A month (19 GB gzip plus working space) does not fit on a hosted runner. The job has a 6 h timeout.
- **`gate1.sh`.**
  - Downloads missing hours to `.part` files and renames each only on success. That stops a partial download from looking complete, which is what happened to `2026-09-06-20`.
  - Runs every check even if an earlier one fails: fixtures (`check.sh`), reference, pipeline batch, reference = batch, pipeline `--replay`, `canon_digest.csv` equality, batch = replay, BigQuery export, reconcile.
  - Records each exit code in `checks.tsv`.
- **`gate1_evidence.py`.** Writes `evidence/gate1.json`. It **refuses to run unless `GITHUB_ACTIONS=true`** and records the run URL. The file contains:
  - the commit SHA
  - the config hash
  - the input manifest: 720 file names with SHA-256, `null` if missing
  - every check's exit code
  - the reconciliation summary
  - a pass/fail per criterion, with criteria 1–6 mapped to checks, and an overall pass
- **What criterion 5 needs.** It passes when `registry.csv` lists exactly the 720 window hours.
- **Upload.** The evidence file, logs and reconciliation files are uploaded as the `gate1-evidence` artifact.
- **Config hash (my definition; the spec doesn't define one).** It is the SHA-256 over the hashes of the files that define the run: `tools/gate1_config.json` (window, 24 cutoffs, source URL), the spec, `requirements.txt` and the three SQL files. The per-file hashes are in the evidence too.

## Refactor

- **One config file.** The window and cutoffs now live only in `tools/gate1_config.json`. They used to be retyped in each ad-hoc month command.
- **One file-name rule.** The hour → file name rule is defined once, as `gate1_evidence.hour_file`, and `gate1.sh` uses it too.
- **Month runs.** Future month comparisons can run `tools/gate1.sh` instead of a one-off command line. Only the evidence-writing step at the end needs CI.

## Tests

`test_reconcile.py` (6 tests) covers:
- a cell inside tolerance
- the top-repo restriction
- an unexplained cell failing the run
- theirs = 0
- `missing_hour_ours`
- a manual category taking priority, and an unknown category being rejected

`test_gate1_evidence.py` (6 tests) covers:
- 720 hours in the window
- all checks passing
- one failed check failing its criterion
- a missing check, and a run outside CI
- an incomplete registry
- refusing to run outside CI

12 tests, all OK. Both files are added to `check.sh`.

## Needs from Steven before the first Gate 1 run

1. **Google Cloud.** Install the Cloud SDK (`brew install --cask google-cloud-sdk`), run `gcloud auth login`, and set a project. First run `bq query --dry_run` on `tools/bigquery/stars.sql` to see the bytes scanned: the `payload` column dominates, and the free tier is 1 TB a month.
2. **Self-hosted runner.** Register this Mac under repo Settings → Actions → Runners → New self-hosted runner (macOS, ARM64), and run it while Gate 1 runs.
3. **Start it.** Actions → gate1 → Run workflow. Expect about 2 h: reference ~48 min, batch ~13–20 min, replay longer, plus the queries.

## Also verified: the pipeline's digest fix on the month

- **Output.** The pipeline at `f5bf11d` (digest per hour, merged in #18) ran on the complete month with the 24 cutoffs. `compare_outputs.py dirs` against the clean run's reference output: **PASS**, all 7 files equal. `canon_digest.csv` is byte-identical to the `7017a34` run, so the fix changed only the speed.
- **Time.** 989.47 s with a peak of 1,565 MB. That is down from 1,268.52 s at `7017a34`, but still above the 771.84 s at `df52f20`. The machine was **not idle**: the 1-minute load average, sampled every 30 s, had a median of 32.6 and a max of 95.3 on 8 cores, far above the pipeline's own ~8 workers. So the gap to 771.84 s can't be attributed to the code yet. The next timing needs an idle machine. The Gate 1 CI run provides one if nothing else is running on the Mac.
- **Reconciliation at full size.** `reconcile.py` ran on the real month outputs against a stand-in "theirs" built from the reference's own `r2`/`r4`. It checked 30,498 cells (type_by_hour 11,009, ids_by_hour 720, stars 18,769) in 0.79 s: 0 out of tolerance, pass. That proves only that it runs at scale and that the key formats line up. The real BigQuery exports are still to come.
- **`./check.sh`.** Passes: 33 tool tests, 27/27 fixtures for the reference, 21 pipeline tests, 27/27 fixtures for the pipeline.

Run outputs: `~/undercurrent-data/runs/2026-09-month-pipe-f5bf11d/` (including `load.log`).

## Follow-up: Google Cloud CLI install

`brew install --cask google-cloud-sdk` failed on this Mac. macOS 14 is Homebrew Tier 3, so it tried to compile `python@3.13` from source, and that failed on a missing `CarbonCore/Folders.h` in the Command Line Tools SDK. Instead the CLI was installed from Google's official archive (`google-cloud-cli-darwin-arm.tar.gz`) into `~/google-cloud-sdk`, with its bundled Python: gcloud 589.0.0, bq 2.1.40. A runner doesn't read `~/.zshrc`, so `gate1.yml` now adds `~/google-cloud-sdk/bin` to the job's PATH.

## Follow-up: BigQuery dry runs and a bq fix

- **Project.** BigQuery sandbox project `genial-upgrade-511700-s1`. Billing is disabled, so it cannot be charged, and the free query allowance is 1 TB a month.
- **Dry runs.** The dry runs are free. type_by_hour scans 1,143,645,956 B, ids_by_hour 1,147,906,704 B and stars 72,920,720,046 B, about 75 GB in total, or 7.5% of the monthly allowance.
- **Fix.** `gate1.sh` had passed each query to `bq` as an argument, where the SQL's leading `--` comment is read as a flag (`FATAL Flags parsing error`). It now feeds the query on stdin.
- **PATH.** `bq` also needs `gcloud` on PATH to authenticate. `gate1.yml` already adds it.
