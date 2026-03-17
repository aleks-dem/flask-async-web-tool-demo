# Transaction Lookup Function

## File
`app_functions/transaction_lookup.py`

## Purpose
Collects reference IDs (single value or Excel list), validates date range, and starts async lookup task.

## Routes
- `GET|POST /transaction_lookup/lookup`
- `GET /transaction_lookup/status/<function_key>`
- `GET /transaction_lookup/download/<function_key>/<filename>`

## Validation Rules
- End date must be >= start date.
- Date range max: 92 days.
- Single ID min length: 5.
- Excel mode max rows: 50 IDs.
