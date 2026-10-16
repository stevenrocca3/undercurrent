"""Tests for gate2_evidence.py. Run: python -m unittest tools/test_gate2_evidence.py"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import gate2_evidence as ge  # noqa: E402

ALL_CHECKS = {n for names in ge.CRITERIA.values() for n in names}
WINDOW = list(ge.hours("2026-10-16T06:00:00Z", "2026-10-30T05:00:00Z"))


class Gate2Evidence(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        t = Path(tmp.name)
        self.root, self.live, self.work = t / "root", t / "live", t / "work"
        for d in (self.root, self.live, self.work / "input"):
            d.mkdir(parents=True)
        (self.root / "fetch_log.csv").write_text("source_file_hour\n")
        (self.work / "input" / "2026-10-16-6.json.gz").write_bytes(b"x")
        (self.work / "available_at.csv").write_text("source_file_hour,available_at\n")
        (self.live / "registry.csv").write_text(
            "source_file_hour,status\n" + "".join(f"{h},present\n" for h in WINDOW))
        self.delay = t / "delay-report.json"
        self.delay.write_text(json.dumps({"proposed_L_hours": 1}))
        patch = mock.patch.object(ge, "DELAY_REPORT", self.delay)
        patch.start()
        self.addCleanup(patch.stop)
        self.write_checks({n: 0 for n in ALL_CHECKS})

    def write_checks(self, codes):
        (self.work / "checks.tsv").write_text("".join(f"{n}\t{c}\n" for n, c in codes.items()))

    def build(self, ci={"run_url": "u"}):
        return ge.build(self.root, self.live, self.work, ci)

    def test_all_pass(self):
        ev = self.build()
        self.assertTrue(ev["pass"], ev["criteria"])
        self.assertEqual(len(ev["input_manifest"]), 336)
        self.assertEqual(ev["input_manifest"][0]["file"], "2026-10-16-6.json.gz")
        self.assertIsNone(ev["input_manifest"][1]["sha256"])
        self.assertEqual(len(ev["fetch_log_sha256"]), 64)
        self.assertEqual(ev["available_at_manifest"], ["source_file_hour,available_at"])
        self.assertEqual(ev["delay_report"], {"proposed_L_hours": 1})

    def test_failed_check_fails_its_criterion(self):
        self.write_checks({n: (1 if n == "live_digest" else 0) for n in ALL_CHECKS})
        ev = self.build()
        self.assertFalse(ev["criteria"]["2_live_equals_replay"])
        self.assertFalse(ev["pass"])

    def test_incomplete_live_registry_fails(self):
        (self.live / "registry.csv").write_text("source_file_hour,status\n2026-10-16T06:00:00Z,present\n")
        self.assertFalse(self.build()["criteria"]["1_every_hour_accounted"])

    def test_no_delay_estimate_or_ci_fails(self):
        self.delay.write_text(json.dumps({"proposed_L_hours": None}))
        ev = self.build(ci=None)
        self.assertFalse(ev["criteria"]["5_delay_report"])
        self.assertFalse(ev["criteria"]["6_generated_by_ci"])

    def test_refuses_outside_ci(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
            self.assertEqual(ge.main(["x", str(self.root), str(self.live), str(self.work), str(self.work / "g.json")]), 2)


if __name__ == "__main__":
    unittest.main()
