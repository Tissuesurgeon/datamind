export type DatasetStatus = "uploading" | "processing" | "ready" | "failed";
export type DatasetVisibility = "public" | "private" | "unlisted";
export type QualityGrade = "A" | "B" | "C";

export type DatasetSummary = {
  id: string;
  title: string;
  category: string;
  tags: string[];
  quality_score: number | null;
  quality_grade: QualityGrade | null;
  ai_readiness: number | null;
  rows: number;
  embeddings_count: number;
  downloads: number;
  visibility: DatasetVisibility;
  status: DatasetStatus;
  progress: number;
  storage_root: string | null;
  onchain_id: number | null;
  owner_wallet: string;
  created_at: string;
};

export type DatasetMarketplaceItem = DatasetSummary & {
  description: string | null;
  price_amount: number | null;
  price_token: string | null;
  license_kind: string | null;
};

export type DatasetDetail = DatasetMarketplaceItem & {
  format: string;
  size_bytes: number;
  columns: number;
  storage_tx_hash: string | null;
  metadata_uri: string | null;
  summary: string | null;
  semantic_tags: string[];
  topics: { label: string; weight: number }[];
  quality_metrics: Record<string, number>;
  sample_rows: Record<string, unknown>[];
};

export type DatasetUploadResponse = {
  dataset: DatasetSummary;
  ws_topic: string;
};

export type Page<T> = {
  items: T[];
  page: { total: number; limit: number; offset: number };
};

export type SearchResult = {
  dataset_id: string;
  title: string;
  category: string;
  score: number;
  snippet: string;
  quality_grade: QualityGrade | null;
  embeddings_count: number;
  owner_wallet: string;
};

export type SearchResponse = {
  query: string;
  mode: string;
  took_ms: number;
  results: SearchResult[];
};

export type TrainingJobStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export type TrainingJob = {
  id: string;
  name: string;
  dataset_id: string;
  base_model: string;
  task: string;
  status: TrainingJobStatus;
  progress: number;
  epoch: number;
  metrics: {
    history?: TrainingHistoryPoint[];
    last?: TrainingHistoryPoint;
    final_loss?: number;
    eval_loss?: number;
    accuracy?: number;
    [k: string]: unknown;
  };
  error: string | null;
  checkpoint_root: string | null;
  checkpoint_tx_hash: string | null;
  config: {
    epochs?: number;
    batch_size?: number;
    learning_rate?: number;
    [k: string]: unknown;
  };
  created_at: string;
  updated_at: string;
};

export type TrainingHistoryPoint = {
  step: number;
  epoch: number;
  loss: number;
  learning_rate?: number;
  progress?: number;
  elapsed_s?: number;
};

export type RealtimeEvent = {
  type: string;
  topic: string;
  payload: Record<string, unknown>;
  ts: number;
};
