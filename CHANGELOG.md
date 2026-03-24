# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Transparent Proxy Architecture**: Introduced `backend/proxy_server.py` to act as a lightweight local middleman on the user's desktop. It fakes GPU and model readiness for the frontend, while transparently forwarding demanding AI generation requests to a heavy cloud computing node configured via `LTX_CLOUD_URL`.
- **Cloud Proxy File Router**: Added `backend/_routes/proxy.py` to handle `POST /api/proxy/upload` and `GET /api/proxy/download`. This provides the essential file transfer pipelines for the proxy to sync payload assets up to Linux and pull generated products down to Windows smoothly.
- **Automated Uplink/Downlink Path Hijacking**: The proxy server now dynamically scans for JSON properties like `imagePath`, `audioPath`, and `video_path` in REST payloads (Generate, Retake, and IC-LoRA). It automatically intercepts files, replaces file paths, performs the uploads/downloads silently, and serves the correct OS-specific absolute paths to trick both the frontend renderer and the backend Python executor.

### Changed
- **Electron Bootstrapper**: `electron/python-backend.ts` now specifically spins up the `proxy_server.py` application daemon rather than attempting to load the heavily GPU-coupled `ltx2_server.py`.
- **Environment Lean-up**: Stripped outdated local ML-specific environment variables (e.g., `PYTORCH_ENABLE_MPS_FALLBACK`) from the Electron app spawn command, drastically lowering startup friction and freeing the host OS from unnecessary overhead.
