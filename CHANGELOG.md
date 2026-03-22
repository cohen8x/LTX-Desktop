# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Client-Server Decoupling:**
  - Added support for running the Electron frontend and Python backend separately.
  - The frontend now accepts `LTX_EXTERNAL_BACKEND_URL`, `LTX_AUTH_TOKEN`, and `LTX_ADMIN_TOKEN` environment variables to connect to an external/remote backend without spawning a local server process.
  - The Python backend now supports the `LTX_FORCE_LOCAL_MODE=1` environment variable. When set, it bypasses local hardware (VRAM) checks and unlocks the full local UI in the frontend, rather than forcing the user into API-only mode.

### Changed
- `electron/python-backend.ts`: Modified `startPythonBackend` to bypass process creation and adopt the external connection if `LTX_EXTERNAL_BACKEND_URL` is provided. Added `external` status to `BackendOwnership`.
- `backend/ltx2_server.py`: Modified `_resolve_force_api_generations` to return `False` when `LTX_FORCE_LOCAL_MODE=1` is set.
