"""--available-at manifest (02 §8, 01 §4).

    .venv/bin/python -m unittest pipeline/test_available_at.py
"""

import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from pipeline.__main__ import main, run_fixtures
from pipeline.canon import available_at, read_manifest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
F27 = FIXTURES / "F27-r5-boundary-conditions"
COMPARED = ["r1.csv", "r2.csv", "r3.csv", "r4.csv", "r5.csv", "registry.csv", "flags.csv", "canon_digest.csv"]


def write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


class TestReadManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def manifest(self, *rows):
        return write(self.tmp / "m.csv", "source_file_hour,available_at\n" + "".join(r + "\n" for r in rows))

    def test_offsets_and_fractions(self):
        m = read_manifest(self.manifest("2026-10-16T00:00:00Z,2026-10-16T01:03:12.5Z",
                                        "2026-10-16T01:00:00Z,2026-10-16T04:10:00+02:00"))
        self.assertEqual(m, {datetime(2026, 10, 16, 0): datetime(2026, 10, 16, 1, 3, 12, 500000),
                             datetime(2026, 10, 16, 1): datetime(2026, 10, 16, 2, 10)})

    def test_errors(self):
        for rows in [["2026-10-16T00:00:00Z,2026-10-16T01:03:12"],  # no offset
                     ["2026-10-16T00:00:00Z,2026-10-16T01:03:12.1234567Z"],  # finer than µs
                     ["2026-10-16T00:00:00Z,2026-10-16T01:00:00Z", "2026-10-16T00:00:00Z,2026-10-16T02:00:00Z"]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                read_manifest(self.manifest(*rows))
        with self.assertRaises(ValueError):
            read_manifest(write(self.tmp / "h.csv", "hour,available_at\n"))

    def test_unlisted_hour_is_backfill(self):
        m = {datetime(2026, 10, 16, 0): datetime(2026, 10, 16, 1, 5)}
        self.assertEqual(available_at(datetime.fromisoformat("2026-10-16T00:00:00+00:00"), m), datetime(2026, 10, 16, 1, 5))
        self.assertEqual(available_at(datetime.fromisoformat("2026-10-16T01:00:00+00:00"), m), datetime(2026, 10, 16, 8))


class TestFixtureManifest(unittest.TestCase):
    """F27 copied with an available_at.csv beside fixture.json."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copytree(F27, self.tmp / "fx" / F27.name)
        self.hours = [p.name.removesuffix(".json.gz") for p in sorted((F27 / "input").glob("*.json.gz"))]

    def run_with(self, name, at_for_hour=None):
        if at_for_hour:
            write(self.tmp / "fx" / F27.name / "available_at.csv", "source_file_hour,available_at\n" + "".join(
                f"{h[:10]}T{int(h[11:]):02d}:00:00Z,{at_for_hour(h)}\n" for h in self.hours))
        run_fixtures(self.tmp / "fx", self.tmp / name)
        return self.tmp / name / F27.name

    def test_backfill_values_change_nothing(self):
        plain = self.run_with("plain")
        same = self.run_with("same", lambda h: f"{datetime.strptime(h, '%Y-%m-%d-%H') + timedelta(hours=7):%Y-%m-%dT%H:%M:%S}.000Z")
        for f in COMPARED:
            with self.subTest(file=f):
                self.assertEqual((plain / f).read_bytes(), (same / f).read_bytes())

    def test_late_hours_leave_r5(self):
        out = self.run_with("late", lambda h: "2099-01-01T00:00:00Z")
        self.assertEqual((out / "r5.csv").read_text(), "cutoff,repo_id,star_events\n")
        evidence = (out / "registry_evidence.csv").read_text().splitlines()
        self.assertEqual(evidence[0], "source_file_hour,status,file_bytes,lines,error,http_status,available_at")
        self.assertTrue(all(row.endswith(",,2099-01-01T00:00:00Z") for row in evidence[1:]))


class TestRunFlag(unittest.TestCase):
    def test_bad_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = write(Path(tmp, "m.csv"), "source_file_hour,available_at\n2026-10-16T00:00:00Z,2026-10-16T01:00:00\n")
            with self.assertRaises(ValueError):
                main(["run", tmp, "2026-10-16T00:00:00Z", "2026-10-16T00:00:00Z", str(Path(tmp, "out")),
                      "--available-at", str(bad)])


if __name__ == "__main__":
    unittest.main()
