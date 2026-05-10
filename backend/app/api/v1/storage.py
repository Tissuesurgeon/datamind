"""Storage proxy — fetch a file by 0G storage root or local fallback."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.storage import og_client

router = APIRouter()


@router.get("/{root}")
async def fetch_storage(root: str):
    path = await og_client.download(root)
    if path is None:
        raise HTTPException(status_code=404, detail="storage object not found")
    return FileResponse(path)
