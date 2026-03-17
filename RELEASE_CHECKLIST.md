# Release Checklist

## Pre-Release

- Version selected (Semantic Versioning).
- `CHANGELOG.md` updated.
- Security/publication scan completed (`.env`, logs, sessions, temp files, secrets).
- Documentation updated (`README.md`, `docs/`).
- Tests passed (`pytest -q`).
- Quick smoke test completed with Docker Compose.

## Tag and Release

- Create tag `vX.Y.Z`.
- Push tag to GitHub.
- Verify GitHub Release workflow completed successfully.
- Publish release notes with highlights, fixes, and known limitations.

## Post-Release

- Validate repository landing page content.
- Confirm release artifacts and links.
- Create follow-up issues for deferred improvements.
