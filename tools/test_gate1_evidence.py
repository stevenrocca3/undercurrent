"""Tests for gate1_evidence.py. Run: python -m unittest tools/test_gate1_evidence.py"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import gate1_evidence as ge  # noqa: E402

ALL_CHECKS = [n for names in ge.CRITERIA.values() for n in names]


class Gate1Evidence(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.input, self.work = Path(tmp.name, "in"), Path(tmp.name, "work")
        self.input.mkdir(), (self.work / "pipeline").mkdir(parents=True)
        (self.input / "2026-09-01-0.json.gz").write_bytes(b"x")
        window = list(ge.hours("2026-09-01T00:00:00Z", "2026-09-30T23:00:00Z"))
        (self.work / "pipeline" / "registry.csv").write_text(
            "source_file_hour,status\n" + "".join(f"{h},present\n" for h in window))
        self.write_checks({n: 0 for n in ALL_CHECKS})

    def write_checks(self, codes):
        (self.work / "checks.tsv").write_text("".join(f"{n}\t{c}\n" for n, c in codes.items()))

    def test_hours_covers_september(self):
        h = list(ge.hours("2026-09-01T00:00:00Z", "2026-09-30T23:00:00Z"))
        self.assertEqual((len(h), h[0], h[-1]), (720, "2026-09-01T00:00:00Z", "2026-09-30T23:00:00Z"))

    def test_all_pass(self):
        ev = ge.build(self.input, self.work, {"run_url": "u"})
        self.assertTrue(ev["pass"], ev["criteria"])
        self.assertEqual(len(ev["input_manifest"]), 720)
        self.assertEqual(ev["input_manifest"][0]["file"], "2026-09-01-0.json.gz")
        self.assertIsNone(ev["input_manifest"][1]["sha256"])
        self.assertEqual(len(ev["config_hash"]), 64)

    def test_one_failed_check_fails_its_criterion(self):
        self.write_checks({n: (1 if n == "replay_digest" else 0) for n in ALL_CHECKS})
        ev = ge.build(self.input, self.work, {"run_url": "u"})
        self.assertFalse(ev["criteria"]["3_replay_equals_batch"])
        self.assertFalse(ev["pass"])

    def test_missing_check_and_no_ci_fail(self):
        self.write_checks({"fixtures": 0})
        ev = ge.build(self.input, self.work, None)
        self.assertFalse(ev["criteria"]["2_month_equal"])
        self.assertFalse(ev["criteria"]["6_generated_by_ci"])

    def test_incomplete_registry_fails(self):
        (self.work / "pipeline" / "registry.csv").write_text("source_file_hour,status\n2026-09-01T00:00:00Z,present\n")
        self.assertFalse(ge.build(self.input, self.work, {})["criteria"]["5_registry_full_month"])

    def test_refuses_outside_ci(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
            self.assertEqual(ge.main(["x", str(self.input), str(self.work), str(self.work / "g.json")]), 2)


if __name__ == "__main__":
    unittest.main()
