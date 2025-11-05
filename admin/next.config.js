/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lantern-room.s3.amazonaws.com',
      },
    ],
  },
  async rewrites() {
    // Ensure backend URL has protocol
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const backendUrlWithProtocol = backendUrl.startsWith('http')
      ? backendUrl
      : `https://${backendUrl}`;

    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrlWithProtocol}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
