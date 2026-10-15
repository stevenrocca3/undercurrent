"""Deduplicate canonical records by event_id only (spec §3).

The kept occurrence of an event_id is the one with the smallest
(source_file_hour, source_line). Only discarded occurrences are written, to
`duplicates`, each with its kept occurrence; `events` is canon minus those.
DuckDB runs the GROUP BY out of core, so dedup state need not fit in memory.

Batch mode deduplicates all of canon once. Replay mode (§4) deduplicates each
hour as it arrives, against the occurrences kept from earlier hours, with the
same query restricted to that hour.
"""

SCHEMA_SQL = """
CREATE TABLE duplicates (
    event_id VARCHAR, source_file_hour TIMESTAMP, source_line INTEGER, record_hash VARCHAR,
    kept_source_file_hour TIMESTAMP, kept_source_line INTEGER, kept_record_hash VARCHAR
);
-- §3: a conflict is a discarded occurrence whose record_hash differs from the kept one.
CREATE VIEW conflicts AS SELECT * FROM duplicates WHERE record_hash <> kept_record_hash;
CREATE VIEW events AS SELECT * FROM canon ANTI JOIN duplicates USING (source_file_hour, source_line);
"""

DEDUP_SQL = """
INSERT INTO duplicates
WITH candidates AS (
    -- occurrences not yet discarded: in replay, the new hour plus the kept rows of earlier hours
    SELECT event_id, source_file_hour, source_line, record_hash
    FROM canon ANTI JOIN duplicates USING (source_file_hour, source_line)
    {hour_filter}
), multi AS (
    SELECT event_id FROM candidates GROUP BY event_id HAVING count(*) > 1
), ranked AS (
    SELECT event_id, source_file_hour, source_line, record_hash,
           row_number() OVER w AS occurrence,
           first_value(source_file_hour) OVER w AS kept_source_file_hour,
           first_value(source_line) OVER w AS kept_source_line,
           first_value(record_hash) OVER w AS kept_record_hash
    FROM candidates SEMI JOIN multi USING (event_id)
    WINDOW w AS (PARTITION BY event_id ORDER BY source_file_hour, source_line)
)
SELECT * EXCLUDE (occurrence) FROM ranked WHERE occurrence > 1
"""

REPLAY_HOUR_FILTER = """
    WHERE source_file_hour <= $hour
      AND event_id IN (SELECT event_id FROM canon WHERE source_file_hour = $hour)
"""


def create_dedup_tables(con):
    con.execute(SCHEMA_SQL)


def deduplicate(con, hour=None):
    """Discard duplicates across all of canon (batch), or within `hour` against earlier kept rows (replay).

    `hour` is a naive UTC datetime, and replay must call this once per hour, in hour order.
    """
    if hour is None:
        con.execute(DEDUP_SQL.format(hour_filter=""))
    else:
        con.execute(DEDUP_SQL.format(hour_filter=REPLAY_HOUR_FILTER), {"hour": hour})


def r3_counts(con):
    """(distinct_event_ids, duplicate_count, conflict_count) (§3, §6 R3)."""
    return con.execute("""
        SELECT (SELECT count(*) FROM canon) - (SELECT count(*) FROM duplicates),
               (SELECT count(*) FROM duplicates),
               (SELECT count(*) FROM conflicts)
    """).fetchone()
