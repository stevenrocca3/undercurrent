#!/usr/bin/env bash
# One command for every repeatable check: comparator tests, then the reference
# on all fixtures, then compare against the expected outputs, then the
# pipeline's own tests.
# Uses .venv's Python (DuckDB); set PYTHON to override, e.g. in CI.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-.venv/bin/python}"
if [ ! -x "$PY" ] && ! command -v "$PY" >/dev/null; then
  echo "No Python at $PY. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 2
fi

out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

"$PY" -m unittest tools/test_compare_outputs.py
"$PY" reference/reference.py fixtures fixtures "$out"
"$PY" tools/compare_outputs.py fixtures fixtures "$out"
"$PY" -m unittest pipeline/test_ingest.py
