# F13: repeated star events from one actor

Bob (actor 202) stars repo 501 three times: baseline line 2, plus lines 7 and 8. Each has a distinct event id, so they are three separate events (§3: "never deduplicate on repo_id or actor_id"). Gross star events, not net stars and not unique stargazers.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 8 lines.

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline (line 2 = bob stars 501 at 00:10) | baseline |
| 7 | 13001 | WatchEvent `started`, bob 202, repo 501, 00:50:00 | repeat star |
| 8 | 13002 | identical to line 7 **except id** (same actor, repo, created_at, payload) | repeat star; content-based dedup would wrongly merge it |

## Expected outputs, derived

- **r1:** canonical = **8**; Q* = 0.
- **r2:** hour 00: Issues **1**, Push **2**, Watch = 2, 4, 6, 7, 8 = **5**.
- **r3:** 8 distinct ids, 0 duplicates, 0 conflicts. Lines 7 and 8 differ in `id`, so they are not duplicates.
- **r4:** 501 = 1002, 1006, 13001, 13002 = **4**; 502 = **1**.
- **r5:** 501 = **4**, 502 = **1** (all available 07:00, before t).
- **registry:** `present`. **flags:** all 0.
