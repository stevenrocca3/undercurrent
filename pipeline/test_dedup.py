"""Dedup tests (spec §3) beyond the fixtures.

    .venv/bin/python -m unittest pipeline/test_dedup.py
"""

import unittest
from datetime import datetime

import duckdb

from pipeline.dedup import create_dedup_tables, deduplicate, r3_counts

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
        create_dedup_tables(con)
        deduplicate(con)
        self.assertEqual(r3_counts(con), (3, 3, 2))
        self.assertEqual(con.execute("SELECT event_id, source_file_hour, source_line FROM events ORDER BY 1").fetchall(),
                         [("x", H0, 5), ("y", H0, 1), ("z", H0, 3)])


    def test_replay_hour_by_hour_matches_batch(self):
        rows = [("x", H1, 1, "A"), ("x", H0, 9, "A"), ("x", H0, 5, "B"), ("y", H1, 2, "C"), ("y", H1, 1, "D")]
        results = []
        for replay in (False, True):
            con = duckdb.connect()
            con.execute("CREATE TABLE canon (event_id VARCHAR, source_file_hour TIMESTAMP, source_line INTEGER, record_hash VARCHAR)")
            create_dedup_tables(con)
            for hour in (H0, H1):
                con.executemany("INSERT INTO canon VALUES (?, ?, ?, ?)", [r for r in rows if r[1] == hour])
                if replay:
                    deduplicate(con, hour)
            if not replay:
                deduplicate(con)
            results.append((r3_counts(con), con.execute("SELECT * FROM duplicates ORDER BY ALL").fetchall()))
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0][0], (2, 3, 3))


if __name__ == "__main__":
    unittest.main()
