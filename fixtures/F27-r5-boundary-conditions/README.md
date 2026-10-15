# F27: R5 point-in-time boundary conditions: event_time == t, event_time == t - 7d, available_at == t

F01 plus lines testing R5 point-in-time window and availability boundaries (§4, §6, SPEC-GAPS G10, G11):
- Cutoff $t = \text{2026-09-01T07:00:00Z}$. Lookback window $[t - 7\text{d}, t) = [\text{2026-08-25T07:00:00Z}, \text{2026-09-01T07:00:00Z})$.
- Hour 0 file has `available_at = 00:00 + 1h + 6h = 2026-09-01T07:00:00Z`, so `available_at == t` for all events in this file. Tests that `available_at <= t` includes records with `available_at == t`.
- Line 7 (Event 27001): WatchEvent `started` on Repo 501 with `created_at = "2026-08-25T07:00:00Z"` (exactly $t - 7\text{d}$). Tests that the lookback window is inclusive on the left ($[t - 7\text{d}, t)$ includes $t - 7\text{d}$). Included in R5!
- Line 8 (Event 27002): WatchEvent `started` on Repo 503 with `created_at = "2026-09-01T07:00:00Z"` (exactly $t$). Tests that the lookback window is strictly exclusive on the right ($< t$). Excluded from R5!

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-01T07:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, 8 lines.
- Depends on SPEC-GAPS G10 (lookback inclusive at $t-7\text{d}$, available_at <= t), G11 (event_time == t excluded).

## Input lines

| line | id | type | repo | created_at | intent |
|---|---|---|---|---|---|
| 1-6 | 1001-1006 | B1-B6 | F01 baseline | baseline; B2, B4, B6 stars have `available_at == t` and are inside window |
| 7 | 27001 | WatchEvent `started` | 501 | 2026-08-25T07:00:00Z | exactly $t - 7\text{d}$ -> included in R5 |
| 8 | 27002 | WatchEvent `started` | 503 | 2026-09-01T07:00:00Z | exactly $t$ -> strictly excluded from R5 |

## Expected outputs, derived

- **r1:** Canonical = lines 1-6 (B1..B6) + line 7 (27001) + line 8 (27002) = **8**. Q1..Q4 = 0.
- **r2:**
  - 2026-09-01T00:00:00Z:
    - IssuesEvent: 1 (B5)
    - PushEvent: 2 (B1, B3)
    - WatchEvent: 5 (B2, B4, B6, 27001, 27002)
- **r3:** 8 distinct IDs, 0 duplicates, 0 conflicts.
- **r4:**
  - Repo 501: line 27001 on 2026-08-25 (1 star); B2, B6 on 2026-09-01 (2 stars).
  - Repo 502: B4 on 2026-09-01 (1 star).
  - Repo 503: line 27002 on 2026-09-01 (1 star).
  - Rows:
    - `501,2026-08-25,1`
    - `501,2026-09-01,2`
    - `502,2026-09-01,1`
    - `503,2026-09-01,1`
- **r5:** Cutoff `2026-09-01T07:00:00Z`.
  - Repo 501: B2 (00:10), B6 (00:40), and 27001 (08-25T07:00 == $t-7\text{d}$) are in $[t-7\text{d}, t)$ with `available_at` == $t$. Total = **3**.
  - Repo 502: B4 (00:20) in $[t-7\text{d}, t)$ with `available_at` == $t$. Total = **1**.
  - Repo 503: line 27002 has `event_time == t`, excluded from R5 ($< t$). Total = 0 (omitted).
  - Rows:
    - `2026-09-01T07:00:00Z,501,3`
    - `2026-09-01T07:00:00Z,502,1`
- **registry:** `present`.
- **flags:**
  - line 27001: `created_at = 2026-08-25T07:00:00Z < 2026-08-31T23:00:00Z` -> `late = 1`.
  - line 27002: `created_at = 2026-09-01T07:00:00Z > 2026-09-01T02:00:00Z` -> `future_skewed = 1`.
  - `unrecognized_type = 0`.
