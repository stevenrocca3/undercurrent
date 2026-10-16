"""Live mode (02 §6) = replay of the archive with the exported manifest (02 §8.1).

The fetcher runs on a fake clock against a local http.server while `live`
runs in a thread, polling the fetch log. Then the archive is replayed with
`run --replay --archive --available-at` and every output file must match.

    .venv/bin/python -m unittest pipeline/test_live.py
    LIVE_REAL=1 .venv/bin/python -m unittest pipeline/test_live.py   # also 3 real September hours
"""

import os
import shutil
import tempfile
import threading
import unittest
from datetime import timedelta
from pathlib import Path

from pipeline.__main__ import run
from pipeline.canon import read_manifest
from pipeline.fetcher import D, Fetcher, export_manifest, read_log
from pipeline.ingest import HOUR, hour_file_name, parse_timestamp, requested_hours
from pipeline.test_fetcher import OTHER, Server

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
REAL = Path.home() / "undercurrent-data" / "gharchive"
OUTPUTS = ["r1.csv", "r2.csv", "r3.csv", "r4.csv", "r5.csv", "registry.csv", "flags.csv",
           "canon_digest.csv", "registry_evidence.csv"]
NOT_FOUND = (404, b"", {})


class TestLiveEqualsReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.server = Server()
        self.addCleanup(self.server.close)

    def serve(self, hour, *responses):
        self.server.script["/" + hour_file_name(hour)] = list(responses)

    def live_and_replay(self, first, last, cutoffs):
        """Run the fetcher to the end of every hour's schedule with live mode following it; return both outputs."""
        root, live_out, replay_out = self.tmp / "fetcher", self.tmp / "live", self.tmp / "replay"
        now = [first + HOUR]
        fetcher = Fetcher(root, first, self.server.url, clock=lambda: now[0],
                          clock_source=lambda: ("test", "0", ""), end_hour=last)
        live = threading.Thread(target=run, args=(root, first, last, live_out, cutoffs),
                                kwargs={"archive": True, "live_poll": 0.01})
        live.start()
        end = last + HOUR + D + timedelta(days=8)  # past every deadline, recheck and late attempt
        while True:
            when, _, _ = fetcher.next_action()
            if when > end:
                break
            now[0] = max(now[0], when)
            fetcher.tick()
        live.join(timeout=600)
        self.assertFalse(live.is_alive())
        export_manifest(root, self.tmp / "manifest.csv")
        run(root, first, last, replay_out, cutoffs, replay=True, archive=True,
            manifest=read_manifest(self.tmp / "manifest.csv"))
        for name in OUTPUTS:
            self.assertEqual((live_out / name).read_bytes(), (replay_out / name).read_bytes(), name)
        return root, live_out

    def test_order_wait_republish_keeps_first_version(self):
        fx = FIXTURES / "F26-flags-from-kept-occurrence"
        h0, h1, h2 = (parse_timestamp(f"2026-09-01T0{i}:00:00Z") for i in range(3))
        files = {h: (fx / "input" / hour_file_name(h)).read_bytes() for h in (h0, h1, h2)}
        self.serve(h0, NOT_FOUND, NOT_FOUND, NOT_FOUND, (200, files[h0], {"ETag": '"v1"'}),
                   (200, OTHER, {"ETag": '"v2"'}))  # found at +15 min, republished at the +24 h recheck
        self.serve(h1, (200, files[h1], {}))  # succeeds first, waits for h0
        self.serve(h2, NOT_FOUND, (200, files[h2], {}))
        root, out = self.live_and_replay(h0, h2, [parse_timestamp("2026-09-02T00:00:00Z")])
        log = read_log(root / "fetch_log.csv")
        self.assertEqual([r["outcome"] for r in log if r["source_file_hour"] == "2026-09-01T00:00:00Z"],
                         ["pending"] * 3 + ["success", "republished"])
        for name in ["r1.csv", "r2.csv", "r3.csv", "r4.csv", "registry.csv", "flags.csv"]:  # first version kept
            self.assertEqual((out / name).read_text(), (fx / "expected" / name).read_text(), name)
        evidence = (out / "registry_evidence.csv").read_text().splitlines()
        self.assertEqual(evidence[1].split(",")[-2:], ["200", "2026-09-01T01:15:00Z"])

    def test_deadline_truncated_unreadable_and_missing_hours(self):
        fx = FIXTURES / "F23-registry-corner-cases"
        hours = list(requested_hours(parse_timestamp("2026-09-01T00:00:00Z"), parse_timestamp("2026-09-01T06:00:00Z")))
        for h in hours[:-1]:  # served as they are: truncated and unreadable ones run to the deadline
            self.serve(h, (200, (fx / "input" / hour_file_name(h)).read_bytes(), {}))
        self.serve(hours[-1], NOT_FOUND)  # never published: missing
        root, out = self.live_and_replay(hours[0], hours[-1], [parse_timestamp("2026-09-02T00:00:00Z")])
        statuses = [line.split(",")[1] for line in (out / "registry.csv").read_text().splitlines()[1:]]
        self.assertEqual(statuses, ["present", "unreadable", "truncated", "unreadable", "present", "present", "missing"])
        finals = [r["outcome"] for r in read_log(root / "fetch_log.csv") if r["outcome"] in ("success", "deadline")]
        self.assertEqual(finals.count("deadline"), 4)

    @unittest.skipUnless(os.environ.get("LIVE_REAL") and REAL.is_dir(), "set LIVE_REAL=1 (needs ~/undercurrent-data)")
    def test_real_september_hours(self):
        h0, h1, h2 = (parse_timestamp(f"2026-09-15T{i}:00:00Z") for i in (14, 15, 16))
        files = {h: (REAL / hour_file_name(h)).read_bytes() for h in (h0, h1, h2)}
        self.serve(h0, NOT_FOUND, NOT_FOUND, (200, files[h0], {}))  # 10 min late
        self.serve(h1, (200, files[h1], {}))
        self.serve(h2, NOT_FOUND, (200, files[h2], {}))
        self.live_and_replay(h0, h2, [parse_timestamp("2026-09-15T18:00:00Z"), parse_timestamp("2026-09-16T00:00:00Z")])


if __name__ == "__main__":
    unittest.main()
