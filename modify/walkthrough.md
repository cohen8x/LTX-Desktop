# Walkthrough: Client-Server Decoupling for LTX-Desktop

I have completed the implementation based on our plan to separate the frontend from the local python backend and bypass the local hardware checks.

## Changes Made

### Frontend Custom Backend Configuration

- **File Modified:** [python-backend.ts](file:///c:\prj\gith\LTX-Desktop\electron\python-backend.ts)
- **What Changed:** Enhanced the Electron backend management module to allow skipping the local Python process creation. By introducing the `external` ownership state, the application now checks for a `LTX_EXTERNAL_BACKEND_URL` environment variable upon backend startup. If provided, the process will immediately report itself as "alive" and hook the interface to the specified URL alongside optional authentication tokens (`LTX_AUTH_TOKEN`, `LTX_ADMIN_TOKEN`), running in a purely standalone client mode.

### Backend Hardware Check Bypass

- **File Modified:** [ltx2_server.py](file:///c:\prj\gith\LTX-Desktop\backend\ltx2_server.py)
- **What Changed:** Added an evaluation of the `LTX_FORCE_LOCAL_MODE` environment variable within `_resolve_force_api_generations`. setting this purely bypasses the VRAM and CUDA architecture capacity checks, unlocking the complete desktop app interface even if the backend sits on a GPU-less or remote cloud setup instance.

### Project Documentation

- **File Modified:** [CHANGELOG.md](file:///c:\prj\gith\LTX-Desktop\CHANGELOG.md) (Created)
- **What Changed:** Documented these new environment variables.

## Validation Results

- ✔️ Passed `pnpm typecheck` successfully, confirming that the new TS typings `BackendOwnership` integration and Python syntax (`os` usages) are valid and free of static analysis violations.

## Running the Architecture

To take advantage of these new capabilities, you can now launch your instances using these parameters:

**Remote Cloud Backend Launch**
```powershell
cd backend
$env:LTX_FORCE_LOCAL_MODE="1"
$env:LTX_APP_DATA_DIR="$env:APPDATA\ltx-desktop"
uv run python ltx2_server.py
```

**Local Client Launch (Pointing to Cloud)**

Option 1: Inline environment variables
```bash
cross-env LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT> pnpm dev
```

Option 2: Using a `.env` file
You can create a `.env` file in the project root so you don't have to type it every time:

```env
LTX_EXTERNAL_BACKEND_URL=http://<REMOTE_IP>:<PORT>
# The following tokens are COMPLETELY OPTIONAL for self-hosted instances. 
# Only add them if you explicitly configured authentication on your backend:
LTX_AUTH_TOKEN=<YOUR_GENERATED_TOKEN>
LTX_ADMIN_TOKEN=<YOUR_GENERATED_ADMIN_TOKEN>
```

Then run: `pnpm dev`
