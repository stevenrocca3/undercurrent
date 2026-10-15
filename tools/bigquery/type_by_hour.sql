-- §5.2 metric 1: event count by (hour, event_type), September 2026.
-- BigQuery has no source file, so the hour is created_at truncated to the hour.
SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:00:00Z', created_at) AS hour, type AS event_type, COUNT(*) AS event_count
FROM `githubarchive.day.2026*`
WHERE _TABLE_SUFFIX BETWEEN '0901' AND '0930'
GROUP BY hour, event_type
