import type { NextConfig } from "next";

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${AGENT_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
