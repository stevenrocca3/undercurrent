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
- **Depends:** none (latent).

## G10. R5 window bounds (§6): DECIDED 2026-10-14 (owner)
- **Decision:** inclusive at `t − 7d`, exclusive at `t`; `available_at <= t` inclusive.
- **Depends:** F12.

## G11. `event_time == t` in R5: DECIDED 2026-10-14 (owner)
- **Decision:** excluded (`< t`). **Not exercised.**

## G12. Registry statuses (§1): DECIDED 2026-10-14 (owner)
- **Decision:**
  - `missing` = no file.
  - `unreadable` = not gzip, or the stream fails before yielding any line; the hour contributes no lines.
  - `truncated` = the gzip stream ends early (EOF/CRC error) after yielding ≥ 1 line. Complete lines are kept, and the partial last line is Q1.
  - A bad line inside a fully decoded file does not change the status.
- **Depends:** F09 (`missing`), F16 (`truncated`), F17 (`unreadable`), F05 (`present` despite Q1).
- **Implementation note:** Python's `gzip.open` line iteration raises `EOFError` and never returns the partial line. Use `zlib.decompressobj(wbits=31)` to see it. See the F16 README.

## G13. Valid JSON that is not an object, and empty lines (§2): DECIDED 2026-10-14 (owner)
- **Decision:** Q1. Not exercised.

## G14. `public` and `payload` missing (§2): DECIDED 2026-10-14 (owner)
- **Decision:** **Q2.** Q2 required fields are `id`, `type`, `repo.id`, `actor.id`, `created_at`, `public`, `payload`. (§2's Q2 list needs the matching edit through change control.)
- **Depends:** F06 line 11 (no `payload` → Q2). A missing `public` is not exercised.

## G15. Star detection: DECIDED 2026-10-14 (owner)
- **Decision:** a star is `type == "WatchEvent"` and `payload.action == "started"` (exact string).
- **Depends:** F01 line 5 (IssuesEvent `opened` is not a star).

## G16. Required fields present as JSON `null`: DECIDED 2026-10-14 (owner)
- **Decision:** treated as missing → Q2. Not exercised.

## G17. `created_at` formats accepted (§2, Q3): DECIDED 2026-10-14 (owner)
- **Decision:** accept RFC 3339 with `Z` or a numeric offset, converted to UTC. Anything else is Q3.
- **Depends:** F14 (month 13 → Q3; `-02:00` offset → canonical at 00:50Z).

## G18. Files outside the requested range: DECIDED 2026-10-14 (owner)
- **Decision:** ignored. No fixture includes one.
