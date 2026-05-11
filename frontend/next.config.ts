import type { NextConfig } from "next";

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
};

export default nextConfig;
