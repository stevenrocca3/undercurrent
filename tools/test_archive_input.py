"""Tests for tools/archive_input.py. Run: python -m unittest tools/test_archive_input.py"""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import archive_input as ai  # noqa: E402

HEADER = "source_file_hour,attempt_at,http_status,bytes,sha256,last_modified,etag,decode_status,outcome,error,available_at\n"


class ArchiveInput(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root, self.out = Path(tmp.name) / "root", Path(tmp.name) / "out"

    def archive(self, name, body):
        sha = hashlib.sha256(body).hexdigest()
        d = self.root / "archive" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{sha}.json.gz").write_bytes(body)
        return sha

    def log(self, rows):
        (self.root / "fetch_log.csv").write_text(HEADER + "".join(
            f"{h},2026-10-16T00:00:00Z,,,{sha},,,,{outcome},,{avail}\n" for h, sha, outcome, avail in rows))

    def test_final_outcomes_only(self):
        ok = self.archive("2026-10-16-2", b"first")
        late = self.archive("2026-10-16-2", b"republished")
        trunc = self.archive("2026-10-16-3", b"truncated")
        stray = self.archive("2026-10-16-4", b"late")
        self.log([("2026-10-16T03:00:00Z", trunc, "incomplete", ""),
                  ("2026-10-16T02:00:00Z", ok, "success", "2026-10-16T03:05:00Z"),
                  ("2026-10-16T02:00:00Z", late, "republished", ""),
                  ("2026-10-16T03:00:00Z", trunc, "deadline", "2026-10-17T04:00:00Z"),
                  ("2026-10-16T04:00:00Z", "", "deadline", ""),
                  ("2026-10-16T04:00:00Z", stray, "late", "")])
        manifest = self.root / "available_at.csv"
        self.assertEqual(ai.main(["x", str(self.root), str(self.out), str(manifest)]), 0)
        self.assertEqual(manifest.read_text(), "source_file_hour,available_at\n"
                         "2026-10-16T02:00:00Z,2026-10-16T03:05:00Z\n2026-10-16T03:00:00Z,2026-10-17T04:00:00Z\n")
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         ["2026-10-16-2.json.gz", "2026-10-16-3.json.gz"])
        self.assertEqual((self.out / "2026-10-16-2.json.gz").read_bytes(), b"first")

    def test_two_final_rows_stop(self):
        sha = self.archive("2026-10-16-2", b"x")
        self.log([("2026-10-16T02:00:00Z", sha, "success", ""), ("2026-10-16T02:00:00Z", sha, "deadline", "")])
        self.assertEqual(ai.main(["x", str(self.root), str(self.out)]), 1)

    def test_hash_mismatch_stops(self):
        self.archive("2026-10-16-2", b"x")
        self.log([("2026-10-16T02:00:00Z", "0" * 64, "success", "")])
        self.assertEqual(ai.main(["x", str(self.root), str(self.out)]), 1)


if __name__ == "__main__":
    unittest.main()
