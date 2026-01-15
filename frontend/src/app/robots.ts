import { MetadataRoute } from 'next'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ytautomation.com'

export default function robots(): MetadataRoute.Robots {
    return {
        rules: [
            {
                userAgent: '*',
                allow: '/',
                disallow: [
                    '/dashboard/',
                    '/api/',
                    '/login',
                    '/register',
                    '/forgot-password',
                    '/reset-password',
                ],
            },
        ],
        sitemap: `${BASE_URL}/sitemap.xml`,
    }
}
