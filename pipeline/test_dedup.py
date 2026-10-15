"""Dedup tests (spec §3) beyond the fixtures.

    .venv/bin/python -m unittest pipeline/test_dedup.py
"""

import unittest
from datetime import datetime

import duckdb

from pipeline.dedup import deduplicate

H0, H1 = datetime(2026, 9, 1, 0), datetime(2026, 9, 1, 1)


class TestDedup(unittest.TestCase):
    def test_keeps_smallest_hour_then_line_regardless_of_load_order(self):
        con = duckdb.connect()
        con.execute("CREATE TABLE canon (event_id VARCHAR, source_file_hour TIMESTAMP, source_line INTEGER, record_hash VARCHAR)")
        con.executemany("INSERT INTO canon VALUES (?, ?, ?, ?)", [
            ("x", H1, 1, "A"),  # loaded first, but a later hour
            ("x", H0, 9, "A"),
            ("x", H0, 5, "B"),  # kept: smallest (hour, line)
            ("y", H0, 1, "C"),
            ("y", H0, 2, "C"),  # same bytes: duplicate, not a conflict
            ("z", H0, 3, "D"),
        ])
        self.assertEqual(deduplicate(con), (3, 3, 2))
        self.assertEqual(con.execute("SELECT event_id, source_file_hour, source_line FROM events ORDER BY 1").fetchall(),
                         [("x", H0, 5), ("y", H0, 1), ("z", H0, 3)])


if __name__ == "__main__":
    unittest.main()
