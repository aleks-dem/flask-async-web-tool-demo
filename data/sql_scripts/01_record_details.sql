-- Template query: fetch a single record by ID.
-- Replace table names and fields with your production schema.

SELECT
    now() AS generated_at,
    record_id,
    created_at,
    amount,
    currency,
    status,
    user_id,
    user_email
FROM analytics.records
WHERE record_id = {record_id}
LIMIT 1;
