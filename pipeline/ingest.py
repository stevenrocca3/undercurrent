"""Read GH Archive hour files and classify each requested hour (spec §1).

`read_hour` streams one hour's lines and records its registry status:

- `missing`: no file for the hour.
- `unreadable`: not gzip, or decompression fails before any complete line.
  The hour yields no lines.
- `truncated`: the stream fails or ends early after >= 1 complete line. The
  complete lines are yielded, then the bytes after the last `\\n` (if any) as a
  final line marked `partial` (the caller quarantines it as Q1).
- `present`: fully decoded. A final line without `\\n` is a normal line.

Lines are the bytes between `\\n` terminators, without the `\\n`. The reader
never holds more than one line plus one chunk in memory.
"""

import zlib
from datetime import datetime, timedelta, timezone

CHUNK_SIZE = 1 << 16
HOUR = timedelta(hours=1)


class StreamError(Exception):
    """Decompression failed or the stream ended early; recovered output was already yielded."""


def hour_file_name(hour):
    """GH Archive name: hour not zero-padded, e.g. 2026-09-01-2.json.gz."""
    return f"{hour:%Y-%m-%d}-{hour.hour}.json.gz"


def requested_hours(first, last):
    """Every hour start from first to last inclusive."""
    hour = first
    while hour <= last:
        yield hour
        hour += HOUR


def parse_timestamp(text):
    """Parse YYYY-MM-DDTHH:MM:SSZ into an aware UTC datetime."""
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def format_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_instant(dt):
    """format_timestamp, plus .ffffff when there is a fraction (02 §8 available_at)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ" if dt.microsecond else "%Y-%m-%dT%H:%M:%SZ")


def inflate(f, chunk_size=CHUNK_SIZE):
    """Yield the decompressed bytes of a (possibly multi-member) gzip file.

    Raises StreamError after yielding everything recoverable when the file is
    not gzip, a member is corrupt (including a bad CRC), the stream ends before
    the end-of-stream marker, or non-gzip bytes follow a complete member.
    `gzip.open` would drop the bytes before the failure point, so this uses
    `zlib.decompressobj(wbits=31)` and, on an error, replays the failing chunk
    byte by byte from a saved state to recover the output before the bad byte.
    """
    d = zlib.decompressobj(wbits=31)
    fed = False  # has the current member received any input?
    members = 0
    pending = b""
    while True:
        chunk = pending or f.read(chunk_size)
        pending = b""
        if not chunk:
            break
        fed = True
        saved = d.copy()
        try:
            yield d.decompress(chunk)
        except zlib.error:
            d = saved
            for i in range(len(chunk)):
                try:
                    yield d.decompress(chunk[i:i + 1])
                except zlib.error as e:
                    raise StreamError(f"decompression error: {e}") from None
            raise AssertionError("chunk failed as a whole but not byte by byte")
        if d.eof:
            members += 1
            pending = d.unused_data
            d = zlib.decompressobj(wbits=31)
            fed = False
    if members == 0 and not fed:
        raise StreamError("empty file: not a gzip stream")
    if fed:
        yield d.flush()
        raise StreamError("stream ended before the end-of-stream marker")


class HourRead:
    """One requested hour: its lines (via `lines()`) and, once read, its registry entry."""

    def __init__(self, input_dir, hour, chunk_size=CHUNK_SIZE):
        self.hour = hour
        self.path = input_dir / hour_file_name(hour)
        self.chunk_size = chunk_size
        self.status = None
        self.file_bytes = None
        self.line_count = 0
        self.error = ""

    def lines(self):
        """Yield (source_line, raw_bytes, partial). Sets status, line_count and error when exhausted."""
        if not self.path.is_file():
            self.status = "missing"
            return
        self.file_bytes = self.path.stat().st_size
        tail = b""
        with open(self.path, "rb") as f:
            try:
                for piece in inflate(f, self.chunk_size):
                    tail += piece
                    *complete, tail = tail.split(b"\n")
                    for raw in complete:
                        self.line_count += 1
                        yield self.line_count, raw, False
            except StreamError as e:
                self.error = str(e)
                if self.line_count == 0:
                    self.status = "unreadable"
                    return
                self.status = "truncated"
                if tail:
                    self.line_count += 1
                    yield self.line_count, tail, True
                return
        self.status = "present"
        if tail:
            self.line_count += 1
            yield self.line_count, tail, False
