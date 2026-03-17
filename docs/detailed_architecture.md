# Detailed Architecture

## 1. Overview
The application is a Flask-based internal-tool style demo designed to show practical full-stack backend skills:
- clean route modularization with Blueprints,
- asynchronous workloads via Celery,
- Redis-backed state management for long-running tasks,
- dynamic frontend behavior with status polling,
- export-oriented workflows (Excel and document generation).

## 2. Main Runtime Components
- **Flask app (`app.py`)**: application factory, login manager, Babel, blueprint registration.
- **Celery app (`celery_app.py`)**: worker bootstrap and task module registration.
- **Redis**: broker/result backend and state repository for progress tracking.
- **APScheduler (`utils/background_tasks.py`)**: cleanup jobs for temp files and stale process state.
- **Observability (`utils/observability.py`)**: request/task metrics (process-local), request-id context, Prometheus text rendering.

## 3. Module Map
- `auth/`: login/logout/dashboard and language switch.
- `admin/`: user CRUD, sorting/filtering/pagination, JSON endpoint for async table updates.
- `app_functions/`:
  - `document_builder.py`
  - `transaction_lookup.py`
- `services/`:
  - `document_builder_task.py`
  - `transaction_lookup_task.py`
- `utils/`: users repository, redis state repository, scheduler utilities, logging setup.

## 4. Async Request Lifecycle
1. User submits a form on a function page.
2. Route validates input and writes initial process state to Redis (`status=processing`, `progress=0`).
3. Route enqueues Celery task.
4. Frontend starts polling `/status/<function_key>` every 2 seconds.
5. Celery task periodically updates progress in Redis.
6. On completion, route exposes `file_url` and/or result payload.
7. User downloads generated artifact; state is cleaned.

## 5. State Contract
State entries are keyed by `process_state:{user_id}:{function_key}` and may include:
- `status`: `not_started`, `processing`, `completed`, `no_data`, `error`
- `progress`: integer 0..100
- `message`, `error`
- `results` (for table rendering)
- `parameters` (for summary tables)
- `file_url`
- `timestamp`

## 6. Internationalization
- Flask-Babel is configured in `app.py`.
- Supported locales: `en`, `ru`.
- Language toggle is handled in `auth/change_lang/<lang>`.

## 7. Deployment and Operations
- **Local**: `docker compose up --build` (web + worker + redis).
- **CI/CD**: `.gitlab-ci.yml` includes:
  - validate stage (Python compile check),
  - deploy stage template over SSH for self-hosted Docker environments.

## 8. Security and Publication Safety
- No production credentials in repository.
- `.env.example` provides placeholders only.
- Demo data mode works without external database access.
- Seed users are generic, non-company-specific, and password hashes are stored instead of plaintext.
- CSRF protection is enabled for all state-changing web requests.
