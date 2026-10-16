# F31: republished hour retains first version

The archived hour file contains the first version, and `available_at.csv` records that version's first successful availability at 07:00. The fixture format has one file per source hour, so it cannot encode a second, changed publication. The fetcher must retain the first version in canonical tables when its later recheck reports a republish; directly testing the changed-file/recheck behavior requires a fetcher-level test.

## Input lines

| hour / line | event | repo | event time | intent |
|---|---|---|---|---|
| 00 / 1 | 31001, WatchEvent started | 501 | 00:30 | star in the retained first version |

## Expected outputs, derived

The first-version file has one canonical, distinct WatchEvent (r1 canonical = 1; r3 = 1/0/0). It contributes one repo-501 star on 2026-09-01. At 07:00 the availability boundary is inclusive, so R5 has repo 501 = 1. The file is `present`; all flags are zero.
