"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  DatasetDetail,
  DatasetMarketplaceItem,
  DatasetSummary,
  DatasetUploadResponse,
  Page,
  SearchResponse,
  TrainingJob,
} from "@/types";

// ----- Datasets ------------------------------------------------------------

export function useDatasets(opts: { mine?: boolean; category?: string } = {}) {
  const params = new URLSearchParams();
  if (opts.mine) params.set("mine", "true");
  if (opts.category) params.set("category", opts.category);
  const q = params.toString() ? `?${params}` : "";
  return useQuery({
    queryKey: ["datasets", opts],
    queryFn: () => api.get<Page<DatasetSummary>>(`/datasets${q}`),
  });
}

export function useDataset(id: string | null | undefined) {
  return useQuery({
    queryKey: ["dataset", id],
    enabled: Boolean(id),
    queryFn: () => api.get<DatasetDetail>(`/datasets/${id}`),
  });
}

export function useUploadDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fd: FormData) => api.upload<DatasetUploadResponse>("/datasets", fd),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["datasets"] });
      qc.invalidateQueries({ queryKey: ["marketplace"] });
    },
  });
}

// ----- Marketplace ---------------------------------------------------------

export function useMarketplace(opts: { category?: string; sort?: string; limit?: number } = {}) {
  const params = new URLSearchParams();
  if (opts.category && opts.category.toLowerCase() !== "all") params.set("category", opts.category);
  if (opts.sort) params.set("sort", opts.sort);
  if (opts.limit) params.set("limit", String(opts.limit));
  const q = params.toString() ? `?${params}` : "";
  return useQuery({
    queryKey: ["marketplace", opts],
    queryFn: () => api.get<Page<DatasetMarketplaceItem>>(`/marketplace${q}`),
  });
}

export function useTrending(limit = 6) {
  return useQuery({
    queryKey: ["marketplace", "trending", limit],
    queryFn: () => api.get<DatasetMarketplaceItem[]>(`/marketplace/trending?limit=${limit}`),
  });
}

// ----- Search --------------------------------------------------------------

export function useSearch() {
  return useMutation({
    mutationFn: (body: { query: string; limit?: number; min_score?: number; mode?: string; category?: string }) =>
      api.post<SearchResponse>(`/search/${body.mode || "semantic"}`, body),
  });
}

// ----- Training ------------------------------------------------------------

export function useTrainingJobs() {
  return useQuery({
    queryKey: ["training", "jobs"],
    queryFn: () => api.get<TrainingJob[]>("/training/jobs"),
  });
}

export function useTrainingJob(id: string | null) {
  return useQuery({
    queryKey: ["training", "job", id],
    enabled: Boolean(id),
    refetchInterval: (q) => {
      const data = q.state.data as TrainingJob | undefined;
      return data && (data.status === "succeeded" || data.status === "failed") ? false : 4000;
    },
    queryFn: () => api.get<TrainingJob>(`/training/jobs/${id}`),
  });
}

export function useCreateTraining() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      dataset_id: string;
      name: string;
      base_model: string;
      epochs: number;
      batch_size: number;
      learning_rate: number;
      lora_r: number;
      lora_alpha: number;
      max_seq_length: number;
    }) => api.post<TrainingJob>("/training/jobs", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["training", "jobs"] });
    },
  });
}
