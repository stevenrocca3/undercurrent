"""Tests for tools/fetch_log_check.py. Run: python -m unittest tools/test_fetch_log_check.py"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_log_check as flc  # noqa: E402

HEADER = "source_file_hour,attempt_at,http_status,bytes,sha256,last_modified,etag,decode_status,outcome,error,available_at\n"
H0, H1 = "2026-10-16T06:00:00Z", "2026-10-16T07:00:00Z"


class FetchLogCheck(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def archive(self, name, body):
        sha = hashlib.sha256(body).hexdigest()
        d = self.root / "archive" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sha}.json.gz").write_bytes(body)
        return sha

    def log(self, rows):
        (self.root / "fetch_log.csv").write_text(HEADER + "".join(
            f"{h},x,,,{sha},,,,{outcome},,\n" for h, sha, outcome in rows))

    def test_consistent(self):
        a = self.archive("2026-10-16-6", b"a")
        late = self.archive("2026-10-16-6", b"republished")
        self.log([(H0, "", "pending"), (H0, a, "success"), (H0, late, "republished"), (H1, "", "deadline")])
        self.assertEqual(flc.problems(self.root, H0, H1), [])
        self.assertEqual(flc.main(["x", str(self.root), H0, H1]), 0)

    def test_every_failure_reported(self):
        a = self.archive("2026-10-16-6", b"a")
        self.archive("2026-10-16-6", b"stray")
        self.log([(H0, a, "success"), (H0, "", "deadline"), (H1, "0" * 64, "success")])
        found = flc.problems(self.root, H0, "2026-10-16T08:00:00Z")
        self.assertEqual(len(found), 4, found)
        self.assertIn("2026-10-16T08:00:00Z: no final outcome", found)
        self.assertIn(f"{H0}: 2 final outcomes", found)
        self.assertTrue(any("0" * 64 in p and "SHA-256 differs" in p for p in found))
        self.assertTrue(any("named by no fetch-log row" in p for p in found))
        self.assertEqual(flc.main(["x", str(self.root), H0, H1]), 1)


if __name__ == "__main__":
    unittest.main()
