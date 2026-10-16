# Brief: pipeline author: the Gate 2 live run

**From:** Steven (owner). Drafted 2026-10-16 by the scrum master from the specs only.
**For:** the pipeline agent.
**Spec:** `02-live-ingestion.md` v0.8 (§6, §7, §9) and `01-event-semantics.md` v0.13. They are authoritative. If this brief and the specs disagree, the specs win; tell the scrum master.
**Follows:** `briefs/pipeline-live-ingestion.md` step 4. The fetcher runs on the VM under systemd (`undercurrent-fetcher.service`, since 2026-10-16 06:01Z). This brief adds the half that step left open: "the pipeline itself runs on the Mac from a copy of the archive".

## Why

Gate 2 criterion 2 (02 §9) needs live tables over the whole window, made **while the window runs**, which `tools/gate2.sh` then compares to a replay of the archive. Nothing produces them yet.

## Fixed inputs (decided; don't change them)

- **Window:** hours `2026-10-16T06:00:00Z` → `2026-10-30T05:00:00Z` (02 §7, v0.7).
- **R5 cutoffs (G36, 02 §9):** the 8 values in `tools/gate2_config.json` (daily 06:00Z, 2026-10-23 → 30). Pass every one as `--cutoff`.
- **Paths:** the Gate 2 workflow (`.github/workflows/gate2.yml`) reads them, so use exactly these:
  - the fetcher-root copy: `~/undercurrent-data/fetcher/`
  - the live output: `~/undercurrent-data/live/`

## What to build

1. **Sync:** copy the VM's fetcher root (`opc@150.136.138.5:/home/opc/undercurrent-data/fetcher/`, key `~/.ssh/undercurrent_oci`) to `~/undercurrent-data/fetcher/` every few minutes. Use a launchd agent or similar that survives logout and reboot.
   - **Never delete in the copy.** The archive is append-only (02 §5.1), and the Gate 2 workflow rsyncs into the same folder.
   - **The copy must never show a fetch-log row whose file is not there yet.** A plain rsync can copy `fetch_log.csv` after newer archive files, or before them. Make the order safe, and test it.
   - **The VM has 498 MiB of RAM.** Read-only access only: no `dnf`, no restarts, nothing that touches the fetcher service or the VM archive.
2. **Live run:** `python -m pipeline live ~/undercurrent-data/fetcher 2026-10-16T06:00:00Z 2026-10-30T05:00:00Z ~/undercurrent-data/live` with the 8 cutoffs, kept running until LAST is done. Every hour is final by 2026-10-31T06:00Z at the latest.
   - **Mac sleep** only delays it: `available_at` comes from the fetch log, not the Mac's clock. Prevent idle sleep the way the Gate 1 runner did (`caffeinate -i`), so it keeps up.
   - **If it dies,** your live-mode note says there's no resume. Clear the output and start again from the copy. It catches up by §8.1. Record each restart in the change note.
   - **Leave the output folder alone** until the run is done, apart from such a restart.

## Checks before reporting

- The sync ran at least twice. `tools/fetch_log_check.py ~/undercurrent-data/fetcher 2026-10-16T06:00:00Z <last final hour>` reports 0 problems. It's a shared tool; run it, don't read it.
- `pipeline live` has caught up to the latest final hour and is waiting on the next one.
- **BENCHMARKS rows:** catch-up time and max RSS for the first run, whether the Mac was idle, and how it was measured.

## Not yours

- The VM, the fetcher service, the window dates and the cutoffs (Steven).
- `tools/gate2.sh` and the Gate 2 workflow. If one of them doesn't fit how live writes its output, report it; don't edit it.

## Reporting

- Same rules as before: a change note, BENCHMARKS rows, and a report of 10 lines or fewer to the scrum master (SendMessage, or via Steven).
- **Stop** once the sync and the live run are running and checked. After that, report only if the live run dies or the sync falls behind by more than an hour.
