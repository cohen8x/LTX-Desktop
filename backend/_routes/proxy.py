"""Route handlers for /api/proxy/upload and /api/proxy/download (Cloud Server side)."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/proxy", tags=["proxy"])

def _get_upload_dir() -> Path:
    env_path = os.environ.get("LTX_APP_DATA_DIR")
    base_dir = Path(env_path) if env_path else Path.cwd()
    upload_dir = base_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

@router.post("/upload")
async def route_proxy_upload(file: UploadFile = File(...)) -> dict[str, str]:
    """Receive an uploaded file from the local proxy and return its absolute path on the cloud."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    
    upload_dir = _get_upload_dir()
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    return {"path": os.path.abspath(file_path).replace("\\", "/")}

@router.get("/download")
async def route_proxy_download(path: str) -> FileResponse:
    """Download a generated file by its absolute path on the cloud."""
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(path=file_path, filename=file_path.name)
