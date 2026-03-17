# Authentication Module

## Purpose
Handles login/logout, dashboard rendering, and language switching.

## Main Routes
- `GET|POST /login`
  - Authenticates user from `data/users.yaml`.
- `GET /logout`
  - Ends user session.
- `GET /dashboard`
  - Shows only functions available to current user.
- `GET /change_lang/<lang>`
  - Sets session language (`en` or `ru`).

## Notes
- Password check is hash-based for all stored users.
- Dashboard cards are generated dynamically from `utils.globals.function_details`.
