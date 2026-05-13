/**
 * DataMind landing page copy.
 *
 * One typed object so all marketing strings can be edited without touching JSX,
 * and so we can A/B test or i18n later. Voice: declarative, infrastructure-grade,
 * no period on big headlines (Linear/Vercel/Immutable cadence).
 */

/** Public DataMind product doc (architecture + general docs). */
export const DATAMIND_PUBLIC_DOC_URL =
  "https://docs.google.com/document/d/1odF1wLrIvBZknjOHNQkVxi8cSEA0V_b48VRvzKSJEg4/edit?usp=sharing";

export const LANDING = {
  nav: {
    links: [
      { href: "/marketplace", label: "Marketplace" },
      { href: "/search", label: "Search" },
      { href: "/training", label: "Training" },
      { href: "https://docs.0g.ai", label: "Docs", external: true },
    ],
    primaryCta: { href: "/dashboard", label: "Launch app" },
  },

  hero: {
    eyebrow: "Decentralized AI Data Economy",
    headlineLine1: "The decentralized economy",
    headlineLine2: "for AI data",
    gradientWord: "economy",
    sub: "DataMind turns raw files into intelligent, discoverable, reusable AI assets — stored on 0G, owned by you, monetizable on day one.",
    primary: { href: "/dashboard", label: "Launch dashboard" },
    secondary: {
      href: DATAMIND_PUBLIC_DOC_URL,
      label: "Read architecture",
      external: true,
    },
    trust: "Built on 0G Galileo Testnet · Foundry-verified provenance · MIT licensed",
  },

  transformation: {
    from: "Raw files",
    to: "AI-ready assets",
    pillars: ["Semantic Search", "Provenance", "Marketplace", "Fine-Tuning"],
  },

  problem: {
    eyebrow: "Why DataMind",
    title: "AI data infrastructure is broken",
    description:
      "Modern AI lives or dies by data. Today, the people who create the data rarely capture its value, and the systems that consume it can't even find it.",
    items: [
      {
        n: "01",
        title: "Centralized ownership",
        body: "Big tech controls datasets, pipelines, and distribution. Contributors rarely capture the value their data creates.",
      },
      {
        n: "02",
        title: "Poor discoverability",
        body: "Datasets lack semantic indexing and consistent metadata. Finding high-quality data is slow and expensive.",
      },
      {
        n: "03",
        title: "No provenance",
        body: "Attribution is unclear, duplicates are everywhere, and origins are unverifiable. That breaks trust and law.",
      },
      {
        n: "04",
        title: "Fragmented training stack",
        body: "Storage, embeddings, training, evaluation and discovery live in five different tools. There is no unified AI-native data economy.",
      },
      {
        n: "05",
        title: "Static files",
        body: "Today's platforms only store data. They don't analyze, enrich, embed, score, or make it usable for AI.",
      },
    ],
  },

  solution: {
    eyebrow: "DataMind in 60 seconds",
    title: "Datasets that actually train models",
    description:
      "Every upload becomes a structured, searchable, anchored AI asset — analyzed, embedded, scored, stored on 0G, and ready for fine-tuning.",
    pipeline: ["Upload", "Profile", "Embed", "Score", "Anchor on 0G", "Publish", "Train", "Reuse"],
    capabilities: [
      "Drag-and-drop CSV / JSON / TXT / PDF",
      "BGE-small embeddings (384-d)",
      "Quality scoring + semantic tags",
      "Anchored on 0G Storage",
      "One-click LoRA fine-tuning",
      "Marketplace publishing",
      "On-chain provenance via DatasetRegistry.sol",
      "Permissioned access via LicenseRegistry.sol",
    ],
  },

  steps: {
    eyebrow: "How it works",
    title: "From raw data to AI economy in four steps",
    items: [
      {
        n: "01",
        title: "Upload datasets",
        body: "Drag any CSV, JSON, TXT, or PDF. DataMind validates, profiles, and queues an enrichment pipeline in seconds.",
      },
      {
        n: "02",
        title: "Auto-enrich with AI",
        body: "SentenceTransformers embeddings, semantic tags, quality scoring, summary, duplication and missing-value analysis — all generated on ingest.",
      },
      {
        n: "03",
        title: "Anchor on 0G + chain",
        body: "Files land in 0G Storage, the storage root and metadata URI are pinned on DatasetRegistry.sol (Galileo testnet, chain 16602), and a provenance receipt is generated.",
      },
      {
        n: "04",
        title: "Discover, license, train",
        body: "Datasets surface in the marketplace with semantic search. Buyers acquire licenses on-chain. One click launches a LoRA fine-tune on TinyLlama / Phi / Qwen.",
      },
    ],
  },

  capabilities: {
    eyebrow: "Capabilities",
    title: "Four ways to work with your data",
    description:
      "Discovery, training, monetization, verification — every dataset moves through all four layers from the moment it's uploaded.",
    items: [
      {
        tag: "Discover",
        title: "Semantic search",
        body: "Find datasets by meaning, not just tags. 384-dim BGE embeddings, hybrid keyword + vector retrieval.",
        stat: "cosine ≥ 0.78 default",
      },
      {
        tag: "Train",
        title: "LoRA fine-tuning",
        body: "Spin up lightweight fine-tunes on TinyLlama, DistilBERT, Phi-1.5 or Qwen 0.5B. Live training metrics.",
        stat: "~3 min cold start",
      },
      {
        tag: "Monetize",
        title: "Marketplace & licensing",
        body: "Publish, price, and license datasets. The on-chain license registry tracks every grant.",
        stat: "personal · commercial · academic · exclusive",
      },
      {
        tag: "Verify",
        title: "On-chain provenance",
        body: "Every dataset, embedding set and checkpoint is anchored to 0G Storage and notarized on-chain.",
        stat: "chain id 16602 · Foundry-verified",
      },
    ],
  },

  preview: {
    eyebrow: "Inside DataMind",
    title: "Every dataset, fully attributed",
    description:
      "The same product surface judges see in a demo. Letter-grade quality scoring, embeddings counts, owners, prices — all on-chain.",
    sideTitle: "Quality-scored datasets",
    sideBody:
      "Every uploaded file is profiled, deduped, scored and graded. Letter grades feed marketplace ranking, search reranking, and training-pipeline guards.",
    funnel: {
      raw: { value: 10_847, label: "Raw rows" },
      filtered: { value: 1_203, label: "Filtered (duplicates, missing values, low signal)" },
      verified: { value: 9_644, label: "AI-ready chunks" },
    },
    subCard: {
      title: "Built-in quality gates",
      bullets: [
        "Cross-row deduplication",
        "Missing value & schema sanity checks",
        "Length & vocabulary distribution",
        "Embedding cluster purity",
      ],
    },
  },

  zerog: {
    eyebrow: "0G Integration",
    title: "Anchored to 0G. Verified on-chain.",
    description:
      "DataMind speaks 0G end-to-end — storage, compute and the EVM-compatible Galileo testnet — with a clean abstraction layer that flips between mocked and live with a single env var.",
    columns: [
      {
        title: "0G Storage",
        body: "Datasets, embedding exports, training checkpoints. All persisted to 0G Storage with a content-addressable merkle root.",
      },
      {
        title: "0G Compute",
        body: "Embedding and training jobs flow through a JobRunner abstraction. Local runner today, OG Compute runner tomorrow — same interface.",
      },
      {
        title: "Galileo Testnet",
        body: "DatasetRegistry.sol and LicenseRegistry.sol live on Galileo (chain id 16602). Every record carries a tx hash and storage root.",
      },
    ],
    snippet: `# Backend (Python)
from app.services.storage import og_client
from app.services.chain import registry

# Push the dataset to 0G Storage
result = await og_client.upload(path)
# -> {"root": "0x…", "tx_hash": "0x…", "size": 1024, "mode": "live"}

# Anchor it in the on-chain registry
chain = await registry.register_dataset(
    storage_root=result["root"],
    metadata_uri=f"0g://{result['root']}",
)
# -> {"onchain_id": 12, "tx_hash": "0x…", "chain_id": 16602}`,
    docsUrl: "https://docs.0g.ai/",
  },

  marketplacePreview: {
    eyebrow: "Marketplace",
    title: "Browse the dataset economy",
    description:
      "Real datasets, real on-chain provenance. Filter by category or quality grade, click any card to open the full provenance + training launcher.",
    chips: ["All", "Finance", "NLP", "Web3", "Tabular", "Vision"],
  },

  vision: {
    eyebrow: "Vision",
    title: "Beyond a marketplace",
    description:
      "DataMind is the foundation for an open, ownable, programmable AI data economy. Marketplace today, coordination layer tomorrow.",
    pillars: [
      "Decentralized AI dataset marketplace",
      "AI training coordination layer",
      "Synthetic dataset factory",
      "Collaborative model training platform",
      "AI provenance + licensing protocol",
    ],
  },

  faq: {
    eyebrow: "FAQ",
    title: "Frequently asked questions",
    items: [
      {
        q: "How does DataMind use 0G Storage and 0G Compute?",
        a: "Every uploaded file is pushed to 0G Storage and anchored on-chain via DatasetRegistry.sol. Embedding generation, dataset analysis and LoRA fine-tuning are scheduled through a JobRunner that targets either the local AI engine or the 0G Compute network — same interface, single env var to switch.",
      },
      {
        q: "What dataset formats are supported and how big can they be?",
        a: "CSV, JSON, JSONL, TSV, TXT, PDF, and Parquet. The default upload limit is 200 MB; raise it with BACKEND_MAX_UPLOAD_MB. Larger datasets stream through chunked upload and never hit memory.",
      },
      {
        q: "Which models can I fine-tune, and how long does training take?",
        a: "TinyLlama-1.1B, DistilBERT, Phi-1.5, and Qwen-0.5B are wired by default. Cold start on a small machine is ~3 minutes; warm cycles run in under a minute.",
      },
      {
        q: "Who owns my dataset, and how is provenance verified?",
        a: "The wallet that uploads a dataset is the on-chain owner. Provenance is enforced by DatasetRegistry.sol, which records the 0G storage root and metadata URI. License grants are minted via LicenseRegistry.sol with optional expiry.",
      },
      {
        q: "How does licensing and pricing work?",
        a: "Datasets can be free or priced in OG. License kinds: personal, commercial, academic, exclusive. Exclusive licenses revoke other grants. All revocations are on-chain.",
      },
      {
        q: "Is DataMind production-ready or testnet only?",
        a: "DataMind is a hackathon MVP wired against 0G Galileo testnet. Mock mode is on by default so the demo runs without keys; flip DATAMIND_OG_MOCK=0 + provide OG_PRIVATE_KEY to publish live.",
      },
    ],
  },

  marquee: {
    label: "Datasets shipping on DataMind",
    items: [
      "Crypto Twitter Sentiment",
      "DeFi Protocol Documentation",
      "Onchain Anomaly Events",
      "Solana DEX Trades",
      "Ethereum NFT Metadata",
      "Lending Liquidations",
      "ZK Proof Set",
      "LLM Eval Harness",
      "Synthetic FX Ticks",
      "Stablecoin Flows",
      "Restaking Operator Returns",
      "RWA Settlement Logs",
    ],
  },

  cta: {
    title: "The decentralized economy for AI data starts here.",
    sub: "Spin up the full stack in a single script. No keys required for the demo.",
    primary: { href: "/dashboard", label: "Connect wallet" },
    secondary: {
      href: DATAMIND_PUBLIC_DOC_URL,
      label: "Read docs",
      external: true,
    },
    tertiary: { href: "https://github.com", label: "View on GitHub" },
  },

  footer: {
    columns: [
      {
        title: "Product",
        links: [
          { href: "/marketplace", label: "Marketplace" },
          { href: "/search", label: "Semantic search" },
          { href: "/upload", label: "Upload" },
          { href: "/training", label: "Training studio" },
        ],
      },
      {
        title: "Builders",
        links: [
          { href: "/dashboard", label: "Dashboard" },
          { href: "https://github.com", label: "GitHub", external: true },
          { href: "/docs/API.md", label: "API" },
          {
            href: DATAMIND_PUBLIC_DOC_URL,
            label: "Architecture",
            external: true,
          },
        ],
      },
      {
        title: "Network",
        links: [
          { href: "https://docs.0g.ai", label: "0G Docs", external: true },
          { href: "https://chainscan-galileo.0g.ai", label: "Galileo Explorer", external: true },
          { href: "/docs/0G_INTEGRATION.md", label: "0G Integration" },
        ],
      },
      {
        title: "Legal",
        links: [
          { href: "/legal/privacy", label: "Privacy" },
          { href: "/legal/terms", label: "Terms" },
          { href: "/LICENSE", label: "License" },
        ],
      },
    ],
    builtOn: { label: "Built on 0G", href: "https://docs.0g.ai" },
  },
} as const;

export type LandingCopy = typeof LANDING;
