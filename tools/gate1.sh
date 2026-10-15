#!/usr/bin/env bash
# Gate 1 evidence run (01-event-semantics.md §8). Meant for CI only
# (.github/workflows/gate1.yml); tools/gate1_evidence.py refuses to write the
# evidence file anywhere else.
#
#   tools/gate1.sh INPUT_DIR WORK_DIR
#
# Downloads any missing hour of the window into INPUT_DIR, then runs every
# check, even after one fails, recording each exit code in WORK_DIR/checks.tsv;
# then writes evidence/gate1.json. Exit code: 0 only if Gate 1 passes.
set -uo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-.venv/bin/python}"
IN="$1"; W="$2"
mkdir -p "$IN" "$W/bigquery"
: > "$W/checks.tsv"
cfg() { "$PY" -c "import json,sys; c=json.load(open('tools/gate1_config.json')); print(*(c[sys.argv[1]] if isinstance(c[sys.argv[1]], list) else [c[sys.argv[1]]]))" "$1"; }
START=$(cfg window_start); END=$(cfg window_end); SRC=$(cfg source)
C=(); for t in $(cfg cutoffs); do C+=(--cutoff "$t"); done

# Fetch to .part and rename only on success, so a dropped connection never
# leaves a partial file that looks complete (it happened once: 2026-09-06-20).
for f in $("$PY" -c "
import sys; sys.path.insert(0, 'tools'); from gate1_evidence import hours, hour_file
print(*map(hour_file, hours('$START', '$END')))"); do
  [ -s "$IN/$f" ] || { curl -sf --retry 3 -o "$IN/$f.part" "$SRC/$f" && mv "$IN/$f.part" "$IN/$f"; } || echo "not downloaded: $f"
done

check() {  # check NAME COMMAND...: run, log to WORK_DIR/NAME.log, record exit code
  local name=$1; shift
  echo "$(date +%H:%M:%S) $name"
  "$@" > "$W/$name.log" 2>&1
  printf '%s\t%s\n' "$name" "$?" >> "$W/checks.tsv"
}
bq_export() {  # run each tools/bigquery/*.sql into WORK_DIR/bigquery/*.csv
  # On stdin: as an argument, the SQL's leading "--" comment parses as a bq flag.
  for q in type_by_hour ids_by_hour stars; do
    bq query --nouse_legacy_sql --format=csv --max_rows=1000000 < "tools/bigquery/$q.sql" > "$W/bigquery/$q.csv" || return 1
  done
}

check fixtures                ./check.sh
check reference_run           "$PY" reference/reference.py run "$IN" "$START" "$END" "$W/reference" "${C[@]}"
check pipeline_batch          "$PY" -m pipeline run "$IN" "$START" "$END" "$W/pipeline" "${C[@]}"
check compare_reference_batch "$PY" tools/compare_outputs.py dirs "$W/reference" "$W/pipeline"
check pipeline_replay         "$PY" -m pipeline run "$IN" "$START" "$END" "$W/replay" "${C[@]}" --replay
check replay_digest           cmp "$W/pipeline/canon_digest.csv" "$W/replay/canon_digest.csv"
check compare_batch_replay    "$PY" tools/compare_outputs.py dirs "$W/pipeline" "$W/replay"
check bigquery                bq_export
CATS=(); [ -f evidence/reconciliation-categories.csv ] && CATS=(--categories evidence/reconciliation-categories.csv)
check reconcile               "$PY" tools/reconcile.py "$W/pipeline" "$W/bigquery" "$W/reconcile" ${CATS[@]+"${CATS[@]}"}

"$PY" tools/gate1_evidence.py "$IN" "$W" evidence/gate1.json
