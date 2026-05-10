"""Semantic tag + topic extraction.

KeyBERT-style: embed candidate phrases against a curated vocabulary and pick
the top-K by cosine similarity to the document centroid.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from datamind_ai.embeddings import embed_many, embed_one

# Curated tag vocabulary covering the categories DataMind cares about.
TAG_VOCABULARY: list[str] = [
    # Web3 / DeFi
    "defi", "crypto", "ethereum", "solana", "bitcoin", "smart contracts", "dex",
    "lending", "yield", "liquidations", "mev", "rollups", "zk proofs", "oracle",
    "stablecoins", "lst", "restaking",
    # Trading / finance
    "trading", "sentiment", "ohlcv", "orderbook", "options", "perps", "macro",
    "market making", "risk", "volatility", "arbitrage", "ltcg",
    # AI / NLP
    "embeddings", "sentiment analysis", "classification", "summarization",
    "instruction tuning", "rag", "retrieval", "fine-tuning",
    # Vision / multimodal
    "image", "nft", "metadata", "rarity",
    # Tabular / general
    "tabular", "time series", "labeled", "synthetic", "benchmark", "evaluation",
    "documentation", "research", "academic",
]


_word_re = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


def extract_semantic_tags(text: str, top_k: int = 7) -> list[str]:
    if not text.strip():
        return []
    doc_vec = embed_one(text[:5000])
    tag_vecs = embed_many(TAG_VOCABULARY)
    scored = sorted(
        zip(TAG_VOCABULARY, tag_vecs),
        key=lambda pair: _cosine(doc_vec, pair[1]),
        reverse=True,
    )
    return [t for t, _ in scored[:top_k]]


def extract_topics(text: str, top_k: int = 5) -> list[dict]:
    """Light-weight n-gram frequency to pick out distinctive topic phrases."""
    if not text.strip():
        return []
    words = [w.lower() for w in _word_re.findall(text)][:20_000]
    if not words:
        return []
    bigrams = [f"{a} {b}" for a, b in zip(words, words[1:])]
    common = Counter(bigrams).most_common(40)
    # Filter out generic combos
    bad = {"of the", "in the", "for the", "to the", "and the"}
    filtered = [(p, c) for p, c in common if p not in bad and len(p) > 5]
    if not filtered:
        return []
    total = sum(c for _, c in filtered) or 1
    return [
        {"label": p.title(), "weight": round(c / total, 4)}
        for p, c in filtered[:top_k]
    ]
