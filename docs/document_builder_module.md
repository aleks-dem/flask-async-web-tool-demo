# Document Builder Function

## File
`app_functions/document_builder.py`

## Purpose
Accepts form input, starts asynchronous document generation, and returns status updates for polling.

## Routes
- `GET|POST /document_builder/build`
  - `GET`: renders page and restores in-progress state.
  - `POST`: validates input, initializes Redis state, enqueues Celery task.
- `GET /document_builder/status/<function_key>`
  - Returns current task state payload.
- `GET /document_builder/download/<function_key>/<filename>`
  - Returns generated file and removes temp copy after download.

## UX Features
- Progress bar and status banners.
- Polling-based completion detection.
- LocalStorage persistence of form values.
