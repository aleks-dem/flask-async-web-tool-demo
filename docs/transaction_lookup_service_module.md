# Transaction Lookup Service Task

## File
`services/transaction_lookup_task.py`

## Purpose
Performs asynchronous reference lookup in demo-safe mock mode and generates XLSX output.

## Output Schema
Each result row includes:
- input reference
- workspace
- record identifiers
- timestamps
- status and routing fields
- financial attributes (amount, fee, currency)
- source/external references

## Notes
- Progress is updated per processed reference.
- Final XLSX is saved in `data/temp` with auto-sized columns.

