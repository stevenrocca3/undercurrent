"""Replay vs batch (spec §4 Replay, §8 criterion 3) on every fixture.

    .venv/bin/python -m unittest pipeline/test_replay.py
"""

import tempfile
import unittest
from pathlib import Path

import duckdb

from pipeline.__main__ import run_fixtures
from pipeline.canon import table_digests

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
COMPARED = ["r1.csv", "r2.csv", "r3.csv", "r4.csv", "r5.csv", "registry.csv", "flags.csv", "canon_digest.csv"]


class TestReplayVsBatch(unittest.TestCase):
    def test_every_fixture_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            batch, replay = Path(tmp, "batch"), Path(tmp, "replay")
            run_fixtures(FIXTURES, batch)
            run_fixtures(FIXTURES, replay, replay=True)
            fixtures = sorted(p.name for p in FIXTURES.iterdir() if (p / "fixture.json").is_file())
            self.assertEqual(len(fixtures), len(list(batch.iterdir())))
            for name in fixtures:
                for f in COMPARED:
                    with self.subTest(fixture=name, file=f):
                        self.assertEqual((batch / name / f).read_bytes(), (replay / name / f).read_bytes())

    def test_digest_sees_data_but_not_run_time(self):
        con = duckdb.connect()
        con.execute("CREATE TABLE canon (source_file_hour TIMESTAMP, source_line INT, event_id VARCHAR,"
                    " ingested_at TIMESTAMP, source_last_modified TIMESTAMP)")
        con.execute("CREATE TABLE quarantine (source_file_hour TIMESTAMP, source_line INT)")
        con.execute("CREATE TABLE duplicates (source_file_hour TIMESTAMP, source_line INT)")
        con.execute("INSERT INTO canon VALUES ('2026-09-01', 2, 'b', '2026-10-01', NULL), ('2026-09-01', 1, 'a', '2026-10-01', NULL)")
        before = table_digests(con)
        con.execute("UPDATE canon SET ingested_at = '2027-01-01', source_last_modified = '2026-09-01'")
        self.assertEqual(table_digests(con), before)  # G29: operational fields excluded
        con.execute("UPDATE canon SET event_id = 'c' WHERE source_line = 2")
        self.assertNotEqual(table_digests(con)[0], before[0])


if __name__ == "__main__":
    unittest.main()
