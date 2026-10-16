"""G33 (02 §8): both implementations, run black-box through their CLIs, treat every
available_at manifest the same way. Run: python -m unittest tools/test_manifest_errors.py

Bad manifests: both exit non-zero and write no output CSV.
Good edge cases: both exit 0 and their R1-R7 compare equal.
Imports neither implementation; runs them as subprocesses.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import compare_outputs as co  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
F12 = next((REPO / "fixtures").glob("F12-*")) / "input"
HOURS = ["2026-09-01T00:00:00Z", "2026-09-01T02:00:00Z", "--cutoff", "2026-09-01T08:00:00Z"]
CLIS = {"reference": [sys.executable, "reference/reference.py", "run"],
        "pipeline": [sys.executable, "-m", "pipeline", "run"]}
H = "source_file_hour,available_at\n"
BAD = {
    "seven_fraction_digits": H + "2026-09-01T02:00:00Z,2026-09-01T03:00:00.1234567Z\n",
    "hour_listed_twice": H + "2026-09-01T02:00:00Z,2026-09-01T03:00:00Z\n2026-09-01T02:00:00Z,2026-09-01T09:30:00Z\n",
    "space_separator": H + "2026-09-01T02:00:00Z,2026-09-01 03:00:00Z\n",
    "compact_form": H + "2026-09-01T02:00:00Z,20260901T030000Z\n",
    "no_offset": H + "2026-09-01T02:00:00Z,2026-09-01T03:00:00\n",
    "lowercase": H + "2026-09-01T02:00:00Z,2026-09-01t03:00:00z\n",
    "bad_header": "hour,available_at\n2026-09-01T02:00:00Z,2026-09-01T03:00:00Z\n",
}
GOOD = {
    "other_offset": H + "2026-09-01T02:00:00Z,2026-09-01T05:00:00+02:00\n",
    "outside_range": H + "2026-09-05T02:00:00Z,2026-09-01T03:00:00Z\n",
    "earlier_than_due": H + "2026-09-01T02:00:00Z,2026-09-01T01:30:00Z\n",
    "microseconds": H + "2026-09-01T01:00:00Z,2026-09-01T08:00:00.000001Z\n2026-09-01T02:00:00Z,2026-09-01T03:04:05.5Z\n",
}


class ManifestErrors(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def run_both(self, name, text):
        manifest = self.tmp / f"{name}.csv"
        manifest.write_text(text)
        results = {}
        for impl, cli in CLIS.items():
            out = self.tmp / f"{name}-{impl}"
            p = subprocess.run(cli + [str(F12), HOURS[0], HOURS[1], str(out), *HOURS[2:],
                                      "--available-at", str(manifest)], cwd=REPO, capture_output=True)
            results[impl] = (p.returncode, out)
        return results

    def test_bad_manifests_stop_both(self):
        for name, text in BAD.items():
            for impl, (code, out) in self.run_both(name, text).items():
                with self.subTest(case=name, impl=impl):
                    self.assertNotEqual(code, 0)
                    self.assertEqual(list(out.glob("*.csv")) if out.exists() else [], [])

    def test_good_edge_cases_agree(self):
        for name, text in GOOD.items():
            r = self.run_both(name, text)
            with self.subTest(case=name):
                self.assertEqual((r["reference"][0], r["pipeline"][0]), (0, 0))
                self.assertEqual(co.main(["x", "dirs", str(r["reference"][1]), str(r["pipeline"][1])]), 0)


if __name__ == "__main__":
    unittest.main()
