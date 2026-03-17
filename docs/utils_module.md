# Utilities Module

## Files
- `utils/users_repository.py`
- `utils/redis_state_repository.py`
- `utils/background_tasks.py`
- `utils/logging_config.py`
- `utils/globals.py`

## Responsibilities
- User storage and CRUD operations (`data/users.yaml`).
- Process state persistence in Redis (with TTL).
- Scheduled cleanup of stale temp files and stale states.
- Root logger setup with rotating log files.
- Central function metadata for dashboard and sidebar rendering.
- Observability helpers: request/task metrics and request context propagation.
