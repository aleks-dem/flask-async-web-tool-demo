-- Template query: bulk lookup by list of references in date range.

SELECT
    input_reference,
    workspace,
    record_id,
    created_at,
    updated_at,
    status,
    amount,
    currency,
    source_reference,
    external_payment_id
FROM analytics.lookup_view
WHERE created_at BETWEEN toDate('{start_date}') AND toDate('{end_date}')
  AND input_reference ILIKE concat('%', '{input_reference}', '%')
LIMIT 100;

