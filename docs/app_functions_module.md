# App Functions Module

## Purpose
Groups user-facing tools as independent Blueprints.

## Registered Functions
- `document_builder`
  - Builds client-facing document files asynchronously (DOCX/PDF output).
- `transaction_lookup`
  - Performs asynchronous ID-based lookup and exports results as XLSX.

## Why this split works
- Each function has isolated routes, template, and permissions.
- Async-heavy routes delegate complex processing into `services/` tasks.
- New functions can be added without impacting existing ones.
