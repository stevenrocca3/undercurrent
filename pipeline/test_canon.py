"""Line classification tests (spec §2) for cases the fixtures don't cover.

    .venv/bin/python -m unittest pipeline/test_canon.py
"""

import json
import unittest
from datetime import datetime

from pipeline.canon import classify, parse_object, record_hash

GOOD = {"id": "1", "type": "PushEvent", "actor": {"id": 1, "login": "a"}, "repo": {"id": 2, "name": "o/r"},
        "payload": {"action": "started"}, "public": True, "created_at": "2026-09-01T00:00:00Z"}


def line(**changes):
    obj = dict(GOOD)
    for key, value in changes.items():
        if value is ...:
            del obj[key]
        else:
            obj[key] = value
    return json.dumps(obj).encode()


def code(raw, partial=False):
    return classify(raw, partial)[0]


class TestParseObject(unittest.TestCase):
    def test_keeps_raw_text_and_last_duplicate_wins(self):
        members = parse_object(' {"payload" : { "a" : 1.10 } , "id":"x", "id":"y"} \r')
        self.assertEqual(members["payload"], ({"a": 1.1}, '{ "a" : 1.10 }'))
        self.assertEqual(members["id"][0], json.loads('{"id":"x","id":"y"}')["id"])

    def test_rejects_what_json_rejects(self):
        for text in ['{"a":1}x', '{"a":1,}', "{'a':1}", '{"a":NaN}', '{"a":Infinity}', "﻿{}", "", "{"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_object(text)


class TestClassify(unittest.TestCase):
    def test_good_line(self):
        c, fields = classify(line(), False)
        self.assertEqual(c, "canonical")
        self.assertEqual(fields["event_time"], datetime(2026, 9, 1))
        self.assertEqual(fields["payload_action"], "started")

    def test_q1(self):
        self.assertEqual(code(line(), partial=True), "Q1")  # partial last line, even if it parses
        self.assertEqual(code(b'{"id":"1","type":"PushEvent","x":NaN}'), "Q1")
        self.assertEqual(code(line(id="\ud800")), "Q1")  # SPEC-GAPS G28: lone surrogate in a stored string

    def test_q2(self):
        self.assertEqual(code(line(repo=5)), "Q2")  # repo not an object: repo.id missing
        self.assertEqual(code(line(actor=None)), "Q2")
        self.assertEqual(code(line(created_at=None)), "Q2")
        self.assertEqual(code(line(public=False)), "canonical")  # false is present

    def test_q3(self):
        for value in ["2026-09-01T00:00:00+24:00", "2026-09-01T00:00:00+00:60", "2026-02-30T00:00:00Z",
                      "２026-09-01T00:00:00Z", "2026-09-01T00:00:00Z\n", " 2026-09-01T00:00:00Z",
                      "0001-01-01T00:00:00+01:00"]:
            with self.subTest(value=value):
                self.assertEqual(code(line(created_at=value)), "Q3")
        c, fields = classify(line(created_at="2026-09-01T00:00:00.5-00:30"), False)
        self.assertEqual(fields["event_time"], datetime(2026, 9, 1, 0, 30, 0, 500000))

    def test_q4_int64_bounds(self):
        self.assertEqual(code(line(repo={"id": 2**63 - 1})), "canonical")
        self.assertEqual(code(line(repo={"id": -2**63})), "canonical")
        self.assertEqual(code(line(repo={"id": 2**63})), "Q4")
        self.assertEqual(code(line(actor={"id": -2**63 - 1})), "Q4")
        self.assertEqual(code(line(actor={"id": False})), "Q4")

    def test_optional_fields_with_wrong_types_are_null(self):
        _, fields = classify(line(org={"id": "7"}, repo={"id": 2, "name": 5}, payload={"action": 1}), False)
        self.assertEqual((fields["org_id"], fields["repo_name"], fields["payload_action"]), (None, None, None))

    def test_non_string_type_keeps_raw_text_last_key_wins(self):
        _, fields = classify(b'{"type":"PushEvent","id":"1","type":[1, 2],"actor":{"id":1},"repo":{"id":2},'
                             b'"payload":{},"public":true,"created_at":"2026-09-01T00:00:00Z"}', False)
        self.assertEqual(fields["event_type"], "[1, 2]")  # G30 raw text, G31 last wins
        _, fields = classify(line(type="PushEvent"), False)
        self.assertEqual(fields["event_type"], "PushEvent")

    def test_record_hash_drops_one_trailing_cr(self):
        self.assertEqual(record_hash(b"x\r"), record_hash(b"x"))
        self.assertNotEqual(record_hash(b"x\r\r"), record_hash(b"x"))


if __name__ == "__main__":
    unittest.main()
