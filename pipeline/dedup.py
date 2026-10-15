"""Deduplicate canonical records by event_id only (spec §3).

The kept occurrence of an event_id is the one with the smallest
(source_file_hour, source_line). Only discarded occurrences are written, to
`duplicates`, each with its kept occurrence; `events` is canon minus those.
DuckDB runs the GROUP BY out of core, so dedup state need not fit in memory.
"""

DEDUP_SQL = """
CREATE TABLE duplicates AS
WITH multi AS (
    SELECT event_id FROM canon GROUP BY event_id HAVING count(*) > 1
), ranked AS (
    SELECT event_id, source_file_hour, source_line, record_hash,
           row_number() OVER w AS occurrence,
           first_value(source_file_hour) OVER w AS kept_source_file_hour,
           first_value(source_line) OVER w AS kept_source_line,
           first_value(record_hash) OVER w AS kept_record_hash
    FROM canon SEMI JOIN multi USING (event_id)
    WINDOW w AS (PARTITION BY event_id ORDER BY source_file_hour, source_line)
)
SELECT * EXCLUDE (occurrence) FROM ranked WHERE occurrence > 1;

-- §3: a conflict is a discarded occurrence whose record_hash differs from the kept one.
CREATE VIEW conflicts AS SELECT * FROM duplicates WHERE record_hash <> kept_record_hash;

CREATE VIEW events AS
SELECT * FROM canon ANTI JOIN duplicates USING (source_file_hour, source_line);
"""


def deduplicate(con):
    """Build duplicates/conflicts/events; return the r3 row (distinct_event_ids, duplicate_count, conflict_count)."""
    con.execute(DEDUP_SQL)
    return con.execute("""
        SELECT (SELECT count(*) FROM canon) - (SELECT count(*) FROM duplicates),
               (SELECT count(*) FROM duplicates),
               (SELECT count(*) FROM conflicts)
    """).fetchone()
