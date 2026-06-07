/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Experimental features
  experimental: {
    // Server actions
    serverActions: {
      bodySizeLimit: '50mb',
    },
  },
  
  // Images configuration
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
  
  // Transpile packages
  transpilePackages: [],
  
  // eslint config
  eslint: {
    ignoreDuringBuilds: false,
  },
  
  // TypeScript
  typescript: {
    ignoreBuildErrors: false,
  },
}

module.exports = nextConfig