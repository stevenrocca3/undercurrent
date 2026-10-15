#!/usr/bin/env python3
"""Write every fixture's input/*.json.gz from the literal lines below.

This script ONLY writes inputs. It computes nothing about expected outputs.
Every input line is a raw string literal: what you read here is exactly the
bytes written to the file (plus a trailing "\n").

Deterministic: fixed line order, "\n" line endings, gzip mtime=0, no filename
in the gzip header.

Run from anywhere:  python3 fixtures/generate_inputs.py
"""
import gzip
import io
import os
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# F01 baseline hour (2026-09-01 hour 0). Reused verbatim by other fixtures.
# --------------------------------------------------------------------------
B1 = r'{"id":"1001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:05:00Z","org":{"id":901,"login":"acme"}}'
B2 = r'{"id":"1002","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:10:00Z"}'
B3 = r'{"id":"1003","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T00:15:00Z"}'
B4 = r'{"id":"1004","type":"WatchEvent","actor":{"id":203,"login":"carol"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:20:00Z"}'
B5 = r'{"id":"1005","type":"IssuesEvent","actor":{"id":202,"login":"bob"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"opened"},"public":true,"created_at":"2026-09-01T00:30:00Z"}'
B6 = r'{"id":"1006","type":"WatchEvent","actor":{"id":204,"login":"dave"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:40:00Z"}'

BASE = [B1, B2, B3, B4, B5, B6]

# --------------------------------------------------------------------------
# Fixtures: {fixture_dir: {input_file_name: [line, line, ...]}}
# --------------------------------------------------------------------------
FIXTURES = {
    "F01-clean-hour": {
        "2026-09-01-0.json.gz": BASE,
    },

    "F02-dup-within-file": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: byte-identical copy of B2 (line 2)
            r'{"id":"1002","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:10:00Z"}',
        ],
    },

    "F03-dup-across-files": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": [
            # line 1: byte-identical copy of B4 (hour 0, line 4)
            r'{"id":"1004","type":"WatchEvent","actor":{"id":203,"login":"carol"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:20:00Z"}',
            # line 2: new event
            r'{"id":"3001","type":"PushEvent","actor":{"id":203,"login":"carol"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T01:10:00Z"}',
        ],
    },

    "F04-conflicting-dup": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: same id as B2 but repo is 502/acme/zephyr instead of 501/acme/rocket
            r'{"id":"1002","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:10:00Z"}',
        ],
    },

    "F05-malformed-json": {
        "2026-09-01-0.json.gz": [
            B1,
            B2,
            B3,
            # line 4: JSON cut off mid-object
            r'{"id":"5001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":50',
            B4,
            B5,
            B6,
        ],
    },

    "F06-missing-required-field": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: no "id" key (a would-be star on 501) -> Q2
            r'{"type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:45:00Z"}',
            # line 8: "repo" has no "id" -> Q2
            r'{"id":"6002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}',
            # line 9: no "type" AND unparseable created_at -> Q2 (precedence, not Q3)
            r'{"id":"6003","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"not-a-date"}',
            # line 10: no actor.login, no org -> both nullable -> canonical (must NOT quarantine)
            r'{"id":"6004","type":"PushEvent","actor":{"id":206},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T00:55:00Z"}',
            # line 11: no "payload" key -> Q2 (G14, decided 2026-10-14)
            r'{"id":"6005","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"public":true,"created_at":"2026-09-01T00:58:00Z"}',
        ],
    },

    "F07-late-event": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: 1 second before source_file_hour - 1h (2026-08-31T23:00:00Z) -> late
            r'{"id":"7001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-08-31T22:59:59Z"}',
            # line 8: exactly source_file_hour - 1h -> NOT late (strict <)
            r'{"id":"7002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-08-31T23:00:00Z"}',
        ],
    },

    "F08-future-skewed": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: 1 second after source_file_hour + 2h (2026-09-01T02:00:00Z) -> future_skewed
            r'{"id":"8001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T02:00:01Z"}',
            # line 8: exactly source_file_hour + 2h -> NOT future_skewed (strict >)
            r'{"id":"8002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T02:00:00Z"}',
        ],
    },

    "F09-missing-hour": {
        "2026-09-01-0.json.gz": BASE,
        # 2026-09-01-1.json.gz deliberately absent
        "2026-09-01-2.json.gz": [
            r'{"id":"9001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T02:10:00Z"}',
            r'{"id":"9002","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T02:20:00Z"}',
        ],
    },

    "F10-unrecognized-type": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: type not in event_types.txt -> kept, flagged
            r'{"id":"10001","type":"MysteryEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}',
            # line 8: rare but recognized type -> NOT flagged
            r'{"id":"10002","type":"GollumEvent","actor":{"id":202,"login":"bob"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"pages":[]},"public":true,"created_at":"2026-09-01T00:55:00Z"}',
        ],
    },

    "F11-repo-renamed": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": [
            # line 1: repo 501 now called acme/rocket-ng
            r'{"id":"11001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket-ng"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T01:10:00Z"}',
            # line 2: a DIFFERENT repo (503) has taken the freed name acme/rocket
            r'{"id":"11002","type":"WatchEvent","actor":{"id":206,"login":"frank"},"repo":{"id":503,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T01:20:00Z"}',
        ],
    },

    "F12-point-in-time-trap": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": [
            # available_at = 01:00 + 7h = 08:00 -> exactly equal to cutoff 1 -> counted (<=)
            r'{"id":"12001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T01:10:00Z"}',
        ],
        "2026-09-01-2.json.gz": [
            # THE TRAP: event_time 02:10 < cutoff 1 (08:00), but available_at = 09:00 > 08:00
            r'{"id":"12002","type":"WatchEvent","actor":{"id":206,"login":"frank"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T02:10:00Z"}',
        ],
    },

    "F13-repeat-stars-one-actor": {
        "2026-09-01-0.json.gz": BASE + [
            # lines 7 and 8: bob (202) stars 501 again, twice; identical except id
            r'{"id":"13001","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:50:00Z"}',
            r'{"id":"13002","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:50:00Z"}',
        ],
    },

    "F14-q3-bad-timestamp": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: month 13 -> created_at fails to parse -> Q3 (would-be star on 501)
            r'{"id":"14001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-13-01T00:45:00Z"}',
            # line 8: bad created_at AND numeric id (Q4) -> Q3 wins (precedence Q1>Q2>Q3>Q4)
            r'{"id":14002,"type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"not-a-date"}',
            # line 9: valid RFC 3339 with -02:00 offset = 2026-09-01T00:50:00Z -> canonical (must NOT be Q3)
            r'{"id":"14003","type":"WatchEvent","actor":{"id":206,"login":"frank"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"started"},"public":true,"created_at":"2026-08-31T22:50:00-02:00"}',
        ],
    },

    "F15-q4-wrong-id-type": {
        "2026-09-01-0.json.gz": BASE + [
            # line 7: id is a JSON number, not a string -> Q4
            r'{"id":15001,"type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:45:00Z"}',
            # line 8: repo.id is a JSON string -> Q4 (would-be star on 501)
            r'{"id":"15002","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":"501","name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T00:50:00Z"}',
            # line 9: actor.id is a JSON string -> Q4
            r'{"id":"15003","type":"PushEvent","actor":{"id":"201","login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T00:55:00Z"}',
            # line 10: org.id is a JSON string -> NOT Q4 (G2: org cannot trigger Q4; org_id stored null)
            r'{"id":"15004","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T00:58:00Z","org":{"id":"901","login":"acme"}}',
        ],
    },

    # F16: gzip stream of the full F01 baseline, cut off mid-stream.
    # See write_truncated_gz: the cut is placed exactly at a Z_SYNC_FLUSH point
    # after B1..B4 + "\n" each and the first part of B5 (B5_HEAD, no newline).
    "F16-truncated-hour": {
        "2026-09-01-0.json.gz": ("truncated",),
    },

    # F17: hour 0 normal; hour 1 is NOT gzip (plain uncompressed JSON text
    # with a .json.gz name). A lenient reader that falls back to plain text
    # would wrongly count its star.
    "F17-unreadable-hour": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": ("raw", b'{"id":"17001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T01:10:00Z"}\n'),
    },
}

# F16 pieces. B5 split in two literal halves; B5_HEAD + B5_TAIL == B5.
B5_HEAD = r'{"id":"1005","type":"IssuesEvent","actor":{"id":202,"lo'
B5_TAIL = r'gin":"bob"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{"action":"opened"},"public":true,"created_at":"2026-09-01T00:30:00Z"}'
assert B5_HEAD + B5_TAIL == B5


def write_truncated_gz(path):
    """Gzip the full baseline B1..B6, but keep only the compressed bytes up to a
    sync-flush point placed right after B1..B4 (each + "\\n") and B5_HEAD.
    Any decoder then recovers exactly those bytes and then hits end-of-input
    before the gzip trailer (no CRC/size): a truncated stream."""
    recoverable = "".join(l + "\n" for l in (B1, B2, B3, B4)) + B5_HEAD
    lost = B5_TAIL + "\n" + B6 + "\n"
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(recoverable.encode("utf-8"))
        gz.flush(zlib.Z_SYNC_FLUSH)
        cut = buf.tell()  # the fixed offset: end of the sync-flushed block
        gz.write(lost.encode("utf-8"))
    with open(path, "wb") as f:
        f.write(buf.getvalue()[:cut])
    return cut


def write_gz(path, lines):
    data = "".join(line + "\n" for line in lines).encode("utf-8")
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(data)
    with open(path, "wb") as f:
        f.write(buf.getvalue())


def main():
    for fixture, files in FIXTURES.items():
        input_dir = os.path.join(HERE, fixture, "input")
        os.makedirs(input_dir, exist_ok=True)
        for name in os.listdir(input_dir):
            if name.endswith(".json.gz"):
                os.remove(os.path.join(input_dir, name))
        for name, spec in files.items():
            path = os.path.join(input_dir, name)
            if isinstance(spec, tuple) and spec[0] == "truncated":
                cut = write_truncated_gz(path)
                print(f"{fixture}/input/{name}: truncated gzip, {cut} bytes")
            elif isinstance(spec, tuple) and spec[0] == "raw":
                with open(path, "wb") as f:
                    f.write(spec[1])
                print(f"{fixture}/input/{name}: raw non-gzip bytes, {len(spec[1])} bytes")
            else:
                write_gz(path, spec)
                print(f"{fixture}/input/{name}: {len(spec)} lines")


if __name__ == "__main__":
    main()
