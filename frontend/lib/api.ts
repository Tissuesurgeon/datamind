"use client";

import { ENV } from "@/lib/env";
import { useAuthStore } from "@/lib/auth-store";

export class ApiError extends Error {
  constructor(public status: number, public detail: string, public url: string) {
    super(`${status} ${detail}`);
  }
}

type RequestOpts = {
  method?: string;
  body?: unknown;
  formData?: FormData;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  auth?: boolean;
};

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { method = "GET", body, formData, headers = {}, signal, auth = true } = opts;
  const url = path.startsWith("http") ? path : `${ENV.apiBase}${path}`;

  const finalHeaders: Record<string, string> = { Accept: "application/json", ...headers };
  if (!formData) {
    if (body !== undefined) finalHeaders["Content-Type"] = "application/json";
  }
  if (auth) {
    const token = useAuthStore.getState().token;
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method,
    headers: finalHeaders,
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
    signal,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || data.error || JSON.stringify(data);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail, url);
  }
  if (res.status === 204) return undefined as T;
  const ctype = res.headers.get("content-type") || "";
  if (ctype.includes("application/json")) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

export const api = {
  get: <T,>(path: string, opts?: RequestOpts) => request<T>(path, { ...opts, method: "GET" }),
  post: <T,>(path: string, body?: unknown, opts?: RequestOpts) =>
    request<T>(path, { ...opts, method: "POST", body }),
  patch: <T,>(path: string, body?: unknown, opts?: RequestOpts) =>
    request<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T,>(path: string, opts?: RequestOpts) =>
    request<T>(path, { ...opts, method: "DELETE" }),
  upload: <T,>(path: string, fd: FormData) =>
    request<T>(path, { method: "POST", formData: fd }),
};
