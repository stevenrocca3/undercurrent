"""Ingest tests (spec §1) against the committed fixtures.

    .venv/bin/python -m unittest pipeline/test_ingest.py
"""

import json
import unittest
from pathlib import Path

from pipeline.ingest import HourRead, parse_timestamp, requested_hours

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def fixture_dirs():
    return sorted(p for p in FIXTURES.iterdir() if (p / "fixture.json").is_file())


def read_fixture(fx, chunk_size=1 << 16):
    """[(hour, status, [(source_line, raw, partial), ...]), ...] for a fixture's requested hours."""
    first, last = (parse_timestamp(h) for h in json.loads((fx / "fixture.json").read_text())["requested_hours"])
    out = []
    for hour in requested_hours(first, last):
        read = HourRead(fx / "input", hour, chunk_size)
        lines = list(read.lines())
        out.append((hour, read.status, lines))
    return out


class TestIngest(unittest.TestCase):
    def test_line_total_matches_expected_r1(self):
        # canonical + all Q = total lines recovered from readable files (spec §6 R1)
        for fx in fixture_dirs():
            with self.subTest(fixture=fx.name):
                rows = (fx / "expected" / "r1.csv").read_text().splitlines()[1:]
                expected = sum(int(r.split(",")[1]) for r in rows)
                got = sum(len(lines) for _, _, lines in read_fixture(fx))
                self.assertEqual(got, expected)

    def test_chunk_size_does_not_change_result(self):
        # Exercises the byte-by-byte replay when an error lands mid-chunk.
        for fx in fixture_dirs():
            with self.subTest(fixture=fx.name):
                baseline = read_fixture(fx)
                for size in (1, 7, 100):
                    self.assertEqual(read_fixture(fx, size), baseline, f"chunk_size={size}")

    def test_f16_recovers_partial_last_line(self):
        [(_, status, lines)] = read_fixture(FIXTURES / "F16-truncated-hour")
        self.assertEqual(status, "truncated")
        self.assertEqual([(n, partial) for n, _, partial in lines],
                         [(1, False), (2, False), (3, False), (4, False), (5, True)])
        self.assertEqual(lines[4][1], b'{"id":"1005","type":"IssuesEvent","actor":{"id":202,"lo')

    def test_f23_statuses_and_line_counts(self):
        got = [(status, len(lines)) for _, status, lines in read_fixture(FIXTURES / "F23-registry-corner-cases")]
        self.assertEqual(got, [("present", 6), ("unreadable", 0), ("truncated", 1), ("unreadable", 0),
                               ("present", 0), ("present", 2), ("truncated", 1)])
        # A truncated hour whose stream failed right after a complete line has no partial line.
        self.assertFalse(any(partial for _, status, lines in read_fixture(FIXTURES / "F23-registry-corner-cases")
                             for _, _, partial in lines))

    def test_f24_final_line_without_lf_is_a_normal_line(self):
        [(_, status, lines)] = read_fixture(FIXTURES / "F24-line-endings-and-cr")
        self.assertEqual(status, "present")
        self.assertEqual(len(lines), 9)
        self.assertFalse(lines[-1][2])
        self.assertTrue(lines[6][1].endswith(b"\r"))  # CR kept in raw bytes; stripped only for record_hash

    def test_missing_hour(self):
        statuses = [status for _, status, _ in read_fixture(FIXTURES / "F09-missing-hour")]
        self.assertEqual(statuses, ["present", "missing", "present"])


if __name__ == "__main__":
    unittest.main()
