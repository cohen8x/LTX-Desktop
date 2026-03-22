# LTX-Desktop Client-Server Decoupling Plan

This plan outlines the changes needed to achieve client-server decoupling, allowing the frontend to connect to a remote backend while bypassing local hardware checks.

## User Review Required
No breaking changes to the default behavior. The new behavior is entirely opt-in via environment variables.

## Proposed Changes

### Electron Main Process

#### [MODIFY] [python-backend.ts](file:///c:\prj\gith\LTX-Desktop\electron\python-backend.ts)
- **Goal**: Allow injecting an external backend URL and bypass spawning the local Python process.
- **Changes**:
  - Update `BackendOwnership` type to include `'external'`.
  - In `startPythonBackend()`, add an early return if `process.env.LTX_EXTERNAL_BACKEND_URL` is set. If set, assign `backendUrl`, `authToken`, and `adminToken` from environment variables, set ownership to `'external'`, and publish an `'alive'` health status.
  - In `stopPythonBackend()`, add a check to clear state without killing any process if `backendOwnership === 'external'`.

### Python Backend

#### [MODIFY] [ltx2_server.py](file:///c:\prj\gith\LTX-Desktop\backend\ltx2_server.py)
- **Goal**: Bypass the hardware/VRAM check that forces the frontend into API-only mode when running the backend on a machine without a dedicated GPU (or when overriding is desired).
- **Changes**:
  - In `_resolve_force_api_generations()`, add a check for an environment variable, `LTX_FORCE_LOCAL_MODE`.
  - If `os.environ.get("LTX_FORCE_LOCAL_MODE") == "1"`, immediately return `False` to tell the frontend to unlock the full local interface, regardless of actual hardware detection.

## Verification Plan

### Manual Verification
1. **Start Backend Separately**:
   - Run the python backend independently with `LTX_FORCE_LOCAL_MODE=1` to ensure it starts and reports `force_api_generations=False`.
   - Command (PowerShell): `$env:LTX_FORCE_LOCAL_MODE="1"; $env:LTX_APP_DATA_DIR="$env:APPDATA\ltx-desktop"; cd backend; uv run python ltx2_server.py`
2. **Start Frontend Separately**:
   - Run the frontend with `LTX_EXTERNAL_BACKEND_URL` pointing to the separated backend.
   - Command: `cross-env LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT> pnpm dev`
   - Alternatively, create a `.env` file in the project root:
     
     ```env
     LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT>
     # (Optional) If your backend requires authentication:
     LTX_AUTH_TOKEN=my_secret_token
     LTX_ADMIN_TOKEN=my_admin_token
     ```
     
     and run: `pnpm dev`
   - Verify the frontend loads the full local UI without attempting to spawn a child Python process.
