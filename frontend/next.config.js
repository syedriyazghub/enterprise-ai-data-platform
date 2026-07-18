/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_GATEWAY_URL: process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000',
    NEXT_PUBLIC_INGESTION_URL: process.env.NEXT_PUBLIC_INGESTION_URL || 'http://localhost:8001',
    NEXT_PUBLIC_VALIDATION_URL: process.env.NEXT_PUBLIC_VALIDATION_URL || 'http://localhost:8002',
    NEXT_PUBLIC_AI_SERVICE_URL: process.env.NEXT_PUBLIC_AI_SERVICE_URL || 'http://localhost:8004',
    NEXT_PUBLIC_ANALYTICS_URL: process.env.NEXT_PUBLIC_ANALYTICS_URL || 'http://localhost:8008',
  },
  async rewrites() {
    return [
      { source: '/api/gateway/:path*', destination: `${process.env.API_GATEWAY_URL || 'http://localhost:8000'}/:path*` },
    ];
  },
};

module.exports = nextConfig;
