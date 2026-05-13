function stripTrailingSlash(s: string): string {
  return s.replace(/\/+$/, "");
}

function isLocalBrowserHost(): boolean {
  if (typeof window === "undefined") return false;
  const h = window.location.hostname;
  return h === "localhost" || h === "127.0.0.1" || h === "[::1]";
}

/** Base URL for REST (e.g. https://api.example.com/api/v1). No trailing slash. */
export function getApiBase(): string {
  const env = process.env.NEXT_PUBLIC_API_BASE?.trim();
  if (env) {
    return stripTrailingSlash(env);
  }
  // Deployed site without env: same-origin rewrite → avoids localhost + CORS.
  if (typeof window !== "undefined" && !isLocalBrowserHost()) {
    return `${window.location.origin}/api/proxy`;
  }
  return "http://localhost:8000/api/v1";
}

/** Download URL for a blob by 0G storage root (goes to FastAPI `/storage/{root}`, not Next.js). */
export function getStorageFetchUrl(storageRoot: string): string {
  const root = storageRoot.trim();
  const base = getApiBase();
  return `${base}/storage/${encodeURIComponent(root)}`;
}

function httpApiToWsBase(apiUrl: string): string | null {
  try {
    const u = new URL(apiUrl);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    u.pathname = "/ws";
    u.search = "";
    u.hash = "";
    return stripTrailingSlash(u.toString());
  } catch {
    return null;
  }
}

/** WebSocket base (e.g. wss://api.example.com/ws). No trailing slash. */
export function getWsBase(): string {
  const env = process.env.NEXT_PUBLIC_WS_BASE?.trim();
  if (env) {
    return stripTrailingSlash(env);
  }
  const api = getApiBase();
  if (api.startsWith("http://") || api.startsWith("https://")) {
    const w = httpApiToWsBase(api);
    if (w) return w;
  }
  if (typeof window !== "undefined" && !isLocalBrowserHost()) {
    // Proxied REST does not give us a WS URL; caller must set NEXT_PUBLIC_WS_BASE.
    if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
      console.warn(
        "[datamind] Set NEXT_PUBLIC_WS_BASE to your API WebSocket URL (e.g. wss://api.yourdomain.com/ws)."
      );
    }
  }
  return "ws://localhost:8000/ws";
}

export const ENV = {
  get apiBase() {
    return getApiBase();
  },
  get wsBase() {
    return getWsBase();
  },
  privyAppId: process.env.NEXT_PUBLIC_PRIVY_APP_ID || "",
  chainId: Number(process.env.NEXT_PUBLIC_CHAIN_ID || "16602"),
  githubUrl: process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com",
  docsUrl:
    process.env.NEXT_PUBLIC_DOCS_URL ||
    "https://docs.google.com/document/d/1odF1wLrIvBZknjOHNQkVxi8cSEA0V_b48VRvzKSJEg4/edit?usp=sharing",
};

export const PRIVY_LIVE = ENV.privyAppId.length > 0;
