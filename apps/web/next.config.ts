import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@eventra/contracts"],
  webpack: (config) => {
    return config;
  },
};

export default nextConfig;
