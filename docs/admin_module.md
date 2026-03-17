# Admin Module

## Purpose
Provides administrative user management for the demo application.

## Main Routes
- `GET /admin/`
  - Renders user list with filter, sorting, and pagination.
- `GET /admin/api/users`
  - JSON API used by frontend for async table updates.
- `POST /admin/create_user`
  - Creates a new user in `data/users.yaml`.
- `POST /admin/delete_user/<user_id>`
  - Deletes selected user (except currently logged-in admin).
- `GET|POST /admin/edit_user/<user_id>`
  - Updates display name, password, role, and assigned functions.

## Notable Implementation Details
- Session-backed persistence of filter/sort/pagination state.
- Windowed pagination with ellipsis for large page sets.
- Route-level admin guard via decorator.
- Duplicate username protection on user creation.
