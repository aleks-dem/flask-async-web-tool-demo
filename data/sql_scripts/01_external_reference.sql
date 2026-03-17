-- Template query: fetch external/source reference for a record.

SELECT
    source_reference,
    external_reference
FROM analytics.record_references
WHERE record_id = {record_id}
LIMIT 1;

