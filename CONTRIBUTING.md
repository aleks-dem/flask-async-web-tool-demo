# Contributing

## Workflow

1. Fork the repository.
2. Create a feature branch from `main`.
3. Keep changes focused and small.
4. Add or update tests for behavior changes.
5. Run local checks before opening a PR.
6. Open a pull request with clear context and test evidence.

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Required Checks

```bash
pytest -q
python -m compileall app.py run.py admin auth app_functions services utils
```

## Coding Guidelines

- Keep code modular and explicit.
- Prefer deterministic behavior in mock/demo data generators.
- Do not commit secrets, credentials, or runtime artifacts.
- Keep documentation aligned with implementation changes.

## Pull Request Checklist

- Behavior change is explained.
- Tests pass locally.
- Documentation is updated (if needed).
- No sensitive data introduced.
- Changelog entry added (if user-visible change).
