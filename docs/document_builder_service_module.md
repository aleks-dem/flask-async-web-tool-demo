# Document Builder Service Task

## File
`services/document_builder_task.py`

## Purpose
Processes document generation asynchronously.

## Flow
1. Update Redis state (`processing`, progress updates).
2. Build mock payload values from input.
3. Use template if available (`data/templates/<template>.docx`), otherwise generate default DOCX.
4. If PDF requested, attempt conversion using LibreOffice.
5. Save final file into `data/temp` and mark state as `completed`.

## Failure Handling
Any exception updates state to `error` with message for frontend display.
