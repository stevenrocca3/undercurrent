"""Tests for compare_outputs.py. Run: python -m unittest tools/test_compare_outputs.py"""

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compare_outputs as co  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "fixtures"


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = co.main(argv)
    return code, buf.getvalue()


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.exp = self.tmp / "exp"
        self.act = self.tmp / "act"
        shutil.copytree(FIXTURES / "F12-point-in-time-trap" / "expected", self.exp)
        shutil.copytree(self.exp, self.act)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def dirs(self):
        return run(["x", "dirs", str(self.exp), str(self.act)])

    def test_identical_passes(self):
        code, out = self.dirs()
        self.assertEqual(code, 0, out)

    def test_row_order_ignored(self):
        p = self.act / "r5.csv"
        header, *rows = p.read_text().splitlines()
        p.write_text("\n".join([header] + rows[::-1]) + "\n")
        self.assertEqual(self.dirs()[0], 0)

    def test_changed_count_fails_and_shows_rows(self):
        p = self.act / "r5.csv"
        p.write_text(p.read_text().replace("2026-09-01T08:00:00Z,501,2", "2026-09-01T08:00:00Z,501,3"))
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("- 2026-09-01T08:00:00Z,501,2", out)
        self.assertIn("+ 2026-09-01T08:00:00Z,501,3", out)

    def test_extra_row_fails(self):
        with open(self.act / "r4.csv", "a") as f:
            f.write("999,2026-09-01,1\n")
        self.assertEqual(self.dirs()[0], 1)

    def test_duplicated_row_fails(self):
        p = self.act / "r4.csv"
        lines = p.read_text().splitlines()
        p.write_text("\n".join(lines + [lines[1]]) + "\n")
        self.assertEqual(self.dirs()[0], 1)

    def test_missing_file_fails(self):
        (self.act / "flags.csv").unlink()
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("flags.csv: missing in actual", out)

    def test_header_difference_fails(self):
        p = self.act / "r3.csv"
        p.write_text(p.read_text().replace("conflict_count", "conflicts"))
        self.assertEqual(self.dirs()[0], 1)

    def test_crlf_fails(self):
        p = self.act / "r1.csv"
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("CR", out)

    def test_no_trailing_newline_fails(self):
        p = self.act / "r1.csv"
        p.write_bytes(p.read_bytes().rstrip(b"\n"))
        self.assertEqual(self.dirs()[0], 1)

    def test_cell_text_is_exact(self):
        p = self.act / "r3.csv"
        p.write_text(p.read_text().replace("8,0,0", "08,0,0"))
        self.assertEqual(self.dirs()[0], 1)

    def test_header_only_files_pass(self):
        for d in (self.exp, self.act):
            (d / "r4.csv").write_text("repo_id,event_date,star_events\n")
        code, out = self.dirs()
        self.assertEqual(code, 0, out)

    def test_header_only_vs_rows_fails(self):
        (self.act / "r4.csv").write_text("repo_id,event_date,star_events\n")
        self.assertEqual(self.dirs()[0], 1)

    def test_zero_byte_file_fails(self):
        (self.act / "r4.csv").write_bytes(b"")
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("0-byte", out)

    def test_header_never_sorted_into_rows(self):
        # Swap the header with the first data row: the header must be compared
        # as line 1, not sorted in with the rows.
        p = self.act / "r5.csv"
        header, *rows = p.read_text().splitlines()
        p.write_text("\n".join([rows[0], header] + rows[1:]) + "\n")
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("header differs", out)

    def test_sort_is_code_point_order(self):
        rows = ["\u00e9", "z", "Z", "a", "10", "9"]
        self.assertEqual(sorted(rows), sorted(rows, key=lambda r: r.encode("utf-8")))

    def test_invalid_utf8_fails_cleanly(self):
        (self.act / "r4.csv").write_bytes(b"repo_id,event_date,star_events\n\xff\n")
        code, out = self.dirs()
        self.assertEqual(code, 1)
        self.assertIn("actual file invalid", out)

    def test_extra_file_noted_not_failed(self):
        (self.act / "debug.csv").write_text("a\n")
        code, out = self.dirs()
        self.assertEqual(code, 0)
        self.assertIn("debug.csv", out)

    def test_fixtures_mode_all_pass_against_themselves(self):
        root = self.tmp / "actual_root"
        count = 0
        for fx in FIXTURES.iterdir():
            if (fx / "expected").is_dir():
                shutil.copytree(fx / "expected", root / fx.name)
                count += 1
        code, out = run(["x", "fixtures", str(FIXTURES), str(root)])
        self.assertEqual(code, 0, out)
        self.assertIn(f"{count}/{count} fixtures equal", out)

    def test_fixtures_mode_missing_fixture_output_fails(self):
        root = self.tmp / "empty_root"
        root.mkdir()
        count = sum(1 for fx in FIXTURES.iterdir() if (fx / "expected").is_dir())
        code, out = run(["x", "fixtures", str(FIXTURES), str(root)])
        self.assertEqual(code, 1)
        self.assertIn(f"0/{count} fixtures equal", out)

    def test_multiset_minus_ignores_order_and_counts_duplicates(self):
        self.assertEqual(co.multiset_minus(["b", "a", "a", "c"], ["a", "c", "b"]), ["a"])
        self.assertEqual(co.multiset_minus(["x"], []), ["x"])
        self.assertEqual(co.multiset_minus([], ["x"]), [])

    def test_usage_error(self):
        self.assertEqual(run(["x", "bogus", "a", "b"])[0], 2)


if __name__ == "__main__":
    unittest.main()
