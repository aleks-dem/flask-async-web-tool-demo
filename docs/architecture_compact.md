# Compact Architecture

## Project Structure
```text
/
├── app.py
├── run.py
├── celery_app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitlab-ci.yml
├── .env.example
├── admin/
├── auth/
├── app_functions/
├── services/
├── utils/
├── templates/
├── static/
├── data/
│   ├── sql_scripts/
│   ├── temp/
│   ├── templates/
│   └── users.yaml
├── translations/
└── docs/
```

## Core Principles
- Blueprint-based modular structure.
- Asynchronous heavy operations via Celery workers.
- Task status and progress persisted in Redis.
- Polling-based frontend status updates.
- Server-side generation of XLSX and DOCX/PDF files.
- Bilingual UI via Flask-Babel (`en`, `ru`).
- Docker-first local deployment.
