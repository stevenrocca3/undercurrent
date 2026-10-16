"""Live fetcher (spec 02-live-ingestion.md §3-§5). Stdlib only, Python 3.9+.

    python -m pipeline.fetcher run ROOT START_HOUR [--base-url URL] [--end-hour H]
    python -m pipeline.fetcher manifest ROOT OUT_CSV

`run` tracks every hour from START_HOUR on and never exits. ROOT holds
`archive/YYYY-MM-DD-H/<sha256>.json.gz` and the append-only `fetch_log.csv`.
All state is rebuilt from the fetch log, so a restart neither loses nor
repeats rows. `manifest` exports the 02 §8 `available_at` manifest.

Fetch-log rows the spec does not define (G34, provisional): an extra last
column `available_at`; outcome `deadline` (no request; written when D passes
without a success, with the last incomplete version's sha256 and status, or
empty for missing); outcome `unchanged` for a +24 h recheck that found the
same content; outcome `clock` rows (empty hour) for the NTP offset.
"""

import argparse
import csv
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.ingest import HOUR, HourRead, format_instant, format_timestamp, hour_file_name, parse_timestamp

BASE_URL = "https://data.gharchive.org/"
USER_AGENT = "undercurrent-fetcher/1.0 (+https://github.com/stevenrocca3/undercurrent; srocca2000@outlook.com)"
P = timedelta(minutes=5)  # poll interval (L1)
D = timedelta(hours=24)  # give-up deadline (L2)
LATE_WINDOW = timedelta(days=7)  # hourly attempts after D (§3)
RECHECK = timedelta(hours=24)  # republication recheck (L6)
BACKOFF_START = timedelta(minutes=1)
CLOCK_EVERY = timedelta(hours=24)
TIMEOUT = 300  # seconds per request
COLUMNS = ["source_file_hour", "attempt_at", "http_status", "bytes", "sha256", "last_modified",
           "etag", "decode_status", "outcome", "error", "available_at"]


def retryable(status):
    return status == 429 or status >= 500


def parse_instant(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ" if "." in text else "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def csv_cell(text):
    if any(c in text for c in ',"\r\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def read_log(path):
    """Rows of the fetch log as dicts. A final line without a newline (a crash mid-write) is cut off."""
    if not path.exists():
        return []
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        data = data[:data.rfind(b"\n") + 1]
        with open(path, "r+b") as f:
            f.truncate(len(data))
    rows = list(csv.reader(data.decode("utf-8").splitlines()))
    if rows and rows[0] != COLUMNS:
        raise ValueError(f"{path}: unexpected header {rows[0]}")
    return [dict(zip(COLUMNS, r)) for r in rows[1:]]


def ntp_offset():
    """(source, offset) from chrony, the VM's NTP client; 'unavailable' elsewhere."""
    try:
        out = subprocess.run(["chronyc", "tracking"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError) as e:
        return "chrony", f"unavailable: {e}"
    fields = dict(line.split(":", 1) for line in out.splitlines() if ":" in line)
    return "chrony " + fields.get("Reference ID", "").strip(), fields.get("System time", "unavailable").strip()


class HourState:
    """What the fetch log says about one hour; rows are applied in log order."""

    def __init__(self, hour):
        self.hour = hour
        self.due = hour + HOUR
        self.last_attempt = None
        self.errors = 0  # consecutive error rows
        self.success = None  # the success row
        self.final = None  # success, deadline or late row
        self.last_incomplete = None
        self.rechecked = False

    def apply(self, row):
        outcome = row["outcome"]
        if outcome != "deadline":
            self.last_attempt = parse_instant(row["attempt_at"])
        self.errors = self.errors + 1 if outcome == "error" else 0
        if self.success:  # a recheck: done unless it failed in a way worth retrying
            self.rechecked = outcome != "error" or (row["http_status"] != "" and not retryable(int(row["http_status"])))
        elif outcome == "incomplete":
            self.last_incomplete = row
        elif outcome == "success":
            self.success = self.final = row
        elif outcome in ("deadline", "late"):
            self.final = row

    def next_action(self):
        """(when, kind) of this hour's next step, or None when it is finished."""
        backoff = min(BACKOFF_START * 2 ** (self.errors - 1), P) if self.errors else None
        if self.success:
            if self.rechecked:
                return None
            when = parse_instant(self.success["available_at"]) + RECHECK
            if self.errors:
                when = max(when, self.last_attempt + backoff)
            return when, "recheck"
        if self.final and self.final["outcome"] == "late":
            return None
        deadline = self.due + D
        if self.final is None:  # before D, or D passed but not yet recorded
            when = self.due if self.last_attempt is None else self.last_attempt + (backoff or P)
            return (deadline, "deadline") if when >= deadline else (when, "fetch")
        when = (self.last_attempt or deadline) + (backoff or HOUR)
        if when > deadline + LATE_WINDOW:
            return None
        return when, "fetch"


class Fetcher:
    def __init__(self, root, start_hour, base_url=BASE_URL, clock=None, clock_source=ntp_offset, end_hour=None):
        self.root = Path(root)
        self.archive = self.root / "archive"
        self.log_path = self.root / "fetch_log.csv"
        self.start_hour = start_hour
        self.end_hour = end_hour  # last tracked hour; None tracks forever
        self.base_url = base_url.rstrip("/") + "/"
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.clock_source = clock_source
        self.archive.mkdir(parents=True, exist_ok=True)
        self.hours = {}
        self.last_clock = None
        for row in read_log(self.log_path):
            self.apply(row)
        if not self.log_path.exists():
            self.log_path.write_text(",".join(COLUMNS) + "\n", encoding="utf-8")

    def apply(self, row):
        if row["outcome"] == "clock":
            self.last_clock = parse_instant(row["attempt_at"])
            return
        hour = parse_timestamp(row["source_file_hour"])
        self.hours.setdefault(hour, HourState(hour)).apply(row)

    def log(self, row):
        """Append one row and fsync it before acting on it."""
        row = {c: str(row.get(c, "")) for c in COLUMNS}
        with open(self.log_path, "a", encoding="utf-8", newline="") as f:
            f.write(",".join(csv_cell(row[c]) for c in COLUMNS) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.apply(row)

    def state(self, hour):
        return self.hours.setdefault(hour, HourState(hour))

    def next_action(self):
        """(when, hour, kind) of the earliest pending step across all tracked hours."""
        now = self.clock()
        if self.last_clock is None or now >= self.last_clock + CLOCK_EVERY:
            return now, None, "clock"
        best = None
        hour = self.start_hour
        while hour + HOUR <= now and (self.end_hour is None or hour <= self.end_hour):  # every due hour
            action = self.state(hour).next_action()
            if action and (best is None or action[0] < best[0]):
                best = (action[0], hour, action[1])
            hour += HOUR
        if best is None and self.end_hour is not None and hour > self.end_hour:
            return self.last_clock + CLOCK_EVERY, None, "clock"  # all done: only the clock remains
        if best is None:
            return hour + HOUR, hour, "fetch"  # the next hour's due time
        return best

    def tick(self):
        """Do the next step if it is due; return seconds to wait before the next call."""
        when, hour, kind = self.next_action()
        now = self.clock()
        if when > now:
            return (when - now).total_seconds()
        if kind == "fetch" and self.state(hour).final is None and now >= hour + HOUR + D:
            kind = "deadline"  # the fetcher was down past D: no attempt was made in time
        if kind == "clock":
            source, offset = self.clock_source()
            self.log({"attempt_at": format_instant(now), "outcome": "clock", "error": f"{source}; offset {offset}"})
        elif kind == "deadline":
            self.record_deadline(hour)
        else:
            self.attempt(hour, recheck=kind == "recheck")
        return 0

    def record_deadline(self, hour):
        """D passed without a success: the hour becomes missing, or the last incomplete version is used (L3)."""
        st = self.state(hour)
        last = st.last_incomplete or {}
        self.log({"source_file_hour": format_timestamp(hour), "attempt_at": format_instant(st.due + D),
                  "sha256": last.get("sha256", ""), "bytes": last.get("bytes", ""),
                  "decode_status": last.get("decode_status", ""), "outcome": "deadline",
                  "available_at": format_instant(st.due + D) if last else ""})

    def attempt(self, hour, recheck=False):
        st = self.state(hour)
        url = self.base_url + hour_file_name(hour)
        headers = {"User-Agent": USER_AGENT}
        if recheck and st.success["etag"]:
            headers["If-None-Match"] = st.success["etag"]
        row = {"source_file_hour": format_timestamp(hour), "attempt_at": format_instant(self.clock())}
        tmp = None
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as resp:
                row.update(http_status=resp.status, last_modified=resp.headers.get("Last-Modified", ""),
                           etag=resp.headers.get("ETag", ""))
                tmp, size, sha = self.download(resp)
                expected = resp.headers.get("Content-Length")
                if expected is not None and int(expected) != size:
                    raise OSError(f"body {size} bytes, Content-Length {expected}")
        except urllib.error.HTTPError as e:
            e.close()
            row["http_status"] = e.code
            if e.code == 304 and recheck:
                row["outcome"] = "unchanged"
            elif e.code == 404:
                row["outcome"] = "pending"
            else:
                row.update(outcome="error", error=f"HTTP {e.code}")
            return self.log(row)
        except Exception as e:  # network failure or short body; nothing reaches the archive
            if tmp:
                tmp.unlink()
            row.update(outcome="error", error=f"{type(e).__name__}: {e}")
            return self.log(row)
        row.update(bytes=size, sha256=sha)
        final = self.archive / f"{hour:%Y-%m-%d}-{hour.hour}" / f"{sha}.json.gz"
        final.parent.mkdir(exist_ok=True)
        if final.exists():
            tmp.unlink()  # identical content already archived; never rewrite it
        else:
            os.replace(tmp, final)
        read = HourRead(final.parent, hour)
        read.path = final
        for _ in read.lines():
            pass
        row.update(decode_status=read.status, error=read.error)
        if recheck:
            row["outcome"] = "unchanged" if sha == st.success["sha256"] else "republished"
        elif read.status != "present":
            row["outcome"] = "incomplete"
        elif st.final is not None:
            row["outcome"] = "late"
        else:  # available_at: the moment validation finished (§4)
            row.update(outcome="success", available_at=format_instant(self.clock()))
        self.log(row)

    def download(self, resp):
        """Stream the body to a temp file in the archive; return (path, size, sha256)."""
        sha = hashlib.sha256()
        size = 0
        fd, name = tempfile.mkstemp(dir=self.archive, suffix=".part")
        tmp = Path(name)
        try:
            with os.fdopen(fd, "wb") as f:
                while True:
                    chunk = resp.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
                    sha.update(chunk)
                    size += len(chunk)
                f.flush()
                os.fsync(f.fileno())
        except BaseException:
            tmp.unlink()
            raise
        return tmp, size, sha.hexdigest()

    def run_forever(self):
        while True:
            time.sleep(min(self.tick(), 60))


def export_manifest(root, out):
    """02 §8 manifest: every hour with a success, or a deadline row that used an incomplete version."""
    rows = []
    for row in read_log(Path(root) / "fetch_log.csv"):
        if row["outcome"] in ("success", "deadline") and row["available_at"]:
            rows.append((row["source_file_hour"], row["available_at"]))
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("source_file_hour,available_at\n")
        for hour, at in sorted(rows):
            f.write(f"{hour},{at}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m pipeline.fetcher")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("root", type=Path)
    p.add_argument("start_hour", type=parse_timestamp)
    p.add_argument("--base-url", default=BASE_URL)
    p.add_argument("--end-hour", type=parse_timestamp, help="last hour to track (default: forever)")
    p = sub.add_parser("manifest")
    p.add_argument("root", type=Path)
    p.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        Fetcher(args.root, args.start_hour, args.base_url, end_hour=args.end_hour).run_forever()
    else:
        export_manifest(args.root, args.out)


if __name__ == "__main__":
    sys.exit(main())
