"""R2, R4, R5 and R7 over kept events (spec §4, §6).

All TIMESTAMP columns are naive UTC, so cutoffs are passed as naive UTC too:
an aware datetime would make DuckDB compare through the session time zone.
"""

from datetime import timezone
from pathlib import Path

EVENT_TYPES_FILE = Path(__file__).resolve().parent.parent / "fixtures" / "event_types.txt"  # canonical copy (§2)
STAR = "event_type = 'WatchEvent' AND payload_action = 'started'"  # §6: exact strings, after dedup


def recognized_event_types():
    return [t for t in EVENT_TYPES_FILE.read_text().split("\n") if t]


def _naive_utc(t):
    return t.astimezone(timezone.utc).replace(tzinfo=None)


def flag_counts(con):
    """[(flag, count)] for future_skewed, late, unrecognized_type, over kept occurrences (§4)."""
    future_skewed, late, unrecognized = con.execute("""
        SELECT count(*) FILTER (WHERE event_time > source_file_hour + INTERVAL 2 HOUR),
               count(*) FILTER (WHERE event_time < source_file_hour - INTERVAL 1 HOUR),
               count(*) FILTER (WHERE NOT list_contains(?, event_type))
        FROM events
    """, [recognized_event_types()]).fetchone()
    return [("future_skewed", future_skewed), ("late", late), ("unrecognized_type", unrecognized)]


def stars_as_of(con, cutoffs):
    """[(cutoff, repo_id, star_events)]: event_time in [t - 7d, t) and available_at <= t (§4 point-in-time)."""
    rows = []
    for t in sorted(cutoffs):
        for repo_id, count in con.execute(f"""
            SELECT repo_id, count(*) FROM events
            WHERE {STAR}
              AND event_time >= $t - INTERVAL 7 DAY AND event_time < $t
              AND available_at <= $t
            GROUP BY repo_id ORDER BY repo_id
        """, {"t": _naive_utc(t)}).fetchall():
            rows.append((t, repo_id, count))
    return rows


def events_by_hour_and_type(con):
    """[(source_file_hour, event_type, event_count)] (R2), attributed to the kept occurrence."""
    return con.execute("""
        SELECT source_file_hour, event_type, count(*) FROM events
        GROUP BY ALL ORDER BY ALL
    """).fetchall()


def stars_by_repo_and_date(con):
    """[(repo_id, event_date, star_events)] (R4), by UTC date of event_time."""
    return con.execute(f"""
        SELECT repo_id, CAST(event_time AS DATE), count(*) FROM events
        WHERE {STAR} GROUP BY ALL ORDER BY ALL
    """).fetchall()
