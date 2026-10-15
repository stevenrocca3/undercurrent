# F11: repo renamed mid-window (same repo_id, new repo_name)

F01 (hour 0, where repo 501 is `acme/rocket`) plus hour 1, where repo 501 is renamed `acme/rocket-ng` **and** a different repo (503) takes the freed name `acme/rocket`.

- Requested hours: `2026-09-01T00:00:00Z` to `2026-09-01T01:00:00Z`. Cutoffs: `2026-09-02T00:00:00Z`.
- Inputs: `2026-09-01-0.json.gz` (6 lines), `2026-09-01-1.json.gz` (2 lines).

## Input lines

| file | line | id | content | intent |
|---|---|---|---|---|
| hour 0 | 1-6 | 1001-1006 | F01 baseline (501 = acme/rocket) | baseline |
| hour 1 | 1 | 11001 | WatchEvent `started`, erin 205, **repo 501 `acme/rocket-ng`**, 01:10:00 | the rename: same id, new name |
| hour 1 | 2 | 11002 | WatchEvent `started`, frank 206, **repo 503 `acme/rocket`**, 01:20:00 | name reuse: old name, different id |

**What the trap catches:**
- Grouping by `repo_name` would give acme/rocket = 3 (1002, 1006, 11002) and acme/rocket-ng = 1.
- Grouping by `repo_id` (correct) gives 501 = 3 (1002, 1006, 11001) and 503 = 1.

## Expected outputs, derived

- **r1:** canonical = **8**; Q* = 0.
- **r2:** hour 00 as F01; hour 01 WatchEvent = **2**.
- **r3:** 8, 0, 0.
- **r4:** all on 2026-09-01. 501 = **3**, 502 = **1**, 503 = **1**.
- **r5:** hour 1 `available_at` = 08:00 <= t = 2026-09-02T00:00:00Z. 501 = **3**, 502 = **1**, 503 = **1**.
- **registry:** 00 `present`, 01 `present`. **flags:** all 0.
