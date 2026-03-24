"""Transparent Proxy Server for LTX-Desktop."""

import os
import sys
import json
import signal
import logging
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Set up logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[console_handler])
logger = logging.getLogger("Proxy")

# Cloud configuration - Load from env or config.ini
def _load_cloud_url() -> str:
    env_url = os.environ.get("LTX_CLOUD_URL")
    if env_url:
        return env_url
        
    import configparser
    ini_paths = [
        Path.cwd() / "config.ini", 
        Path(os.environ.get("LTX_APP_DATA_DIR", "")) / "config.ini" if os.environ.get("LTX_APP_DATA_DIR") else None
    ]
    
    for p in [x for x in ini_paths if x is not None]:
        if p.exists():
            try:
                config = configparser.ConfigParser()
                config.read(p, encoding="utf-8")
                if "Proxy" in config and "CloudUrl" in config["Proxy"]:
                    url = config["Proxy"]["CloudUrl"].strip()
                    if url: return url
            except Exception as e:
                logger.error(f"Error reading config.ini at {p}: {e}")
                
    return "http://117.50.248.201:8000" # Final fallback

LTX_CLOUD_URL = _load_cloud_url()

# Local Paths
_env_dir = os.environ.get("LTX_APP_DATA_DIR")
LTX_APP_DATA_DIR = Path(_env_dir) if _env_dir else Path.cwd()
OUTPUTS_DIR = LTX_APP_DATA_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

timeout = httpx.Timeout(3600.0)
client = httpx.AsyncClient(timeout=timeout)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client.aclose()

app = FastAPI(title="LTX Transparent Proxy", lifespan=lifespan)

from api_types import (
    HealthResponse,
    GpuInfoResponse,
    ModelsStatusResponse,
    GpuTelemetry,
    TextEncoderStatus,
)


# ============================================================
# Bypass Routes (Enables Frontend to Start Without GPU)
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def route_health() -> HealthResponse:
    gpu = GpuTelemetry(name="Proxy GPU", vram=24000, vramUsed=0)
    return HealthResponse(
        status="ok",
        models_loaded=True,
        active_model="proxy",
        gpu_info=gpu,
        sage_attention=False,
        models_status=[]
    )

@app.get("/api/gpu-info", response_model=GpuInfoResponse)
async def route_gpu_info() -> GpuInfoResponse:
    gpu = GpuTelemetry(name="Proxy GPU", vram=24000, vramUsed=0)
    return GpuInfoResponse(
        cuda_available=True,
        mps_available=False,
        gpu_available=True,
        gpu_name="Proxy GPU",
        vram_gb=24,
        gpu_info=gpu
    )

@app.get("/api/models/status", response_model=ModelsStatusResponse)
async def route_models_status() -> ModelsStatusResponse:
    te_status = TextEncoderStatus(downloaded=True, size_bytes=0, size_gb=0.0, expected_size_gb=0.0)
    return ModelsStatusResponse(
        models=[],
        all_downloaded=True,
        total_size=0,
        downloaded_size=0,
        total_size_gb=0.0,
        downloaded_size_gb=0.0,
        models_path=str(LTX_APP_DATA_DIR / "models"),
        has_api_key=False,
        text_encoder_status=te_status,
        use_local_text_encoder=False
    )


# ============================================================
# System Routes
# ============================================================

def _shutdown_process() -> None:
    os.kill(os.getpid(), signal.SIGTERM)

@app.post("/api/system/shutdown")
async def route_shutdown(background_tasks: BackgroundTasks, request: Request):
    client_host = request.client.host if request.client else None
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    
    background_tasks.add_task(_shutdown_process)
    return {"status": "shutting_down"}


# ============================================================
# File Hijacking Logic (Uplink / Downlink)
# ============================================================

async def upload_file_to_cloud(local_path: str) -> str:
    """Uploads a local file to the cloud proxy-upload endpoint and returns the cloud path."""
    if not local_path or not os.path.exists(local_path):
        logger.warning(f"File not found for upload, skipping: {local_path}")
        return local_path
    
    upload_url = f"{LTX_CLOUD_URL}/api/proxy/upload"
    filename = os.path.basename(local_path)
    
    logger.info(f"Intercepted local path. Uploading to cloud: {local_path}")
    try:
        with open(local_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            response = await client.post(upload_url, files=files)
            response.raise_for_status()
            cloud_path = response.json()["path"]
            logger.info(f"Upload complete. Cloud path: {cloud_path}")
            return cloud_path
    except Exception as e:
        logger.error(f"Failed to upload file {local_path}: {e}")
        return local_path

async def download_file_from_cloud(cloud_path: str) -> str:
    """Downloads a file from the cloud proxy-download endpoint to the local outputs dir."""
    if not cloud_path:
        return cloud_path
    
    filename = os.path.basename(cloud_path)
    local_path = OUTPUTS_DIR / filename
    
    logger.info(f"Intercepted cloud path. Downloading to local: {cloud_path}")
    download_url = f"{LTX_CLOUD_URL}/api/proxy/download"
    try:
        async with client.stream("GET", download_url, params={"path": cloud_path}) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    
        local_abs = str(local_path.absolute())
        logger.info(f"Download complete. Local path: {local_abs}")
        return local_abs
    except Exception as e:
        logger.error(f"Failed to download file {cloud_path}: {e}")
        return cloud_path

async def process_uplink_hijack(path: str, body: bytes) -> bytes:
    """Inspects and modifies the request payload to replace local paths with cloud paths."""
    if path in ["api/generate", "api/retake", "api/ic-lora/extract-conditioning", "api/ic-lora/generate"]:
        try:
            data = json.loads(body)
            # Find and replace local paths
            if data.get("imagePath"):
                data["imagePath"] = await upload_file_to_cloud(data["imagePath"])
            if data.get("audioPath"):
                data["audioPath"] = await upload_file_to_cloud(data["audioPath"])
            if data.get("video_path"):
                data["video_path"] = await upload_file_to_cloud(data["video_path"])
            
            if "images" in data and isinstance(data["images"], list):
                for img in data["images"]:
                    if img.get("path"):
                        img["path"] = await upload_file_to_cloud(img["path"])
            
            return json.dumps(data).encode("utf-8")
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Error processing uplink: {e}", exc_info=True)
    return body

async def process_downlink_hijack(path: str, response_body: bytes, status_code: int) -> bytes:
    """Inspects and modifies the response payload to replace cloud paths with local paths."""
    if status_code == 200:
        if path in ["api/generate", "api/retake", "api/ic-lora/generate"]:
            try:
                data = json.loads(response_body)
                if data.get("status") == "complete" and data.get("video_path"):
                    local_path = await download_file_from_cloud(data["video_path"])
                    data["video_path"] = local_path.replace("\\", "/") # Frontend expects posix-like for file://
                return json.dumps(data).encode("utf-8")
            except Exception:
                pass
                
        elif path == "api/ic-lora/extract-conditioning":
            try:
                data = json.loads(response_body)
                if data.get("conditioning"):
                    local_path = await download_file_from_cloud(data["conditioning"])
                    data["conditioning"] = local_path.replace("\\", "/")
                if data.get("original"):
                    local_path = await download_file_from_cloud(data["original"])
                    data["original"] = local_path.replace("\\", "/")
                return json.dumps(data).encode("utf-8")
            except Exception:
                pass
                
    return response_body


# ============================================================
# Catch-All HTTP Relay Route
# ============================================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_catchall(request: Request, path: str):
    """Intercept all requests, modify payload if necessary, and forward to cloud."""
    url = f"{LTX_CLOUD_URL}/{path}"
    
    # Filter request headers
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    body = await request.body()
    body = await process_uplink_hijack(path, body)
    
    try:
        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body,
        )
        response = await client.send(req, stream=False)
        
        response_body = await process_downlink_hijack(path, response.content, response.status_code)
        
        # Filter response headers
        resp_headers = dict(response.headers)
        resp_headers.pop("content-length", None)
        resp_headers.pop("content-encoding", None) # Handled by fastapi/uvicorn
        
        return Response(content=response_body, status_code=response.status_code, headers=resp_headers)
        
    except Exception as e:
        logger.error(f"Proxy error connecting to cloud server: {type(e).__name__} - {e}")
        if path in ["api/generate", "api/retake", "api/ic-lora/generate"]:
            logger.info("Connection dropped during video generation. Fallback tracking progress...")
            import asyncio
            for _ in range(1800): # Allow up to ~1 hour of polling just in case
                await asyncio.sleep(2)
                try:
                    prog_resp = await client.get(f"{LTX_CLOUD_URL}/api/generation/progress")
                    if prog_resp.status_code != 200:
                        continue
                    prog_data = prog_resp.json()
                    status = prog_data.get("status")
                    if status == "complete":
                        cloud_path = prog_data.get("video_path")
                        if cloud_path:
                            local_path = await download_file_from_cloud(cloud_path)
                            resp_data = {"status": "complete", "video_path": local_path.replace("\\", "/")}
                            return JSONResponse(content=resp_data)
                    elif status in ["error", "cancelled"]:
                        return JSONResponse(status_code=500, content={"error": "Cloud generation failed or cancelled."})
                except Exception as poll_e:
                    pass
                    
        return JSONResponse(status_code=502, content={"error": "Cloud server unreachable or timed out."})


if __name__ == "__main__":
    import socket as _socket
    
    port = int(os.environ.get("LTX_PORT", "8000"))
    logger.info("=" * 60)
    logger.info("LTX-Desktop Transparent Proxy Server")
    logger.info(f"Proxying requests to Cloud: {LTX_CLOUD_URL}")
    logger.info("=" * 60)

    # Bind explicitly to print the ready message (match ltx2_server.py behavior)
    sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    actual_port = int(sock.getsockname()[1])

    config = uvicorn.Config(app, host="127.0.0.1", port=actual_port, log_level="info", access_log=False)
    server = uvicorn.Server(config)
    
    _orig_startup = server.startup

    async def _startup_with_ready_msg(sockets: list[_socket.socket] | None = None) -> None:
        await _orig_startup(sockets=sockets)
        if server.started:
            print(f"Server running on http://127.0.0.1:{actual_port}", flush=True)

    server.startup = _startup_with_ready_msg  # type: ignore[assignment]
    
    # Make sure we can run it correctly
    import asyncio
    asyncio.run(server.serve(sockets=[sock]))

