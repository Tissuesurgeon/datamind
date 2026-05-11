"""Demo seeder.

Populates Postgres + Qdrant with six showcase datasets so the marketplace
and the landing page's `<DashboardPreview/>` look real out of the box.

Idempotent: re-running won't create duplicates; it `UPSERTS` on title.
"""

from __future__ import annotations

import asyncio
import csv
import json
import random
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db.session import session_scope
from app.models.dataset import Dataset, DatasetFile, DatasetStatus, DatasetVisibility
from app.models.dataset_analytics import DatasetAnalytics
from app.models.user import User
from app.services.chain import registry as chain_registry
from app.services.embeddings.chunker import chunk_csv, chunk_text
from app.services.embeddings.indexer import ensure_collection, index_chunks
from app.services.storage import og_client
from app.utils.files import file_sha256

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = REPO_ROOT / "scripts" / "seed"

log = get_logger(__name__)


SEED_OWNER = {
    "wallet_address": "0xdemo000000000000000000000000000000000001",
    "display_name": "DataMind Labs",
    "email": "labs@datamind.dev",
}


SEED_DATASETS: list[dict[str, Any]] = [
    {
        "title": "Crypto Twitter Sentiment",
        "description": (
            "Hand-labeled tweets across BTC / ETH / SOL with sentiment, sarcasm "
            "and topic tags — ideal for trader-LM fine-tuning and signal mining."
        ),
        "category": "Web3",
        "tags": ["sentiment", "twitter", "crypto", "btc", "eth", "trading"],
        "format": "csv",
        "rows": 10_847,
        "columns": 6,
        "quality_score": 0.91,
        "ai_readiness": 0.94,
        "quality_grade": "A",
        "downloads": 2_140,
        "views": 8_902,
        "price_amount": 12.0,
        "price_token": "OG",
        "license_kind": "commercial",
        "summary": (
            "10,847 hand-labeled tweets covering BTC, ETH and SOL — sentiment, "
            "sarcasm and topic tags. Validated label agreement κ = 0.81."
        ),
        "semantic_tags": [
            "crypto", "sentiment", "trading", "twitter", "btc", "eth", "social",
        ],
        "topics": [
            {"label": "Bitcoin price action", "weight": 0.27},
            {"label": "Ethereum upgrades", "weight": 0.18},
            {"label": "Memecoin hype cycles", "weight": 0.15},
            {"label": "Macro / Fed outlook", "weight": 0.12},
            {"label": "DeFi narratives", "weight": 0.11},
        ],
        "quality_metrics": {
            "completeness": 0.97,
            "uniqueness": 0.93,
            "schema_consistency": 0.99,
            "label_agreement_kappa": 0.81,
        },
        "duplicate_ratio": 0.014,
        "missing_ratio": 0.005,
        "sample_rows": [
            {"text": "ETH ETF flows are absurd this week", "sentiment": "bullish"},
            {"text": "Bitcoin chop continues, Powell speech soon", "sentiment": "neutral"},
            {"text": "SOL devs keep shipping while everyone else cries", "sentiment": "bullish"},
        ],
    },
    {
        "title": "DeFi Protocol Documentation Corpus",
        "description": (
            "Cleaned developer docs for 42 top DeFi protocols (Aave, Uniswap, "
            "Curve, Compound, Maker, Lido, GMX, …) — pre-chunked for RAG."
        ),
        "category": "NLP",
        "tags": ["defi", "documentation", "rag", "smart-contracts"],
        "format": "json",
        "rows": 26_544,
        "columns": 5,
        "quality_score": 0.87,
        "ai_readiness": 0.90,
        "quality_grade": "A",
        "downloads": 1_504,
        "views": 5_802,
        "price_amount": 24.0,
        "price_token": "OG",
        "license_kind": "commercial",
        "summary": (
            "26.5k docs paragraphs from 42 DeFi protocols, deduped + chunk-aligned "
            "to 256 tokens. Ready for RAG pipelines and code-aware fine-tuning."
        ),
        "semantic_tags": ["defi", "rag", "documentation", "smart contracts"],
        "topics": [
            {"label": "Lending markets", "weight": 0.22},
            {"label": "AMM design", "weight": 0.19},
            {"label": "Liquidations", "weight": 0.13},
            {"label": "Governance", "weight": 0.12},
        ],
        "quality_metrics": {"completeness": 0.95, "uniqueness": 0.91, "schema_consistency": 0.98},
        "duplicate_ratio": 0.022,
        "missing_ratio": 0.011,
        "sample_rows": [
            {"protocol": "Aave", "section": "isolation_mode", "text": "Isolation mode caps debt against newly listed assets…"},
            {"protocol": "Uniswap", "section": "v4_hooks", "text": "Hooks let pools execute custom logic at lifecycle points…"},
        ],
    },
    {
        "title": "Onchain Anomaly Events",
        "description": (
            "Labeled timeline of MEV sandwiches, oracle deviations, large "
            "rebalances, and exploit signatures across 5 chains."
        ),
        "category": "Web3",
        "tags": ["mev", "anomalies", "exploits", "onchain"],
        "format": "csv",
        "rows": 8_120,
        "columns": 11,
        "quality_score": 0.78,
        "ai_readiness": 0.83,
        "quality_grade": "B",
        "downloads": 906,
        "views": 3_122,
        "price_amount": 18.0,
        "price_token": "OG",
        "license_kind": "academic",
        "summary": "8.1k labeled onchain anomaly events with chain, block, type, severity.",
        "semantic_tags": ["mev", "exploit", "anomaly", "ethereum", "solana"],
        "topics": [
            {"label": "MEV sandwich", "weight": 0.34},
            {"label": "Oracle deviation", "weight": 0.21},
            {"label": "Liquidation cascades", "weight": 0.18},
        ],
        "quality_metrics": {"completeness": 0.88, "uniqueness": 0.84, "schema_consistency": 0.96},
        "duplicate_ratio": 0.04,
        "missing_ratio": 0.06,
        "sample_rows": [
            {"chain": "ethereum", "type": "mev_sandwich", "severity": "high"},
            {"chain": "solana", "type": "oracle_dev", "severity": "medium"},
        ],
    },
    {
        "title": "Solana DEX Trades — 30d",
        "description": (
            "30 days of trades from Raydium, Orca, Phoenix and Lifinity with "
            "user clustering and wallet-cohort tags."
        ),
        "category": "Finance",
        "tags": ["solana", "dex", "trades", "tabular"],
        "format": "parquet",
        "rows": 1_240_006,
        "columns": 17,
        "quality_score": 0.81,
        "ai_readiness": 0.85,
        "quality_grade": "B",
        "downloads": 612,
        "views": 2_188,
        "price_amount": 30.0,
        "price_token": "OG",
        "license_kind": "commercial",
        "summary": "1.2M trade events across four Solana DEXs over the last 30 days.",
        "semantic_tags": ["solana", "dex", "trades", "raydium", "orca"],
        "topics": [
            {"label": "Memecoin rotations", "weight": 0.26},
            {"label": "Stablecoin arb", "weight": 0.19},
        ],
        "quality_metrics": {"completeness": 0.92, "uniqueness": 0.78, "schema_consistency": 1.0},
        "duplicate_ratio": 0.18,
        "missing_ratio": 0.01,
        "sample_rows": [
            {"dex": "raydium", "pair": "SOL/USDC", "side": "buy", "size_usd": 412.18},
            {"dex": "orca", "pair": "JLP/USDC", "side": "sell", "size_usd": 8210.0},
        ],
    },
    {
        "title": "Ethereum NFT Metadata",
        "description": (
            "Cleaned metadata + traits for 4M NFTs across 1,200 collections, "
            "with rarity scores and cluster embeddings."
        ),
        "category": "Vision",
        "tags": ["nft", "ethereum", "metadata", "rarity"],
        "format": "json",
        "rows": 4_012_300,
        "columns": 9,
        "quality_score": 0.71,
        "ai_readiness": 0.74,
        "quality_grade": "B",
        "downloads": 488,
        "views": 1_480,
        "price_amount": 9.0,
        "price_token": "OG",
        "license_kind": "personal",
        "summary": "Metadata for 4M NFTs, normalized trait schema, rarity index pre-computed.",
        "semantic_tags": ["nft", "metadata", "rarity", "ethereum"],
        "topics": [{"label": "Profile pictures", "weight": 0.41}, {"label": "Generative art", "weight": 0.23}],
        "quality_metrics": {"completeness": 0.84, "uniqueness": 0.69, "schema_consistency": 0.95},
        "duplicate_ratio": 0.27,
        "missing_ratio": 0.13,
        "sample_rows": [
            {"collection": "Pudgy Penguins", "id": 1234, "rarity": 0.012},
            {"collection": "Azuki", "id": 6789, "rarity": 0.041},
        ],
    },
    {
        "title": "Lending Liquidations Across Chains",
        "description": (
            "Cross-chain liquidation events from Aave, Compound, Morpho, "
            "Spark and Kamino. Includes pre-liquidation health factor curves."
        ),
        "category": "Finance",
        "tags": ["lending", "liquidations", "risk", "defi"],
        "format": "csv",
        "rows": 41_902,
        "columns": 14,
        "quality_score": 0.66,
        "ai_readiness": 0.68,
        "quality_grade": "C",
        "downloads": 214,
        "views": 821,
        "price_amount": 6.0,
        "price_token": "OG",
        "license_kind": "academic",
        "summary": "Cross-chain lending liquidations with pre-event health factor curves.",
        "semantic_tags": ["liquidation", "lending", "risk", "defi"],
        "topics": [{"label": "Vol regime", "weight": 0.31}, {"label": "Cascade events", "weight": 0.22}],
        "quality_metrics": {"completeness": 0.71, "uniqueness": 0.78, "schema_consistency": 0.91},
        "duplicate_ratio": 0.06,
        "missing_ratio": 0.18,
        "sample_rows": [
            {"protocol": "Aave-v3", "asset": "WETH", "size_usd": 184_213.5},
            {"protocol": "Morpho", "asset": "USDC", "size_usd": 12_400.0},
        ],
    },
]


def _ensure_seed_files() -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)

    crypto_csv = SEED_DIR / "crypto_twitter_sentiment.csv"
    if not crypto_csv.exists():
        rng = random.Random(42)
        sentiments = ["bullish", "bearish", "neutral"]
        coins = ["BTC", "ETH", "SOL", "ARB", "TIA", "LINK"]
        snippets = [
            "ETF flows look insane this week",
            "Powell speech could nuke the rally",
            "L2 rollups keep eating mainnet TVL",
            "Memecoin season is officially back",
            "Restaking yield finally cooling off",
            "GMX liquidity feels thin tonight",
            "Solana DEX volume just printed a new ATH",
            "BTC chop is going nowhere fast",
            "DeFi blue chips are coiling up",
            "Funding rates are flipping negative",
        ]
        with open(crypto_csv, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "timestamp", "coin", "text", "sentiment", "label_quality"])
            for i in range(800):
                writer.writerow(
                    [
                        i,
                        f"2026-01-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z",
                        rng.choice(coins),
                        f"{rng.choice(snippets)} #{rng.choice(coins).lower()}",
                        rng.choice(sentiments),
                        round(0.7 + rng.random() * 0.3, 2),
                    ]
                )

    for ds in SEED_DATASETS[1:]:
        path = SEED_DIR / f"{ds['title'].lower().replace(' ', '_').replace('—', '').replace('-', '_')}.txt"
        if not path.exists():
            path.write_text(
                f"{ds['title']}\n\n"
                f"{ds['description']}\n\n"
                f"Categories: {', '.join(ds['tags'])}\n"
                f"Topics: {', '.join(t['label'] for t in ds['topics'])}\n"
                f"Sample summary: {ds['summary']}\n"
            )


async def _seed() -> None:
    _ensure_seed_files()
    await ensure_collection()

    async with session_scope() as db:
        # Seed owner
        res = await db.execute(
            select(User).where(User.wallet_address == SEED_OWNER["wallet_address"])
        )
        user = res.scalar_one_or_none()
        if user is None:
            user = User(**SEED_OWNER)
            db.add(user)
            await db.flush()

        for spec in SEED_DATASETS:
            res = await db.execute(select(Dataset).where(Dataset.title == spec["title"]))
            d = res.scalar_one_or_none()
            if d is not None:
                log.info("seed.dataset.skip", title=spec["title"])
                continue

            d = Dataset(
                owner_id=user.id,
                title=spec["title"],
                description=spec["description"],
                category=spec["category"],
                tags=spec["tags"],
                format=spec["format"],
                rows=spec["rows"],
                columns=spec["columns"],
                size_bytes=spec["rows"] * spec["columns"] * 32,
                quality_score=spec["quality_score"],
                ai_readiness=spec["ai_readiness"],
                quality_grade=spec["quality_grade"],
                downloads=spec["downloads"],
                views=spec["views"],
                visibility=DatasetVisibility.PUBLIC,
                status=DatasetStatus.READY,
                progress=100,
                price_amount=spec["price_amount"],
                price_token=spec["price_token"],
                license_kind=spec["license_kind"],
            )
            db.add(d)
            await db.flush()

            # Pick the relevant seed file (only crypto has a CSV; others get a text blob).
            if spec["title"] == "Crypto Twitter Sentiment":
                src = SEED_DIR / "crypto_twitter_sentiment.csv"
                chunks = chunk_csv(src, max_rows_per_chunk=10)
            else:
                src = SEED_DIR / f"{spec['title'].lower().replace(' ', '_').replace('—', '').replace('-', '_')}.txt"
                chunks = chunk_text(src.read_text())

            sha = await file_sha256(src)
            file = DatasetFile(
                dataset_id=d.id,
                filename=src.name,
                mime_type="text/csv" if spec["format"] == "csv" else "text/plain",
                size_bytes=src.stat().st_size,
                sha256=sha,
                local_path=str(src),
            )
            db.add(file)

            og = await og_client.upload(src, dedupe_salt=d.id)
            d.storage_root = og["root"]
            d.storage_tx_hash = og.get("tx_hash")
            d.metadata_uri = f"0g://{og['root']}"

            chain = await chain_registry.register_dataset(
                storage_root=og["root"], metadata_uri=d.metadata_uri
            )
            d.chain_id = chain.get("chain_id")
            d.onchain_id = chain.get("onchain_id")

            indexed = await index_chunks(
                dataset_id=d.id,
                owner_wallet=user.wallet_address,
                title=d.title,
                category=d.category,
                tags=list(d.tags or []),
                chunks=chunks,
            )
            d.embeddings_count = indexed

            a = DatasetAnalytics(
                dataset_id=d.id,
                summary=spec["summary"],
                semantic_tags=spec["semantic_tags"],
                topics=spec["topics"],
                quality_metrics=spec["quality_metrics"],
                duplicate_ratio=spec["duplicate_ratio"],
                missing_ratio=spec["missing_ratio"],
                column_profile={},
                sample_rows=spec["sample_rows"],
            )
            db.add(a)

            log.info(
                "seed.dataset.created",
                title=spec["title"],
                rows=spec["rows"],
                embeddings=indexed,
            )

    log.info("seed.done", count=len(SEED_DATASETS))


def main() -> None:
    configure_logging()
    asyncio.run(_seed())


if __name__ == "__main__":
    main()
