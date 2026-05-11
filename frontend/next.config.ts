import type { NextConfig } from "next";
import path from "path";

// Server-side rewrite target (set in Vercel/Railway to your FastAPI root + /api/v1).
// BACKEND_INTERNAL_URL keeps the real API URL out of the browser when using /api/proxy.
const apiBase = (
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_BASE ||
  "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion", "recharts"],
  },
  async rewrites() {
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${apiBase}/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // @metamask/sdk (via wagmi MetaMask connector) optional-deps RN storage — not used on web.
    config.resolve.alias = {
      ...config.resolve.alias,
      "@react-native-async-storage/async-storage": path.join(
        __dirname,
        "lib/stubs/async-storage.js"
      ),
    };
    return config;
  },
};

export default nextConfig;
