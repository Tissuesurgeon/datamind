"""Reset the DataMind Postgres database to a clean slate.

Drops every public table and every project-owned enum type, plus the
alembic_version bookkeeping table. After this runs successfully, a fresh
`alembic upgrade head` will apply the initial schema from scratch.

Usage (from repo root):
    backend/.venv/bin/python scripts/db_reset.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import get_engine  # noqa: E402

ENUMS = (
    "dataset_visibility",
    "dataset_status",
    "training_job_status",
    "license_kind",
)


async def reset() -> None:
    settings = get_settings()
    print(f"[db_reset] target: {settings.database_url}")
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # Defensive: even though DROP SCHEMA CASCADE removes the enums, run
        # explicit DROP TYPE IF EXISTS so this script is safe to re-run.
        for name in ENUMS:
            await conn.execute(text(f"DROP TYPE IF EXISTS {name} CASCADE"))
    await engine.dispose()
    print("[db_reset] schema reset. Run `alembic upgrade head` next.")


if __name__ == "__main__":
    asyncio.run(reset())
