export const ENV = {
  apiBase: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1",
  wsBase: process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000/ws",
  privyAppId: process.env.NEXT_PUBLIC_PRIVY_APP_ID || "",
  chainId: Number(process.env.NEXT_PUBLIC_CHAIN_ID || "16602"),
  githubUrl: process.env.NEXT_PUBLIC_GITHUB_URL || "https://github.com",
  docsUrl: process.env.NEXT_PUBLIC_DOCS_URL || "https://docs.0g.ai",
};

export const PRIVY_LIVE = ENV.privyAppId.length > 0;
