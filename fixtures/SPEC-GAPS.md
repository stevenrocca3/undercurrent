# Spec gaps found while writing the fixtures

These are places where `01-event-semantics.md` v0.2 was silent or ambiguous, so the fixtures had to assume something. Steven decided every entry on 2026-10-14. Folding them into the spec itself still has to go through change control (§10). Each entry gives the section, the gap, the decision, and the fixtures that depend on it.

## G1. Quarantine precedence (§2): DECIDED 2026-10-14 (owner)
- **Gap:** "exactly one reason code", but no order is given when a line fails several checks.
- **Decision:** first match wins, checked in the order Q1 → Q2 → Q3 → Q4.
- **Depends:** F06 line 9 (no `type` + bad date → **Q2**); F14 line 8 (bad date + numeric `id` → **Q3**).

## G2. Q4 "ID field of the wrong JSON type" (§2): DECIDED 2026-10-14 (owner)
- **Decision:**
  - `id` must be a JSON **string**; a numeric `id` is **Q4** (never cast).
  - `actor.id` and `repo.id` must be JSON **integers**.
  - `org.id` **cannot** trigger Q4: `org` is optional, and a wrong-typed `org.id` is stored as `org_id = null`.
  - A JSON `null` in `id`/`actor.id`/`repo.id` is treated as **missing → Q2**.
- **Depends:** F15 (numeric `id`, string `repo.id`, string `actor.id` → Q4; string `org.id` → canonical); F14 line 8.

## G3. `record_hash` input (§2): DECIDED 2026-10-14 (owner)
- **Decision:** the raw bytes of the line as read, **excluding** the trailing `\n` (and `\r` if present).
- **Depends:** F02, F03 (identical bytes → conflict 0); F04 (different bytes → conflict 1).

## G4. Recognized event types (§2): DECIDED 2026-10-14 (owner), list under review
- **Decision:** `event_types.txt` = the 16 types on GitHub's "GitHub event types" docs page as fetched on 2026-10-14. Matching is exact and case-sensitive. Older types such as `SponsorshipEvent`, `PullRequestReviewThreadEvent`, `GistEvent` and `FollowEvent` would be flagged. Steven is checking the list against real September 2026 data.
- **Depends:** F10; all fixtures (base types must be listed).

## G5. R1 definition (§6): DECIDED 2026-10-14 (owner)
- **Decision:** `canonical` = lines that became canonical records **before** dedup. canonical + ΣQ = total input lines recovered from readable files. Rows are always present.
- **Depends:** F02, F03, F04, F16 (5 recovered lines, not 6).

## G6. R3 definitions (§3, §6): DECIDED 2026-10-14 (owner)
- **Decision:** distinct_event_ids = distinct `event_id` among canonical records (quarantined lines excluded). duplicate_count = **discarded** occurrences. conflict_count = discarded occurrences whose `record_hash` differs from the **kept** one.
- **Depends:** F02, F03, F04, F06, F14, F15.

## G7. `conflicts` table contents (§3): DECIDED 2026-10-14 (owner)
- **Decision:** not part of the fixture CSV contract. Only `conflict_count` in r3 is checked.
- **Depends:** F04.

## G8. Row order of r1 and flags: DECIDED 2026-10-14 (owner)
- **Decision:** rows are sorted by every column in byte order. r1 = `Q1,Q2,Q3,Q4,canonical`; flags = `future_skewed,late,unrecognized_type`.
- **Depends:** all fixtures.

## G9. Flags counted after dedup (§4): DECIDED 2026-10-14 (owner)
- **Decision:** flags are counted over **kept** occurrences only, using the kept occurrence's `source_file_hour`.
- **Depends:** F26.

## G10. R5 window bounds (§6): DECIDED 2026-10-14 (owner)
- **Decision:** inclusive at `t − 7d`, exclusive at `t`; `available_at <= t` inclusive.
- **Depends:** F12, F27.

## G11. `event_time == t` in R5: DECIDED 2026-10-14 (owner)
- **Decision:** excluded (`< t`).
- **Depends:** F27.

## G12. Registry statuses (§1): DECIDED 2026-10-14 (owner)
- **Decision:**
  - `missing` = no file.
  - `unreadable` = not gzip, or the stream fails before yielding any complete line; the hour contributes no lines.
  - `truncated` = the gzip stream ends early (EOF/CRC error) after yielding ≥ 1 complete line. Complete lines are kept, and the partial last line is Q1.
  - A bad line inside a fully decoded file does not change the status.
- **Depends:** F09 (`missing`), F16 (`truncated`), F17 (`unreadable`), F05 (`present` despite Q1), F23.
- **Implementation note:** Python's `gzip.open` line iteration raises `EOFError` and never returns the partial line. Use `zlib.decompressobj(wbits=31)` to see it. See the F16 README.

## G13. Valid JSON that is not an object, and empty lines (§2): DECIDED 2026-10-14 (owner)
- **Decision:** Q1.
- **Depends:** F18.

## G14. `public` and `payload` missing (§2): DECIDED 2026-10-14 (owner)
- **Decision:** **Q2.** Q2 required fields are `id`, `type`, `repo.id`, `actor.id`, `created_at`, `public`, `payload`.
- **Depends:** F06 line 11 (no `payload` → Q2), F19 (no `public` → Q2).

## G15. Star detection: DECIDED 2026-10-14 (owner)
- **Decision:** a star is `type == "WatchEvent"` and `payload.action == "started"` (exact string).
- **Depends:** F01 line 5 (IssuesEvent `opened` is not a star).

## G16. Required fields present as JSON `null`: DECIDED 2026-10-14 (owner)
- **Decision:** treated as missing → Q2.
- **Depends:** F19.

## G17. `created_at` formats accepted (§2, Q3): DECIDED 2026-10-14 (owner)
- **Decision:** accept RFC 3339 with `Z` or a numeric offset, converted to UTC. Anything else is Q3.
- **Depends:** F14 (month 13 → Q3; `-02:00` offset → canonical at 00:50Z), F21 (`+05:30` offset).

## G18. Files outside the requested range: DECIDED 2026-10-14 (owner)
- **Decision:** ignored.
- **Depends:** F25.

## G19. `type`, `public`, and `payload` type checks (§2): DECIDED 2026-10-14 (owner, spec v0.6)
- **Decision:** `type`, `public`, and `payload` are checked for presence only, not JSON type. A non-string `type` is stored as its JSON text and flagged `unrecognized_type`.
- **Depends:** F22.

## G20. `unreadable` vs complete lines (§1): DECIDED 2026-10-14 (owner, spec v0.6)
- **Decision:** `unreadable` = decompression fails before yielding any *complete* line; partial bytes are discarded and not counted as Q1.
- **Depends:** F23 hour 1.

## G21. Trailing non-gzip bytes after complete member (§1): DECIDED 2026-10-14 (owner, spec v0.6)
- **Decision:** non-gzip bytes after a complete gzip member make the hour `truncated`.
- **Depends:** F23 hour 2.

## G22. Q3 timestamp parsing strictness (§2): DECIDED 2026-10-14 (owner, spec v0.6)
- **Decision:** strict form `YYYY-MM-DDTHH:MM:SS[.f{1,6}](Z|±HH:MM)`: uppercase `T` and `Z`, at most 6 fractional digits, no leap second `:60`.
- **Depends:** F21.

## G23. `repo.id` / `actor.id` outside int64 range (§2, Q4): DECIDED 2026-10-14 (owner)
- **Gap:** §2 states `actor.id` and `repo.id` are int64, and Q4 requires them to be integers. The spec does not state whether an integer exceeding 64-bit signed bounds (`[-2^63, 2^63 - 1]`) triggers Q4, is rejected, or is an error.
- **Decision:** Q4. Folded into §2 in v0.7.
- **Depends:** none (not exercised).

## G24. CSV quoting and escaping rules (§6): DECIDED 2026-10-14 (owner)
- **Gap:** §6 specifies CSV column formats but does not specify RFC 4180 escaping/quoting when cell content contains commas, quotes, or newlines (e.g. if a non-string `type` was a JSON object `{"a":1,"b":2}`).
- **Decision:** RFC 4180 quoting with LF line endings. A cell containing `,`, `"` or a line break is quoted, with inner `"` doubled; nothing else is quoted, and cell text is never trimmed. Folded into §6 in v0.7.
- **Depends:** none (F22 uses `[1]`, which needs no quoting).

## G25. Invalid UTF-8 bytes in canonical fields (§2): DECIDED 2026-10-14 (owner)
- **Gap:** If invalid UTF-8 bytes occur inside a canonical field (e.g. non-string or raw field that decoded partially), writing it to CSV would violate UTF-8 encoding rules (§6).
- **Decision:** a line containing invalid UTF-8 anywhere is Q1, so no canonical field can hold it. Folded into §2 in v0.7.
- **Depends:** F18 line 13.

## G26. Registry evidence when reading local files (§1, §8 criterion 5): DECIDED 2026-10-15 (owner, spec v0.8)
- **Gap:** §1 says every hour's status comes "with the evidence (HTTP status, byte count, decompression error)". The Gate 1 pipeline reads hour files from a local `INPUT_DIR` (brief interface), so it has no HTTP status. The spec also doesn't say where the evidence goes: `registry.csv` (§6) holds only `source_file_hour,status`.
- **Decision:** the provisional behaviour, folded into §1 in v0.8. The pipeline writes `registry_evidence.csv` beside `registry.csv`, with columns `source_file_hour,status,file_bytes,lines,error` (`file_bytes` empty when `missing`; `error` is the decompression error text, empty when `present`). It is not compared. No HTTP status column until something downloads the files and records it.
- **Depends:** none (not compared by any fixture).

## G27. Non-quarantining fields that are missing or the wrong JSON type (§2): DECIDED 2026-10-15 (owner, spec v0.9)
- **Gap:** §2 marks `repo_name` and `is_public` as non-null, but no quarantine rule covers a missing or non-string `repo.name`, and F22 makes `"public": "yes"` canonical, so `is_public` has no bool to hold. §2 also doesn't say what a non-string `actor.login` or `payload.action` becomes.
- **Decision:** store null (folded into §2 in v0.9). `is_public` is null when `public` is not a JSON bool, and `repo_name`, `actor_login` and `payload_action` are null when the source is missing or not a string. `repo_name` and `is_public` are nullable columns in the pipeline's canonical table. None of these fields reaches R1–R7: star detection needs `payload.action == "started"` exactly, so null is not a star.
- **Depends:** F22 line 8 (canonical with `is_public` null). Nothing compared depends on it.

## G28. A JSON string escape that is not valid Unicode, e.g. `"\ud800"` (§2, G25): DECIDED 2026-10-15 (owner, spec v0.9)
- **Gap:** a lone-surrogate escape is valid JSON grammar in valid UTF-8 bytes, so neither Q1 rule catches it. But the decoded string can't be written as UTF-8, which is the problem G25 meant to rule out. It matters when it lands in a stored string (`id`, `type`, `actor.login`, `repo.name`, `payload.action`); `event_type` reaches r2.csv.
- **Decision:** `Q1` when any of those stored strings holds a lone surrogate after decoding. `payload_raw` keeps the payload's raw text, where the escape is plain ASCII, so a lone surrogate inside the payload doesn't quarantine the line.
- **Depends:** no fixture. `pipeline/test_canon.py` covers it.

## G29. `ingested_at` and byte-identical replay vs batch (§2, §4): DECIDED 2026-10-15 (owner, spec v0.9)
- **Gap:** §2 sets `ingested_at` from the pipeline clock, and §4 requires byte-identical canonical tables from replay and batch on identical input. Two runs never share a clock reading, so a content hash over every column can never match.
- **Decision:** the replay-vs-batch byte-identity check excludes `ingested_at` and `source_last_modified` (§4 Replay, v0.9). The pipeline sets `ingested_at` once per run.
- **Depends:** none yet.

## G30. Text of a non-string `type` (§2): DECIDED 2026-10-15 (owner, spec v0.10)
- **Gap:** "stored as its JSON text" could mean the raw text in the line or a re-serialization; they differ for `[1,2]` vs `[1, 2]`, key spacing, `1.0` vs `1`. It reaches r2.
- **Decision:** the raw JSON text as it appears in the line, not re-serialized. (Raised by the reference agent; the pipeline already did this.)
- **Depends:** F22 (`[1]`, where both readings agree).

## G31. Repeated keys in one JSON object (§2): DECIDED 2026-10-15 (owner, spec v0.11)
- **Gap:** RFC 8259 leaves repeated keys undefined; some parsers keep the first, some the last, some reject.
- **Decision:** the last occurrence wins at every level, for every check and field, including the raw `type` text. `record_hash` is unaffected. (Raised by the reference agent; the pipeline already did this: `parse_object` at the top level, `json.loads` below it.)
- **Depends:** none (not exercised by a fixture).

## G32. `payload_raw` for a full month does not fit on the Gate 1 machine (§2, brief scale constraint): DECIDED 2026-10-15 (owner, spec v0.12)
- **Gap:** §2 requires `payload_raw` (not null) on every canonical record. One real hour (`2026-09-15-15`: 81,136 canonical rows) takes 273 MiB in `canon.duckdb`, or 3,528 bytes per row. 256 MB of that is `payload_raw`, which DuckDB stores uncompressed. For 720 hours that's about 200 GB (58M rows) to 250 GB (70M rows), against about 31 GB of free disk. Even the gzip source alone (61.7 MB for this hour) comes to about 44 GB for the month.
- **Options:** (a) don't store `payload_raw` in the month run; it is reachable from `(source_file_hour, source_line)` plus the source file, so it would be fetched on demand, and no R1–R7 output reads it; (b) store it compressed (e.g. zstd per row); this still needs measuring, and it probably still doesn't fit; (c) run on a bigger disk.
- **Decision:** option (a). Gate 1 runs store `payload_raw` as null. The payload stays recoverable via `source_file_hour` + `source_line`, the manifest SHA-256 (§8) and `record_hash` (§2, v0.12).
- **Depends:** none (no fixture is affected).

## G33. `available_at` manifest validation (02 §8): DECIDED 2026-10-15 (owner, spec 02 v0.4)
- **Gap:** 02 §8 only said a value without an offset is an error. It didn't cover: a repeated hour; more than 6 fractional digits; a non-`Z` offset; a bad header; listed hours outside the requested range; an `available_at` earlier than `source_file_hour + 1h`.
- **Decision:** as the pipeline proposed. A repeated hour, a bad header, or a value that isn't the 01 §2 Q3 instant form (offset required, 1–6 fractional digits) is an error, and the run stops. Any offset is accepted and converted to UTC. Listed hours outside the requested range are ignored. An early `available_at` is used as given. (Raised by the pipeline. A black-box probe found the reference accepting 7-digit fractions, repeated hours, a space separator and the compact form; it was tightened to match.)
- **Depends:** `tools/test_manifest_errors.py` runs both implementations black-box on every case.

## G34. Fetch-log rows the spec does not define (02 §4, §5.2, §6): DECIDED 2026-10-16 (owner, spec 02 v0.6)
- **Gap:** §4 says `available_at` and the NTP offset are "recorded in the fetch log", but §5.2's columns have no place for either. §5.2's `outcome` list lacks `republished` (§6), the result of a recheck that found the same content, the final outcome of an hour that reaches `D` (§8.4 needs one), and what a 404 after `D` is. L3 covers only truncated versions at `D`, not `unreadable` ones. It is also unsaid whether an hour the fetcher never tried before `D` (downtime) counts as missing.
- **Provisional (pipeline):** an extra last column `available_at` (success and deadline rows); `outcome = deadline`, a row written when `D` passes without a success (no request; `attempt_at` = the deadline; the last incomplete version's `sha256`, `bytes` and `decode_status`, and `available_at` = the deadline, or all empty when there was none: `missing`); `outcome = unchanged` for a recheck with 304 or the same SHA-256; `outcome = clock` rows (empty hour) with `"<source>; offset <value>"` in `error`; 404 after `D` stays `pending`; the last incomplete version is used at `D` whether `truncated` or `unreadable`; downtime past `D` makes the hour missing (no late `available_at`). The manifest lists success rows and deadline rows that used a version.
- **Decision:** the provisional rules, except the clock.
  - Clock offsets go to a separate `clock.csv` (`checked_at, source, offset_seconds, error`; 02 §5.4), not to `outcome = clock` rows. This keeps the fetch log at one row per attempt, and gives the delay report a number.
  - Also written into 02: `republished` in the outcome list; an hour's final outcome is its `success` or `deadline` row; and §9 now says downtime past `D` makes an hour `missing`.
- **Depends:** `pipeline/test_fetcher.py`.

## G35. Percentile method and "round up" in the delay report (02 §7): DECIDED 2026-10-16 (owner, spec 02 v0.7)
- **Gap:** §7 asks for p50, p90 and p99 of the delay but doesn't name a percentile method. With 336 samples, methods differ (nearest-rank, linear interpolation). It also says to round the p99 "up to the next whole hour" without saying what an exact whole hour becomes.
- **Provisional (reference author, `tools/delay_report.py`):** nearest-rank (the value at rank ⌈q·n⌉), which is always an observed delay and matches §7's "about 3 hours above it". `L = ⌈p99 / 1 h⌉`, so an exact 2 h stays 2 h.
- **Decision:** the provisional rule, now in 02 §7.
- **Depends:** `tools/test_delay_report.py`.
