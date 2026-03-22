# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Client-Server Decoupling:**
  - Added an `.env` file parser running early in the Electron application initialization sequence. Support setting `LTX_EXTERNAL_BACKEND_URL`, `LTX_AUTH_TOKEN`, and `LTX_ADMIN_TOKEN` directly via the file.
  - Added support for running the Electron frontend and Python backend separately.
  - The frontend now accepts `LTX_EXTERNAL_BACKEND_URL`, `LTX_AUTH_TOKEN`, and `LTX_ADMIN_TOKEN` environment variables to connect to an external/remote backend without spawning a local server process.
  - The frontend now automatically bypasses the model download/setup screen when connected to an external backend interface, as it assumes the server administrator will manage the local models.
  - The Python backend now supports the `LTX_FORCE_LOCAL_MODE=1` environment variable. When set, it bypasses local hardware (VRAM) checks and unlocks the full local UI in the frontend, rather than forcing the user into API-only mode.
- `ltx2_server.py` now respects `LTX_HOST` environment variable to support binding the embedded backend to 0.0.0.0 for external network access.

### Changed
- `electron/preload.ts` & `electron/ipc/app-handlers.ts`: Added IPC exposure `isExternalBackend()` to check if the current frontend is connected to an external server.
- `frontend/App.tsx`: Added condition to skip `requiredModelsGate` check when `isExternalBackend()` evaluates to true.
- `electron/python-backend.ts`: Modified `startPythonBackend` to bypass process creation and adopt the external connection if `LTX_EXTERNAL_BACKEND_URL` is provided. Added `external` status to `BackendOwnership`.
- `backend/ltx2_server.py`: Modified `_resolve_force_api_generations` to return `False` when `LTX_FORCE_LOCAL_MODE=1` is set.
