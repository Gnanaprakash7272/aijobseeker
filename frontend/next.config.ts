import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",           // enables Docker multi-stage build
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;
