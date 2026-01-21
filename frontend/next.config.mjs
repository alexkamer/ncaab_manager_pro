/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['a.espncdn.com'],
  },
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
