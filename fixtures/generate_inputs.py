#!/usr/bin/env python3
"""Write every fixture's input/*.json.gz from the literal lines below.

This script ONLY writes inputs. It computes nothing about expected outputs.
Every input line is a raw string literal: what you read here is exactly the
bytes written to the file (plus a trailing "\\n").

Deterministic: fixed line order, "\\n" line endings, gzip mtime=0, no filename
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
# F18 lines (Q1 non-object, empty line, invalid UTF-8)
# --------------------------------------------------------------------------
F18_Q1_ARRAY = r'[1, 2]'
F18_Q1_NUM = r'42'
F18_Q1_STR = r'"x"'
F18_CANON_1 = r'{"id":"18001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F18_Q1_EMPTY = ""
F18_CANON_2 = r'{"id":"18002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:51:00Z"}'
F18_Q1_BAD_UTF8 = b'{"id":"18003",\xff\xfe}'

# --------------------------------------------------------------------------
# F19 lines (Q2 null and missing)
# --------------------------------------------------------------------------
F19_Q2_ID_NULL = r'{"id":null,"type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F19_Q2_PAYLOAD_NULL = r'{"id":"19002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":null,"public":true,"created_at":"2026-09-01T00:51:00Z"}'
F19_Q2_REPO_ID_NULL = r'{"id":"19003","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":null,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:52:00Z"}'
F19_Q2_NO_PUBLIC = r'{"id":"19004","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"created_at":"2026-09-01T00:53:00Z"}'
F19_Q2_REPO_EMPTY = r'{"id":"19005","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{},"payload":{},"public":true,"created_at":"2026-09-01T00:54:00Z"}'

# --------------------------------------------------------------------------
# F20 lines (Q4 types and precedence)
# --------------------------------------------------------------------------
F20_Q4_BOOL_REPO = r'{"id":"20001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":true,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F20_Q4_FLOAT_ACTOR = r'{"id":"20002","type":"PushEvent","actor":{"id":201.0,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:51:00Z"}'
F20_Q2_BEATS_Q4 = r'{"id":20003,"type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"created_at":"2026-09-01T00:52:00Z"}'

# --------------------------------------------------------------------------
# F21 lines (Q3 strictness)
# --------------------------------------------------------------------------
F21_Q3_LOWER_Z = r'{"id":"21001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00z"}'
F21_Q3_LOWER_T = r'{"id":"21002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01t00:50:00Z"}'
F21_Q3_NO_SECS = r'{"id":"21003","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50Z"}'
F21_Q3_DATE_ONLY = r'{"id":"21004","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01"}'
F21_Q3_LEAP_SEC = r'{"id":"21005","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T23:59:60Z"}'
F21_Q3_7_DIGITS = r'{"id":"21006","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00.1234567Z"}'
F21_Q3_NUMERIC = r'{"id":"21007","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":1788220800}'
F21_CANON_6_DIGITS = r'{"id":"21008","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00.123456Z"}'
F21_CANON_OFFSET = r'{"id":"21009","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T05:00:00+05:30"}'

# --------------------------------------------------------------------------
# F22 lines (type/public/payload wrong types)
# --------------------------------------------------------------------------
F22_TYPE_ARRAY = r'{"id":"22001","type":[1],"actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F22_PUBLIC_STRING = r'{"id":"22002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":"yes","created_at":"2026-09-01T00:51:00Z"}'
F22_PAYLOAD_STRING = r'{"id":"22003","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":"x","public":true,"created_at":"2026-09-01T00:52:00Z"}'

# --------------------------------------------------------------------------
# F23 lines (registry corner cases)
# --------------------------------------------------------------------------
F23_LINE_H2 = r'{"id":"23201","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T02:10:00Z"}'
F23_LINE_H5A = r'{"id":"23501","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T05:10:00Z"}'
F23_LINE_H5B = r'{"id":"23502","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":502,"name":"acme/zephyr"},"payload":{},"public":true,"created_at":"2026-09-01T05:20:00Z"}'
F23_LINE_H6 = r'{"id":"23601","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T06:10:00Z"}'

# --------------------------------------------------------------------------
# F24 lines (line endings)
# --------------------------------------------------------------------------
F24_LINE_7 = r'{"id":"24001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F24_LINE_8 = r'{"id":"24001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:50:00Z"}'
F24_LINE_9 = r'{"id":"24002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:55:00Z"}'

# --------------------------------------------------------------------------
# F25 lines (hours outside requested range)
# --------------------------------------------------------------------------
F25_LINE_1 = r'{"id":"25001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T01:10:00Z"}'
F25_LINE_2 = r'{"id":"25002","type":"WatchEvent","actor":{"id":202,"login":"bob"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T01:20:00Z"}'

# --------------------------------------------------------------------------
# F26 lines (flags from kept occurrence)
# --------------------------------------------------------------------------
F26_LINE_KEPT_FUTURE = r'{"id":"26001","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T02:30:00Z"}'
F26_LINE_KEPT_NORMAL = r'{"id":"26002","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T00:30:00Z"}'
F26_LINE_H1 = r'{"id":"26003","type":"PushEvent","actor":{"id":201,"login":"alice"},"repo":{"id":501,"name":"acme/rocket"},"payload":{},"public":true,"created_at":"2026-09-01T01:10:00Z"}'

# --------------------------------------------------------------------------
# F27 lines (R5 boundary conditions)
# --------------------------------------------------------------------------
F27_STAR_AT_T_MINUS_7D = r'{"id":"27001","type":"WatchEvent","actor":{"id":205,"login":"erin"},"repo":{"id":501,"name":"acme/rocket"},"payload":{"action":"started"},"public":true,"created_at":"2026-08-25T07:00:00Z"}'
F27_STAR_AT_T = r'{"id":"27002","type":"WatchEvent","actor":{"id":206,"login":"frank"},"repo":{"id":503,"name":"acme/comet"},"payload":{"action":"started"},"public":true,"created_at":"2026-09-01T07:00:00Z"}'

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

    "F18-q1-non-object-and-bytes": {
        "2026-09-01-0.json.gz": BASE + [
            F18_Q1_ARRAY,
            F18_Q1_NUM,
            F18_Q1_STR,
            F18_CANON_1,
            F18_Q1_EMPTY,
            F18_CANON_2,
            F18_Q1_BAD_UTF8,
        ],
    },

    "F19-q2-null-and-missing": {
        "2026-09-01-0.json.gz": BASE + [
            F19_Q2_ID_NULL,
            F19_Q2_PAYLOAD_NULL,
            F19_Q2_REPO_ID_NULL,
            F19_Q2_NO_PUBLIC,
            F19_Q2_REPO_EMPTY,
        ],
    },

    "F20-q4-id-types-and-precedence": {
        "2026-09-01-0.json.gz": BASE + [
            F20_Q4_BOOL_REPO,
            F20_Q4_FLOAT_ACTOR,
            F20_Q2_BEATS_Q4,
        ],
    },

    "F21-q3-timestamp-strictness": {
        "2026-09-01-0.json.gz": BASE + [
            F21_Q3_LOWER_Z,
            F21_Q3_LOWER_T,
            F21_Q3_NO_SECS,
            F21_Q3_DATE_ONLY,
            F21_Q3_LEAP_SEC,
            F21_Q3_7_DIGITS,
            F21_Q3_NUMERIC,
            F21_CANON_6_DIGITS,
            F21_CANON_OFFSET,
        ],
    },

    "F22-type-public-payload-wrong-types": {
        "2026-09-01-0.json.gz": BASE + [
            F22_TYPE_ARRAY,
            F22_PUBLIC_STRING,
            F22_PAYLOAD_STRING,
        ],
    },

    "F23-registry-corner-cases": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": ("cut_inside_first_line",),
        "2026-09-01-2.json.gz": ("trailing_bytes", [F23_LINE_H2], b"EXTRA_NON_GZIP_BYTES"),
        "2026-09-01-3.json.gz": ("raw", b""),
        "2026-09-01-4.json.gz": ("empty_gzip",),
        "2026-09-01-5.json.gz": ("multi_member", [[F23_LINE_H5A], [F23_LINE_H5B]]),
        "2026-09-01-6.json.gz": ("corrupt_crc", [F23_LINE_H6]),
    },

    "F24-line-endings-and-cr": {
        "2026-09-01-0.json.gz": (
            "raw_chunks",
            [b.encode("utf-8") + b"\n" for b in BASE]
            + [
                F24_LINE_7.encode("utf-8") + b"\r\n",
                F24_LINE_8.encode("utf-8") + b"\n",
                F24_LINE_9.encode("utf-8"),  # no trailing newline
            ],
        ),
    },

    "F25-hours-outside-requested-range": {
        "2026-09-01-0.json.gz": BASE,
        "2026-09-01-1.json.gz": [F25_LINE_1, F25_LINE_2],
        "2026-09-01-2.json.gz": [BASE[0], BASE[1]],
    },

    "F26-flags-from-kept-occurrence": {
        "2026-09-01-0.json.gz": BASE + [F26_LINE_KEPT_FUTURE, F26_LINE_KEPT_NORMAL],
        "2026-09-01-1.json.gz": [F26_LINE_H1],
        "2026-09-01-2.json.gz": [F26_LINE_KEPT_FUTURE, F26_LINE_KEPT_NORMAL],
    },

    "F27-r5-boundary-conditions": {
        "2026-09-01-0.json.gz": BASE + [F27_STAR_AT_T_MINUS_7D, F27_STAR_AT_T],
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


def write_cut_inside_first_line_gz(path):
    """Gzip B1, but cut compressed output at 25 bytes so that decompression fails
    before yielding any complete line: unreadable stream."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(B1.encode("utf-8") + b"\n")
    with open(path, "wb") as f:
        f.write(buf.getvalue()[:25])


def write_gz_with_trailing(path, lines, trailing_bytes):
    """Write complete gzip member followed by non-gzip bytes."""
    buf = io.BytesIO()
    data = "".join(line + "\n" for line in lines).encode("utf-8")
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(data)
    with open(path, "wb") as f:
        f.write(buf.getvalue() + trailing_bytes)


def write_empty_gz(path):
    """Write valid gzip file of empty content."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        pass
    with open(path, "wb") as f:
        f.write(buf.getvalue())


def write_multi_member_gz(path, members_lines):
    """Write two or more concatenated valid gzip members."""
    out = io.BytesIO()
    for lines in members_lines:
        buf = io.BytesIO()
        data = "".join(line + "\n" for line in lines).encode("utf-8")
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
            gz.write(data)
        out.write(buf.getvalue())
    with open(path, "wb") as f:
        f.write(out.getvalue())


def write_corrupt_crc_gz(path, lines):
    """Write a valid gzip member then flip bits in the 4-byte CRC trailer."""
    buf = io.BytesIO()
    data = "".join(line + "\n" for line in lines).encode("utf-8")
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(data)
    raw = bytearray(buf.getvalue())
    # CRC32 is at offset -8 to -4
    raw[-8] ^= 0xFF
    raw[-7] ^= 0xFF
    with open(path, "wb") as f:
        f.write(raw)


def write_raw_chunks_gz(path, chunks):
    """Write raw byte chunks directly into a valid gzip member."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        for c in chunks:
            gz.write(c)
    with open(path, "wb") as f:
        f.write(buf.getvalue())


def write_gz(path, lines):
    parts = []
    for line in lines:
        if isinstance(line, bytes):
            parts.append(line if line.endswith(b"\n") else line + b"\n")
        else:
            parts.append(line.encode("utf-8") + b"\n")
    data = b"".join(parts)
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
            elif isinstance(spec, tuple) and spec[0] == "cut_inside_first_line":
                write_cut_inside_first_line_gz(path)
                print(f"{fixture}/input/{name}: cut inside first line, 25 bytes")
            elif isinstance(spec, tuple) and spec[0] == "trailing_bytes":
                write_gz_with_trailing(path, spec[1], spec[2])
                print(f"{fixture}/input/{name}: gzip with trailing non-gzip bytes")
            elif isinstance(spec, tuple) and spec[0] == "empty_gzip":
                write_empty_gz(path)
                print(f"{fixture}/input/{name}: valid empty gzip")
            elif isinstance(spec, tuple) and spec[0] == "multi_member":
                write_multi_member_gz(path, spec[1])
                print(f"{fixture}/input/{name}: multi-member gzip")
            elif isinstance(spec, tuple) and spec[0] == "corrupt_crc":
                write_corrupt_crc_gz(path, spec[1])
                print(f"{fixture}/input/{name}: gzip with corrupted CRC trailer")
            elif isinstance(spec, tuple) and spec[0] == "raw_chunks":
                write_raw_chunks_gz(path, spec[1])
                print(f"{fixture}/input/{name}: raw chunks gzip")
            else:
                write_gz(path, spec)
                print(f"{fixture}/input/{name}: {len(spec)} lines")


if __name__ == "__main__":
    main()
