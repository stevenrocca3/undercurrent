-- §5.2 metric 3: star events by (repo_id, UTC date) for the 1,000 repos with the
-- most star events in September 2026 (ties: smaller repo_id first).
-- A star event is a WatchEvent whose payload.action is "started" (§2 is_star).
WITH s AS (
  SELECT repo.id AS repo_id, DATE(created_at) AS event_date
  FROM `githubarchive.day.2026*`
  WHERE _TABLE_SUFFIX BETWEEN '0901' AND '0930'
    AND type = 'WatchEvent' AND JSON_EXTRACT_SCALAR(payload, '$.action') = 'started'
),
top AS (SELECT repo_id FROM s GROUP BY repo_id ORDER BY COUNT(*) DESC, repo_id LIMIT 1000)
SELECT repo_id, FORMAT_DATE('%Y-%m-%d', event_date) AS event_date, COUNT(*) AS star_events
FROM s JOIN top USING (repo_id)
GROUP BY repo_id, event_date
