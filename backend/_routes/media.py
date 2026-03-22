"""Route handlers for /api/upload and /api/media."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from _routes._errors import HTTPError
from app_handler import AppHandler
from state import get_state_service

router = APIRouter(prefix="/api", tags=["media"])

@router.post("/upload")
async def route_upload(
    file: UploadFile = File(...),
    handler: AppHandler = Depends(get_state_service),
) -> dict[str, str]:
    """POST /api/upload - Receive a multipart file and save to outputs directory."""
    if not file.filename:
        raise HTTPError(400, "No filename provided")

    # Generate a unique path inside outputs_dir
    ext = os.path.splitext(file.filename)[1]
    fd, temp_path = tempfile.mkstemp(dir=handler.config.outputs_dir, suffix=ext, prefix="uploaded_")
    with os.fdopen(fd, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": temp_path}


@router.get("/media")
def route_get_media(
    path: str,
    handler: AppHandler = Depends(get_state_service),
) -> FileResponse:
    """GET /api/media?path=... - Stream a file from the backend."""
    target_path = Path(path).resolve()
    base_dir = handler.config.outputs_dir.resolve()

    # Security check: Ensure the requested path is inside outputs_dir
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise HTTPError(403, "Access denied: file is outside outputs directory")

    if not target_path.is_file():
        raise HTTPError(404, "File not found")

    return FileResponse(str(target_path))
