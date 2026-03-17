# Documentation

Technical documentation for the public demo repository.

## Recommended Reading Order
1. [Detailed architecture](detailed_architecture.md)
2. [Compact architecture](architecture_compact.md)
3. [Authentication module](auth_module.md)
4. [Admin module](admin_module.md)
5. [App functions module](app_functions_module.md)
6. [Document Builder function](document_builder_module.md)
7. [Document Builder service task](document_builder_service_module.md)
8. [Transaction Lookup function](transaction_lookup_module.md)
9. [Transaction Lookup service task](transaction_lookup_service_module.md)
10. [Utilities](utils_module.md)

## Scope of This Demo
- Modular Flask architecture with Blueprints.
- Celery-based asynchronous processing.
- Redis-based process state tracking.
- Analyst-oriented export workflows (XLSX and DOCX/PDF).
- Dockerized local setup.

## Local Run
```bash
docker compose up --build
```

Open `http://localhost:5000`.

Demo credentials:
- `admin / admin123`
- `analyst / analyst123`

## Data Safety Notes
- Default mode is `DATA_SOURCE_MODE=mock`.
- SQL files are templates, not production queries.
- Repository is sanitized for public portfolio use.
