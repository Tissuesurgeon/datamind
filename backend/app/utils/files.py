"""File ingest helpers — hashing, format sniffing, safe writes."""

from __future__ import annotations

import asyncio
import hashlib
import mimetypes
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_EXTENSIONS = {".csv", ".json", ".jsonl", ".txt", ".pdf", ".tsv", ".parquet"}
ALLOWED_MIME_PREFIXES = ("text/", "application/")


async def save_upload(file: UploadFile, dataset_id: str) -> tuple[Path, str, int]:
    """Stream `file` to disk, returning `(path, sha256_hex, size_bytes)`.

    Validates extension + size before persisting.
    """
    settings = get_settings()
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"unsupported extension {ext!r}",
        )

    target_dir = settings.upload_dir / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / file.filename

    sha = hashlib.sha256()
    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024

    async with aiofiles.open(target, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                await out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"file exceeds {settings.max_upload_mb}MB limit",
                )
            sha.update(chunk)
            await out.write(chunk)

    return target, sha.hexdigest(), size


def sniff_format(filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    return ext or "bin"


def guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def detect_format(path: Path) -> str:
    """Return one of csv|json|jsonl|txt|pdf|tsv|parquet."""
    return path.suffix.lower().lstrip(".") or "bin"


async def file_sha256(path: Path) -> str:
    """Async SHA-256 of a file already on disk."""
    h = hashlib.sha256()

    def _hash() -> str:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    return await asyncio.to_thread(_hash)
