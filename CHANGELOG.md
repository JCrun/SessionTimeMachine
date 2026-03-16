# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-16
### Added
- Local snapshots for `Auto Save Session.sublime_session` and `Session.sublime_session`.
- Automatic backups for `Packages/User` config files.
- Date- and type-based snapshot directory layout.
- Git sync backend with pull on startup and push after snapshots.
- Session rollback command and Quick Panel selector.
- Path mappings and missing-file handling for rollback.
- SQLite FTS indexing and search command for unsaved buffers.
- Windows git console window suppression.

### Fixed
- Non-UTF8 session decode handling.
- Restore without auto-indentation to preserve tabs.
- Better extraction of saved file paths in session data.
- Buffer naming from session settings and sheet metadata.
- Skip restoring session files themselves.

