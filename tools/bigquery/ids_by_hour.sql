-- §5.2 metric 2: distinct event_id count by hour, September 2026.
SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:00:00Z', created_at) AS hour, COUNT(DISTINCT id) AS distinct_event_ids
FROM `githubarchive.day.2026*`
WHERE _TABLE_SUFFIX BETWEEN '0901' AND '0930'
GROUP BY hour
