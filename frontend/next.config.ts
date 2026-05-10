import type { NextConfig } from "next";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion", "recharts"],
  },
  async rewrites() {
    return [
      // Optionally proxy API in dev to avoid CORS during local work.
      { source: "/api/proxy/:path*", destination: `${apiBase}/:path*` },
    ];
  },
};

export default nextConfig;
