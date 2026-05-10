"""SentenceTransformers loader + deterministic fallback.

The first request lazily loads the model. If `sentence-transformers` isn't
installed (or the model can't be downloaded), we fall back to a deterministic
hash-based embedding so the demo never breaks.
"""

from __future__ import annotations

import hashlib
import logging
import math
import threading

from datamind_ai.config import get_config

log = logging.getLogger(__name__)

_DEFAULT_DIM = 384
_lock = threading.Lock()
_model = None
_model_name: str | None = None
_dim: int = _DEFAULT_DIM
_real: bool = False


def _try_load() -> None:
    global _model, _model_name, _dim, _real
    if _model is not None or _real is True:
        return
    cfg = get_config()
    try:
        from sentence_transformers import SentenceTransformer

        log.info("loading SentenceTransformer model=%s", cfg.embedding_model)
        m = SentenceTransformer(cfg.embedding_model, cache_folder=str(cfg.hf_cache))
        _model = m
        _model_name = cfg.embedding_model
        _dim = int(m.get_sentence_embedding_dimension() or _DEFAULT_DIM)
        _real = True
        log.info("model ready name=%s dim=%d", _model_name, _dim)
    except Exception as exc:  # pragma: no cover — slow path / offline
        log.warning("falling back to deterministic embed: %s", exc)
        _model = None
        _model_name = "deterministic-sha512"
        _dim = _DEFAULT_DIM
        _real = False


def get_model_name() -> str:
    if _model_name is None:
        _try_load()
    return _model_name or "deterministic-sha512"


def get_dim() -> int:
    if _model is None and not _real:
        _try_load()
    return _dim


def is_real_model() -> bool:
    if _model is None and not _real:
        _try_load()
    return _real


def _fallback(text: str) -> list[float]:
    if not text:
        text = " "
    seed = hashlib.sha512(text.encode("utf-8")).digest()
    buf = b""
    while len(buf) < _dim * 4:
        seed = hashlib.sha512(seed).digest()
        buf += seed
    ints = [int.from_bytes(buf[i : i + 4], "big") for i in range(0, _dim * 4, 4)]
    floats = [(i / 0xFFFFFFFF) * 2.0 - 1.0 for i in ints]
    norm = math.sqrt(sum(x * x for x in floats)) or 1.0
    return [x / norm for x in floats]


def embed_one(text: str) -> list[float]:
    with _lock:
        if _model is None and not _real:
            _try_load()
    if _model is not None:
        vec = _model.encode(text, normalize_embeddings=True).tolist()
        return list(vec)
    return _fallback(text)


def embed_many(texts: list[str]) -> list[list[float]]:
    with _lock:
        if _model is None and not _real:
            _try_load()
    if _model is not None:
        arr = _model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
        return [list(v) for v in arr]
    return [_fallback(t) for t in texts]
