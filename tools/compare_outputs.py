"""Exact-equality comparison of output CSVs (01-event-semantics.md §6, §8).

Two modes:

    python tools/compare_outputs.py dirs EXPECTED_DIR ACTUAL_DIR
        Compare one set of outputs, e.g. reference_out/ vs pipeline_out/.

    python tools/compare_outputs.py fixtures FIXTURES_DIR ACTUAL_ROOT
        For every fixture FIXTURES_DIR/Fxx-*/expected/, compare against
        ACTUAL_ROOT/Fxx-*/ (the outputs produced from that fixture's input/).

Rules:
- The files compared are r1..r5, registry, flags (R1-R7). Each must exist on
  both sides. Extra files in ACTUAL are listed, not failed.
- Headers must match exactly.
- Rows are compared as exact text after sorting both sides (byte order), so
  row order never matters; cell text does ("7" != "07", no trimming).
- Line endings must be LF. A CR anywhere fails the file.
- No tolerance, no fuzzy matching. Exit code 0 = all equal, 1 = any difference,
  2 = usage error.

Standard library only. Must not import anything from the pipeline codebase.
"""

import sys
from pathlib import Path

OUTPUT_FILES = ["r1.csv", "r2.csv", "r3.csv", "r4.csv", "r5.csv", "registry.csv", "flags.csv"]
MAX_ROWS_SHOWN = 10


def read_csv_lines(path):
    """Return (header, rows) as raw text lines, or raise ValueError on a format violation."""
    data = path.read_bytes()
    if b"\r" in data:
        raise ValueError("contains CR; line endings must be LF")
    text = data.decode("utf-8")
    if text == "":
        raise ValueError("empty file; a header row is required")
    if not text.endswith("\n"):
        raise ValueError("last line has no trailing LF")
    lines = text[:-1].split("\n")
    return lines[0], lines[1:]


def compare_file(expected_path, actual_path):
    """Return a list of problem strings; empty means equal."""
    if not actual_path.exists():
        return ["missing in actual"]
    try:
        exp_header, exp_rows = read_csv_lines(expected_path)
    except ValueError as e:
        return [f"expected file invalid: {e}"]
    try:
        act_header, act_rows = read_csv_lines(actual_path)
    except ValueError as e:
        return [f"actual file invalid: {e}"]

    problems = []
    if exp_header != act_header:
        problems.append(f"header differs: expected {exp_header!r}, actual {act_header!r}")

    exp_sorted, act_sorted = sorted(exp_rows), sorted(act_rows)
    if exp_sorted != act_sorted:
        only_exp = multiset_minus(exp_sorted, act_sorted)
        only_act = multiset_minus(act_sorted, exp_sorted)
        problems.append(f"rows differ: {len(only_exp)} only in expected, {len(only_act)} only in actual")
        for row in only_exp[:MAX_ROWS_SHOWN]:
            problems.append(f"  - {row}")
        for row in only_act[:MAX_ROWS_SHOWN]:
            problems.append(f"  + {row}")
        hidden = max(0, len(only_exp) - MAX_ROWS_SHOWN) + max(0, len(only_act) - MAX_ROWS_SHOWN)
        if hidden:
            problems.append(f"  ... {hidden} more")
    return problems


def multiset_minus(a, b):
    """Rows of sorted list a not matched by a row of sorted list b (duplicates counted)."""
    out, j = [], 0
    for row in a:
        while j < len(b) and b[j] < row:
            j += 1
        if j < len(b) and b[j] == row:
            j += 1
        else:
            out.append(row)
    return out


def compare_dirs(expected_dir, actual_dir, label=""):
    """Compare all output files; print a report. Return True if all equal."""
    ok = True
    prefix = f"{label}: " if label else ""
    for name in OUTPUT_FILES:
        exp_path = expected_dir / name
        if not exp_path.exists():
            print(f"FAIL {prefix}{name}: missing in expected ({expected_dir})")
            ok = False
            continue
        problems = compare_file(exp_path, actual_dir / name)
        if problems:
            ok = False
            print(f"FAIL {prefix}{name}: {problems[0]}")
            for p in problems[1:]:
                print(f"     {p}")
        else:
            print(f"ok   {prefix}{name}")
    if actual_dir.is_dir():
        extra = sorted(p.name for p in actual_dir.glob("*.csv") if p.name not in OUTPUT_FILES)
        if extra:
            print(f"note {prefix}extra files in actual, not compared: {', '.join(extra)}")
    return ok


def compare_fixtures(fixtures_dir, actual_root):
    fixture_dirs = sorted(p for p in fixtures_dir.iterdir() if (p / "expected").is_dir())
    if not fixture_dirs:
        print(f"FAIL no fixtures with expected/ found in {fixtures_dir}")
        return False
    failed = []
    for fx in fixture_dirs:
        if not compare_dirs(fx / "expected", actual_root / fx.name, label=fx.name):
            failed.append(fx.name)
    print()
    print(f"{len(fixture_dirs) - len(failed)}/{len(fixture_dirs)} fixtures equal")
    for name in failed:
        print(f"  failed: {name}")
    return not failed


def main(argv):
    if len(argv) != 4 or argv[1] not in ("dirs", "fixtures"):
        print(__doc__, file=sys.stderr)
        return 2
    mode, a, b = argv[1], Path(argv[2]), Path(argv[3])
    if not a.is_dir():
        print(f"not a directory: {a}", file=sys.stderr)
        return 2
    ok = compare_dirs(a, b) if mode == "dirs" else compare_fixtures(a, b)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
