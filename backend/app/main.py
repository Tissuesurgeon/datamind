"""FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from app import __version__
from app.api.v1 import api_router, websocket as ws_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter
from app.db.session import dispose
from app.schemas.common import HealthOut
from app.services.realtime import get_ws_manager
from app.services.storage import og_client
from app.web3.listeners import start_indexer, stop_indexer

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("backend.starting", version=__version__)
    settings = get_settings()
    await get_ws_manager().start()
    await og_client.warmup()
    await start_indexer()
    log.info(
        "backend.ready",
        env=settings.env,
        og_mock=settings.og_mock,
        chain_live=settings.chain_live,
        privy_live=settings.privy_live,
        web3_user_tx=settings.web3_user_tx,
        chain_indexer=settings.chain_indexer_enabled,
    )
    try:
        yield
    finally:
        log.info("backend.stopping")
        await stop_indexer()
        await get_ws_manager().shutdown()
        await dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DataMind API",
        version=__version__,
        description="Decentralized AI data economy backend.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    @app.get("/health", response_model=HealthOut, tags=["meta"])
    async def health() -> HealthOut:
        return HealthOut(
            status="ok",
            version=__version__,
            services={
                "og": "live" if settings.storage_live else "mock",
                "chain": "live" if settings.chain_live else "mock",
                "privy": "live" if settings.privy_live else "mock",
            },
        )

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router.router)  # mounts at /ws/{topic}
    return app


app = create_app()
