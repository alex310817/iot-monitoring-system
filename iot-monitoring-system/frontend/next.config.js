/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  
  // Basic optimization
  compress: true,
  poweredByHeader: false,
  
  // Basic image settings
  images: {
    domains: ['localhost'],
  },
  
  // Оптимизация для разработки
  reactStrictMode: false,
  webpack: (config) => {
    // Disable cache during development to prevent ENOENT errors
    config.cache = false;

    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
    }
    return config
  },
}

module.exports = nextConfig
