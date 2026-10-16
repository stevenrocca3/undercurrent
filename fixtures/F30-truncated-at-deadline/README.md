# F30: truncated hour available at deadline

The input is the deliberately truncated gzip stream from F16: complete lines B1-B4 followed by the partial B5 prefix on line 5. Its `available_at.csv` value is `2026-09-02T01:00:00Z`, exactly `h + 1h + 24h`.

## Input lines

| hour / line | event | intent |
|---|---|---|
| 00 / 1-4 | B1-B4 from F01 | four complete canonical lines; B2 and B4 are stars |
| 00 / 5 | partial B5 JSON | incomplete final line, quarantined Q1 |

## Expected outputs, derived

Lines 1-4 are canonical and line 5 is Q1, so r1 canonical = 4 and Q1 = 1. The complete records are two PushEvents and two WatchEvents, with four distinct IDs and no duplicates/conflicts. B2 and B4 give one star each for repos 501 and 502 on 2026-09-01. The registry status is `truncated`. Before the deadline (00:59:59), the file is not available and R5 has no rows; at the deadline, `available_at == t`, so both complete stars are included. The partial line is not canonical and contributes no R5 event. All flags are zero.
