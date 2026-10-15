# F08: future-skewed event

F01 plus one future-skewed star and one row exactly on the future boundary.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 8 lines.
- Future rule (§4): `event_time > source_file_hour + 2h` = `event_time > 2026-09-01T02:00:00Z` (strict).

## Input lines

| line | id | content | intent |
|---|---|---|---|
| 1-6 | 1001-1006 | F01 baseline | baseline |
| 7 | 8001 | WatchEvent `started`, erin 205, repo 502, created **2026-09-01T02:00:01Z** | future-skewed: 1 s past the bound |
| 8 | 8002 | PushEvent, alice, repo 501, created **2026-09-01T02:00:00Z** | exactly on the bound, so **not** future-skewed (strict `>`) |

## Expected outputs, derived

- **r1:** canonical = **8**; Q* = 0.
- **r2:** both in hour 00 (by file). Push = 1, 3, 8 = **3**; Watch = 2, 4, 6, 7 = **4**; Issues = **1**.
- **r3:** 8, 0, 0.
- **r4:** 8001 is on 2026-09-01 for repo 502. 501 = **2**, 502 = 1 + 1 = **2**.
- **r5:** t = 2026-09-02T00:00:00Z. 02:00:01 is before t, and `available_at` = 07:00 (from the **file** hour, not event_time) <= t. 501 = **2**, 502 = **2**.
- **registry:** `present`.
- **flags:** future_skewed = **1** (line 7 only), late = 0, unrecognized_type = 0.
