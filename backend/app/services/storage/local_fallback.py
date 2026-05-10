"""Local file-system fallback for environments where 0G isn't reachable."""

from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import get_settings


def stage_local(src: Path, dataset_id: str) -> Path:
    """Ensure `src` lives under upload_dir/<dataset_id>; return the final path."""
    settings = get_settings()
    target_dir = settings.upload_dir / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / src.name
    if src.resolve() != target.resolve():
        shutil.copy2(src, target)
    return target
