# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added
- _Add upcoming features here._

### Changed
- _Add upcoming behavior changes here._

### Fixed
- _Add upcoming bug fixes here._

### Security
- _Add upcoming security-related updates here._

## [1.0.0] - 2026-03-17

### Added
- Public portfolio documentation set (`README`, module docs index, contributing/security/release policy files).
- GitHub release workflow for tagged versions (`v*`).
- MIT license for open-source publication.

### Changed
- Hardened user management with hash-only password verification and duplicate-username checks.
- Improved process-state reliability with Redis key TTL.
- Improved transaction lookup mock determinism with stable seeded generation.

### Fixed
- Patched download endpoint path traversal risk by using safe temp-path joins.
- Fixed admin table sorting indicator logic to avoid breaking header markup.
- Improved Excel parsing behavior to skip blank rows and deduplicate reference IDs.

### Security
- Removed plaintext demo passwords from `data/users.yaml` (stored as hashes).
- Expanded `.gitignore` to prevent committing runtime artifacts and local secrets.
