"""Fetcher (02 §3-§5) against a scripted local http.server, with a fake clock.

    .venv/bin/python -m unittest pipeline/test_fetcher.py
"""

import gzip
import hashlib
import shutil
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from pipeline.fetcher import D, P, USER_AGENT, Fetcher, export_manifest, read_log

H = datetime(2026, 9, 1, 0, tzinfo=timezone.utc)
DUE = H + timedelta(hours=1)
PATH = "/2026-09-01-0.json.gz"
FULL = gzip.compress(b"".join(b'{"n":%d,"pad":"%064d"}\n' % (i, i * 7919) for i in range(3000)), mtime=0)
TRUNCATED = FULL[:len(FULL) // 2]
OTHER = gzip.compress(b'{"n":"republished"}\n', mtime=0)


class Server:
    """Serves scripted responses per path, in order; the last one repeats. Unscripted paths 404."""

    def __init__(self):
        self.script = {}
        self.requests = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                server.requests.append((self.path, dict(self.headers)))
                queue = server.script.get(self.path, [(404, b"", {})])
                status, body, headers = queue.pop(0) if len(queue) > 1 else queue[0]
                if status == "drop":  # promise more than is sent, then close the connection
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body) + 1000))
                    self.end_headers()
                    self.wfile.write(body)
                    self.close_connection = True
                    return
                if headers.get("ETag") and self.headers.get("If-None-Match") == headers["ETag"]:
                    status, body = 304, b""
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.server = Server()
        self.addCleanup(self.server.close)
        self.now = DUE
        self.fetcher = self.new_fetcher()

    def new_fetcher(self):
        return Fetcher(self.root, H, self.server.url, clock=lambda: self.now,
                       clock_source=lambda: ("test", "+0.000001 seconds fast"), end_hour=H)

    def serve(self, *responses):
        self.server.script[PATH] = list(responses)

    def run_until(self, t):
        """Advance the fake clock step by step to t, doing every action due on the way."""
        while True:
            when, _, _ = self.fetcher.next_action()
            if when > t:
                self.now = t
                return
            self.now = max(self.now, when)
            self.fetcher.tick()

    def rows(self):
        return [r for r in read_log(self.root / "fetch_log.csv") if r["source_file_hour"] == "2026-09-01T00:00:00Z"]

    def outcomes(self):
        return [r["outcome"] for r in self.rows()]

    def archived(self):
        return sorted(p.name for p in (self.root / "archive").rglob("*") if p.is_file())

    def manifest(self):
        out = self.root / "manifest.csv"
        export_manifest(self.root, out)
        return out.read_text().splitlines()[1:]

    def test_404_then_200(self):
        self.serve((404, b"", {}), (200, FULL, {"ETag": '"e1"', "Last-Modified": "Tue, 01 Sep 2026 01:04:00 GMT"}))
        self.run_until(DUE + P)
        self.assertEqual(self.outcomes(), ["pending", "success"])
        ok = self.rows()[1]
        self.assertEqual(ok["attempt_at"], "2026-09-01T01:05:00Z")
        self.assertEqual(ok["available_at"], "2026-09-01T01:05:00Z")
        self.assertEqual(ok["sha256"], hashlib.sha256(FULL).hexdigest())
        self.assertEqual((ok["http_status"], ok["decode_status"], ok["etag"]), ("200", "present", '"e1"'))
        self.assertEqual(self.archived(), [ok["sha256"] + ".json.gz"])
        self.assertEqual(self.server.requests[0][1]["User-Agent"], USER_AGENT)
        self.assertIn("srocca2000@outlook.com", USER_AGENT)
        self.assertEqual(self.manifest(), ["2026-09-01T00:00:00Z,2026-09-01T01:05:00Z"])

    def test_clock_offset_logged_at_start_and_every_24h(self):
        self.run_until(DUE + timedelta(hours=25))
        clock = [r for r in read_log(self.root / "fetch_log.csv") if r["outcome"] == "clock"]
        self.assertEqual([r["attempt_at"] for r in clock], ["2026-09-01T01:00:00Z", "2026-09-02T01:00:00Z"])
        self.assertEqual(clock[0]["error"], "test; offset +0.000001 seconds fast")

    def test_truncated_then_complete(self):
        self.serve((200, TRUNCATED, {}), (200, FULL, {}))
        self.run_until(DUE + P)
        self.assertEqual(self.outcomes(), ["incomplete", "success"])
        self.assertEqual(self.rows()[0]["decode_status"], "truncated")
        self.assertEqual(len(self.archived()), 2)  # the truncated version is archived too
        self.assertEqual(self.manifest(), ["2026-09-01T00:00:00Z,2026-09-01T01:05:00Z"])

    def test_connection_dropped_mid_body(self):
        self.serve(("drop", FULL[:1000], {}), (200, FULL, {}))
        self.run_until(DUE)
        self.assertEqual(self.outcomes(), ["error"])
        self.assertEqual(self.archived(), [])  # no final-name file, no leftover temp file
        self.run_until(DUE + timedelta(minutes=1))
        self.assertEqual(self.outcomes(), ["error", "success"])

    def test_429_and_500_back_off_exponentially_up_to_p(self):
        self.serve((429, b"", {}), (500, b"", {}), (503, b"", {}), (502, b"", {}), (500, b"", {}), (200, FULL, {}))
        self.run_until(DUE + timedelta(hours=1))
        rows = self.rows()
        self.assertEqual(self.outcomes(), ["error"] * 5 + ["success"])
        gaps = [(datetime.fromisoformat(b["attempt_at"][:-1]) - datetime.fromisoformat(a["attempt_at"][:-1]))
                for a, b in zip(rows, rows[1:])]
        self.assertEqual([g.total_seconds() / 60 for g in gaps], [1, 2, 4, 5, 5])
        self.assertEqual(rows[0]["error"], "HTTP 429")

    def test_deadline_with_only_truncated_versions(self):
        self.serve((200, TRUNCATED, {}))
        self.run_until(DUE + D + timedelta(hours=2))
        outcomes = self.outcomes()
        deadline = outcomes.index("deadline")
        self.assertEqual(outcomes[:deadline], ["incomplete"] * 288)  # every P for 24 h
        self.assertEqual(outcomes[deadline + 1:], ["incomplete"] * 2)  # then hourly
        row = self.rows()[deadline]
        self.assertEqual((row["decode_status"], row["available_at"]), ("truncated", "2026-09-02T01:00:00Z"))
        self.assertEqual(row["sha256"], hashlib.sha256(TRUNCATED).hexdigest())
        self.assertEqual(self.archived(), [row["sha256"] + ".json.gz"])  # one file: identical versions
        self.assertEqual(self.manifest(), ["2026-09-01T00:00:00Z,2026-09-02T01:00:00Z"])

    def test_down_past_deadline_then_late_file(self):
        self.serve((200, FULL, {}))
        self.now = DUE + D + timedelta(minutes=30)
        self.run_until(self.now + timedelta(hours=1))
        self.assertEqual(self.outcomes(), ["deadline", "late"])
        self.assertEqual(self.rows()[0]["decode_status"], "")  # missing
        self.assertEqual(self.manifest(), [])  # stays missing for live runs
        self.run_until(self.now + timedelta(days=9))
        self.assertEqual(self.outcomes(), ["deadline", "late"])  # nothing more for this hour

    def test_404_stops_after_seven_late_days(self):
        self.run_until(DUE + D + timedelta(days=8))
        outcomes = self.outcomes()
        self.assertEqual(outcomes.count("deadline"), 1)
        self.assertEqual(len(outcomes) - outcomes.index("deadline") - 1, 7 * 24)

    def test_restart_mid_hour(self):
        self.serve((404, b"", {}), (404, b"", {}), (200, FULL, {}))
        self.run_until(DUE + timedelta(minutes=2))
        with open(self.root / "fetch_log.csv", "a") as f:
            f.write("2026-09-01T00:00:00Z,2026-09-01T01:0")  # a crash in the middle of a row
        self.fetcher = self.new_fetcher()
        when, hour, kind = self.fetcher.next_action()
        self.assertEqual((when, hour, kind), (DUE + P, H, "fetch"))  # resumes the schedule, no repeat
        self.run_until(DUE + 2 * P)
        self.assertEqual(self.outcomes(), ["pending", "pending", "success"])
        clock = [r for r in read_log(self.root / "fetch_log.csv") if r["outcome"] == "clock"]
        self.assertEqual(len(clock), 1)  # not repeated on restart within 24 h

    def test_republished_at_24h_keeps_first_version(self):
        self.serve((200, FULL, {"ETag": '"v1"'}), (200, OTHER, {"ETag": '"v2"'}))
        self.run_until(DUE + RECHECK_AND_A_BIT)
        self.assertEqual(self.outcomes(), ["success", "republished"])
        first, recheck = self.rows()
        self.assertEqual(recheck["attempt_at"], "2026-09-02T01:00:00Z")
        self.assertEqual(self.server.requests[-1][1]["If-None-Match"], '"v1"')
        self.assertEqual(recheck["sha256"], hashlib.sha256(OTHER).hexdigest())
        self.assertEqual(len(self.archived()), 2)
        self.assertEqual(self.manifest(), ["2026-09-01T00:00:00Z,2026-09-01T01:00:00Z"])
        self.assertIsNone(self.fetcher.state(H).next_action())

    def test_unchanged_at_24h(self):
        self.serve((200, FULL, {"ETag": '"v1"'}))
        self.run_until(DUE + RECHECK_AND_A_BIT)
        self.assertEqual(self.outcomes(), ["success", "unchanged"])
        self.assertEqual(self.rows()[1]["http_status"], "304")
        self.assertIsNone(self.fetcher.state(H).next_action())


RECHECK_AND_A_BIT = timedelta(hours=26)

if __name__ == "__main__":
    unittest.main()
