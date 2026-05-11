from fastapi import APIRouter

from app.api.v1 import (
    auth,
    datasets,
    embeddings,
    marketplace,
    search,
    storage,
    training,
    web3,
    websocket,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(web3.router, prefix="/web3", tags=["web3"])

__all__ = ["api_router", "websocket"]
