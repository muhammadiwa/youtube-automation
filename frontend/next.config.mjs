/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'yt3.ggpht.com',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'i.ytimg.com',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: '*.googleusercontent.com',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'lh3.googleusercontent.com',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'www.youtube.com',
                pathname: '/**',
            },
            // Cloudflare R2 storage
            {
                protocol: 'https',
                hostname: '*.r2.dev',
                pathname: '/**',
            },
            // AWS S3
            {
                protocol: 'https',
                hostname: '*.s3.amazonaws.com',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: '*.s3.*.amazonaws.com',
                pathname: '/**',
            },
            // MinIO (local development)
            {
                protocol: 'http',
                hostname: 'localhost',
                port: '9000',
                pathname: '/**',
            },
        ],
    },
};

export default nextConfig;
