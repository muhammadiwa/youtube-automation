import { MetadataRoute } from 'next'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ytautomation.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    // Static pages
    const staticPages: MetadataRoute.Sitemap = [
        {
            url: BASE_URL,
            lastModified: new Date(),
            changeFrequency: 'weekly',
            priority: 1,
        },
        {
            url: `${BASE_URL}/about`,
            lastModified: new Date(),
            changeFrequency: 'monthly',
            priority: 0.8,
        },
        {
            url: `${BASE_URL}/blog`,
            lastModified: new Date(),
            changeFrequency: 'daily',
            priority: 0.9,
        },
        {
            url: `${BASE_URL}/contact`,
            lastModified: new Date(),
            changeFrequency: 'monthly',
            priority: 0.7,
        },
        {
            url: `${BASE_URL}/careers`,
            lastModified: new Date(),
            changeFrequency: 'weekly',
            priority: 0.6,
        },
    ]

    // Fetch blog articles from API (if available)
    let blogPages: MetadataRoute.Sitemap = []
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/v1/blog/articles?page_size=100`, {
            next: { revalidate: 3600 }, // Revalidate every hour
        })

        if (response.ok) {
            const data = await response.json()
            blogPages = data.items.map((article: { slug: string; updated_at: string }) => ({
                url: `${BASE_URL}/blog/${article.slug}`,
                lastModified: new Date(article.updated_at),
                changeFrequency: 'weekly' as const,
                priority: 0.7,
            }))
        }
    } catch (error) {
        console.error('Failed to fetch blog articles for sitemap:', error)
    }

    return [...staticPages, ...blogPages]
}
