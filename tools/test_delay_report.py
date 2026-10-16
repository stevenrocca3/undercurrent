"""Tests for tools/delay_report.py. Run: python -m unittest tools/test_delay_report.py"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import delay_report as dr  # noqa: E402

HEADER = "source_file_hour,attempt_at,http_status,bytes,sha256,last_modified,etag,decode_status,outcome,error,available_at\n"


class DelayReport(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "clock.csv").write_text(
            "checked_at,source,offset_seconds,error\n2026-10-16T00:00:00Z,chrony,-0.0001,\n")

    def log(self, rows):
        (self.root / "fetch_log.csv").write_text(HEADER + "".join(
            f'{h},x,,,{sha},"Fri, 16 Oct 2026 01:05:04 GMT",,,{outcome},,{avail}\n'
            for h, sha, outcome, avail in rows))

    def test_counts_and_delays(self):
        self.log([("2026-10-16T00:00:00Z", "", "pending", ""),
                  ("2026-10-16T00:00:00Z", "a", "success", "2026-10-16T01:05:00Z"),
                  ("2026-10-16T00:00:00Z", "b", "republished", ""),
                  ("2026-10-16T01:00:00Z", "c", "success", "2026-10-16T03:10:00.5+01:00"),
                  ("2026-10-16T02:00:00Z", "d", "incomplete", ""),
                  ("2026-10-16T02:00:00Z", "d", "deadline", "2026-10-17T03:00:00Z"),
                  ("2026-10-16T03:00:00Z", "", "deadline", ""),
                  ("2026-10-16T04:00:00Z", "", "pending", "")])
        r = dr.report(self.root)
        self.assertEqual((r["window_start"], r["window_end"], r["hours_tracked"]),
                         ("2026-10-16T00:00:00Z", "2026-10-16T04:00:00Z", 5))
        self.assertEqual((r["succeeded"], r["missing"], r["ingested_truncated"], r["republished"],
                          r["no_final_outcome_yet"]), (2, 1, 1, 1, 1))
        # Hour 01 is due 02:00Z; 03:10:00.5+01:00 is 02:10:00.5Z.
        self.assertEqual(r["delay_seconds"], {"min": 300.0, "p50": 300.0, "p90": 600.5,
                                              "p99": 600.5, "max": 600.5})
        self.assertEqual(r["proposed_L_hours"], 1)
        self.assertEqual(r["clock_offsets"][0]["offset_seconds"], "-0.0001")

    def test_nearest_rank(self):
        values = list(range(1, 337))  # 336 hours, the 14-day window
        self.assertEqual(dr.nearest_rank(values, 0.99), 333)
        self.assertEqual(dr.nearest_rank(values, 0.50), 168)
        self.assertEqual(dr.nearest_rank([7], 0.99), 7)

    def test_no_success_yet(self):
        self.log([("2026-10-16T00:00:00Z", "", "pending", "")])
        r = dr.report(self.root)
        self.assertIsNone(r["delay_seconds"])
        self.assertIsNone(r["proposed_L_hours"])


if __name__ == "__main__":
    unittest.main()
