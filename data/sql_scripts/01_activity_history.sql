-- Template query: fetch activity history around a target record.

WITH base_record AS (
    SELECT user_id, created_at
    FROM analytics.records
    WHERE record_id = {record_id}
    LIMIT 1
)
SELECT
    event_type,
    event_id,
    event_time,
    amount,
    currency,
    status
FROM analytics.record_events
WHERE user_id = (SELECT user_id FROM base_record)
ORDER BY event_time ASC
LIMIT 200;
