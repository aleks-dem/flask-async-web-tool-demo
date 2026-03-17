# Transaction Operations Toolkit Demo (Flask)

Portfolio-safe demo of an internal operations service for analysts: lookup workflows, async processing, and export/document generation.

## Why This Project Fits a Senior Data Engineer Portfolio
- Designs and ships an end-to-end internal data product, not just notebooks or scripts.
- Combines backend APIs, async job orchestration, state management, and operational deployment.
- Implements practical controls: RBAC, background cleanup jobs, environment-based config, and test coverage.
- Demonstrates integration patterns commonly used around analytics platforms and transaction investigation workflows.

## Core Capabilities
- Modular Flask app with Blueprints (`auth`, `admin`, `document_builder`, `transaction_lookup`).
- Async execution with Celery workers and Redis-backed process state.
- Polling-based UX for long-running jobs with progress/status recovery.
- Excel ingestion and Excel export for analyst-friendly workflows.
- DOCX/PDF generation for document preparation.
- Admin UI for user management (CRUD, filtering, sorting, pagination).
- CSRF protection for state-changing web requests.
- Observability baseline: request IDs, JSON structured logs, and process-local Prometheus-style `/metrics`.
- Docker Compose local runtime (`web`, `worker`, `redis`).

## Architecture (High Level)
1. User submits form in UI (`document_builder` or `transaction_lookup`).
2. Flask route validates input and initializes process state in Redis.
3. Route enqueues Celery task.
4. Frontend polls status endpoint every 2 seconds.
5. Worker updates progress/results in Redis.
6. UI renders final table/parameters and downloads generated artifact from `data/temp`.
7. Scheduler cleans stale temp files and stale process states.

Extended docs: [docs/README.md](docs/README.md)

## Quick Start (Docker)
```bash
docker compose up --build
```

Open `http://localhost:5000`.

Demo users:
- `admin / admin123`
- `analyst / analyst123`

## Local Development
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python run.py
```

## Test Suite
```bash
pytest -q
```

## Repository Layout
```text
admin/          Admin module and user-management routes
app_functions/  User-facing feature routes
auth/           Login/logout/dashboard routes
services/       Celery task implementations
utils/          User repo, Redis state repo, scheduler, logging
templates/      Jinja templates with status polling UI
data/           Demo users, SQL templates, temp outputs
docs/           Architecture and module-level technical docs
tests/          Pytest suite
```

## Publication Safety
- Mock mode is the default (`DATA_SOURCE_MODE=mock`).
- `.env` is gitignored; `.env.example` contains placeholders only.
- Runtime artifacts (`logs`, `flask_session`, `data/temp`) are gitignored.
- No production credentials or company identifiers are stored in this demo.

## Release and Governance
- Changelog template: [CHANGELOG.md](CHANGELOG.md)
- Public contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Release checklist: [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE).
Third-party dependency notes: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
