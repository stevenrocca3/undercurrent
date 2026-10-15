"""Tests for reconcile.py. Run: python -m unittest tools/test_reconcile.py"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import reconcile as rc  # noqa: E402

H0, H1 = "2026-09-01T00:00:00Z", "2026-09-01T01:00:00Z"


def write(d, name, text):
    (d / name).write_text(text)


class Reconcile(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.ours, self.theirs = Path(tmp.name, "ours"), Path(tmp.name, "theirs")
        self.ours.mkdir(), self.theirs.mkdir()
        write(self.ours, "r2.csv", f"source_file_hour,event_type,event_count\n{H0},PushEvent,1000\n{H0},WatchEvent,10\n")
        write(self.ours, "r4.csv", "repo_id,event_date,star_events\n7,2026-09-01,10\n8,2026-09-01,3\n")
        write(self.ours, "registry.csv", f"source_file_hour,status\n{H0},present\n{H1},present\n")
        write(self.theirs, "type_by_hour.csv", f"hour,event_type,event_count\n{H0},PushEvent,1001\n{H0},WatchEvent,10\n")
        write(self.theirs, "ids_by_hour.csv", f"hour,distinct_event_ids\n{H0},1011\n")
        write(self.theirs, "stars.csv", "repo_id,event_date,star_events\n7,2026-09-01,10\n")

    def cell(self, cells, metric, key):
        return next(c for c in cells if c["metric"] == metric and c["key"] == key)

    def test_within_tolerance_passes(self):
        cells, summary = rc.reconcile(self.ours, self.theirs)
        self.assertTrue(summary["pass"])
        self.assertEqual(summary["out_of_tolerance"], 0)
        c = self.cell(cells, "type_by_hour", f"{H0}|PushEvent")  # 1/1001 < 0.1%
        self.assertEqual(c["rel_diff"], "0.000999")
        self.assertTrue(c["within_tolerance"])

    def test_stars_only_for_their_top_repos(self):
        cells, _ = rc.reconcile(self.ours, self.theirs)
        self.assertEqual({c["key"] for c in cells if c["metric"] == "stars"}, {"7|2026-09-01"})

    def test_out_of_tolerance_is_unexplained_and_fails(self):
        write(self.theirs, "type_by_hour.csv", f"hour,event_type,event_count\n{H0},PushEvent,1002\n{H0},WatchEvent,10\n")
        cells, summary = rc.reconcile(self.ours, self.theirs)
        self.assertEqual(self.cell(cells, "type_by_hour", f"{H0}|PushEvent")["category"], "unexplained")
        self.assertFalse(summary["pass"])

    def test_theirs_zero_ours_nonzero_is_out(self):
        write(self.ours, "r2.csv", f"source_file_hour,event_type,event_count\n{H0},PushEvent,1000\n{H0},WatchEvent,10\n{H1},PushEvent,1\n")
        cells, _ = rc.reconcile(self.ours, self.theirs)
        c = self.cell(cells, "ids_by_hour", H1)
        self.assertEqual(c["rel_diff"], "inf")
        self.assertEqual(c["category"], "missing_hour_theirs")

    def test_missing_hour_ours(self):
        write(self.ours, "registry.csv", f"source_file_hour,status\n{H0},truncated\n")
        write(self.theirs, "ids_by_hour.csv", f"hour,distinct_event_ids\n{H0},2000\n")
        cells, _ = rc.reconcile(self.ours, self.theirs)
        self.assertEqual(self.cell(cells, "ids_by_hour", H0)["category"], "missing_hour_ours")

    def test_manual_category_wins_and_unknown_is_rejected(self):
        write(self.theirs, "ids_by_hour.csv", f"hour,distinct_event_ids\n{H0},2000\n")
        row = {"metric": "ids_by_hour", "key": H0, "category": "dedup_policy", "reason": "checked"}
        cells, summary = rc.reconcile(self.ours, self.theirs, [row])
        self.assertEqual(self.cell(cells, "ids_by_hour", H0)["reason"], "checked")
        self.assertTrue(summary["pass"])
        with self.assertRaises(ValueError):
            rc.reconcile(self.ours, self.theirs, [dict(row, category="close_enough")])


if __name__ == "__main__":
    unittest.main()
