#!/usr/bin/env bash
# Gate 2 evidence run (02-live-ingestion.md §9). Meant for CI only
# (.github/workflows/gate2.yml); tools/gate2_evidence.py refuses to write the
# evidence file anywhere else.
#
#   tools/gate2.sh FETCHER_ROOT LIVE_OUT WORK_DIR
#
# FETCHER_ROOT is a copy of the fetcher's root (fetch_log.csv, clock.csv,
# archive/). LIVE_OUT is the output of `python -m pipeline live` over the window,
# run with the cutoffs in tools/gate2_config.json. Runs every check, even after
# one fails, recording each exit code in WORK_DIR/checks.tsv; then writes
# evidence/delay-report.json and evidence/gate2.json. Exit code: 0 only if
# Gate 2 passes.
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-.venv/bin/python}"
ROOT="$1"; LIVE="$2"; W="$3"
mkdir -p "$W"
: > "$W/checks.tsv"
cfg() { "$PY" -c "import json,sys; c=json.load(open('tools/gate2_config.json')); print(*(c[sys.argv[1]] if isinstance(c[sys.argv[1]], list) else [c[sys.argv[1]]]))" "$1"; }
START=$(cfg window_start); END=$(cfg window_end)
C=(); for t in $(cfg cutoffs); do C+=(--cutoff "$t"); done
M="$W/available_at.csv"

check() {  # check NAME COMMAND...: run, log to WORK_DIR/NAME.log, record exit code
  local name=$1; shift
  echo "$(date +%H:%M:%S) $name"
  "$@" > "$W/$name.log" 2>&1
  printf '%s\t%s\n' "$name" "$?" >> "$W/checks.tsv"
}

check fixtures               ./check.sh
check fetch_log              "$PY" tools/fetch_log_check.py "$ROOT" "$START" "$END"
check archive_input          "$PY" tools/archive_input.py "$ROOT" "$W/input" "$M"
check reference_run          "$PY" reference/reference.py run "$W/input" "$START" "$END" "$W/reference" "${C[@]}" --available-at "$M"
check compare_reference_live "$PY" tools/compare_outputs.py dirs "$W/reference" "$LIVE"
check pipeline_replay        "$PY" -m pipeline run "$ROOT" "$START" "$END" "$W/replay" "${C[@]}" --archive --replay --available-at "$M"
check live_digest            cmp "$LIVE/canon_digest.csv" "$W/replay/canon_digest.csv"
check compare_live_replay    "$PY" tools/compare_outputs.py dirs "$LIVE" "$W/replay"
check delay_report           "$PY" tools/delay_report.py "$ROOT" evidence/delay-report.json

"$PY" tools/gate2_evidence.py "$ROOT" "$LIVE" "$W" evidence/gate2.json
