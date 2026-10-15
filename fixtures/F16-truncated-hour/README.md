# F16: truncated hour

The F01 baseline is gzipped, and then the compressed bytes are cut off partway through line 5. The registry must say `truncated`. Lines 1-4 are kept, the partial line 5 is Q1, and line 6 does not exist as far as the reader can tell.

- Requested hours: `2026-09-01T00:00:00Z` only. Cutoffs: `2026-09-02T00:00:00Z`.
- Input: `input/2026-09-01-0.json.gz`, **255 bytes**, no gzip trailer.
- Depends on SPEC-GAPS G12 (decided): truncated = the gzip stream ends early after yielding at least one line; complete lines are kept; the partial last line is Q1.

## How the file is built (`write_truncated_gz` in `../generate_inputs.py`)

1. Write `B1\nB2\nB3\nB4\n` + `B5_HEAD` into a gzip stream (mtime 0, no filename).
2. Do a `Z_SYNC_FLUSH`. That forces every byte so far into complete deflate output and ends with the marker `00 00 ff ff`. Record the compressed offset (255).
3. Write the rest (`B5_TAIL\nB6\n`) and close the stream normally.
4. Keep only the first 255 compressed bytes. Everything after the sync point is dropped, including the 8-byte CRC/size trailer.

Because the cut is exactly at a sync point, every decoder recovers the same bytes: no more, no fewer.

## What a reader recovers (verified by decoding)

`zlib.decompressobj(wbits=31).decompress(file_bytes)` returns **803 bytes** with `eof == False` (no end-of-stream marker):

| recovered line | bytes | content | status |
|---|---|---|---|
| 1 | 201 + `\n` | B1 (1001 PushEvent) | complete |
| 2 | 186 + `\n` | B2 (1002 WatchEvent, 501) | complete |
| 3 | 169 + `\n` | B3 (1003 PushEvent) | complete |
| 4 | 188 + `\n` | B4 (1004 WatchEvent, 502) | complete |
| 5 | 55, **no `\n`** | `{"id":"1005","type":"IssuesEvent","actor":{"id":202,"lo` | **partial → Q1** |
| (6) | | B6 (1006 WatchEvent, 501) | not recoverable; not a line at all |

**Different readers behave differently. Steven, please check this:**
- Python `for line in gzip.open(path)` yields lines 1-4 and then raises `EOFError: Compressed file ended before the end-of-stream marker was reached`. **It never returns the partial line 5.** A reader built this way sees 4 lines and Q1 = 0, which does **not** match the expected r1. To surface the partial bytes, decompress with `zlib.decompressobj(wbits=31)` (streaming) and treat the leftover bytes after the last `\n` as a final line.
- Apple `gzip -dc` / `zcat` (430.140.2) prints **nothing** for this file ("unexpected end of file"), not even lines 1-4. Do not use it to inspect this fixture.

## Expected outputs, derived

- **registry:** hour 00 = **`truncated`** (the stream ended early, after yielding at least 1 line).
- **r1:** canonical = lines 1-4 = **4**; Q1 = partial line 5 = **1**; Q2..Q4 = 0. 4 + 1 = 5 recovered lines. B6 is not counted anywhere.
- **r2:** hour 00: PushEvent = 1001, 1003 = **2**; WatchEvent = 1002, 1004 = **2**. No IssuesEvent row: 1005 was in the partial line.
- **r3:** 4 distinct, 0, 0.
- **r4:** 501 = 1002 only = **1** (1006 was lost); 502 = 1004 = **1**.
- **r5:** 501 = **1**, 502 = **1**.
- **flags:** all 0.
