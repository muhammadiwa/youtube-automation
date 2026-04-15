import { Metadata } from "next"
import BlogPageClient from "./blog-client"

export const metadata: Metadata = {
    title: "Blog",
    description: "Tips, tutorials, and insights for YouTube creators. Learn how to grow your channel, optimize your content, and automate your workflow.",
    openGraph: {
        title: "Blog | YT Automation",
        description: "Tips, tutorials, and insights for YouTube creators.",
        type: "website",
    },
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Article {
    id: string
    title: string
    slug: string
    excerpt: string | null
    category: string
    featured: boolean
    author_name: string
    read_time_minutes: number
    published_at: string | null
    featured_image: string | null
    view_count: number
}

async function getArticles(): Promise<{ items: Article[]; categories: string[] }> {
    try {
        const response = await fetch(`${API_URL}/blog/articles?page_size=50`, {
            next: { revalidate: 60 },
        })

        if (response.ok) {
            const data = await response.json()
            const categoriesRes = await fetch(`${API_URL}/blog/categories`, {
                next: { revalidate: 3600 },
            })
            const categories = categoriesRes.ok ? await categoriesRes.json() : []
            return { items: data.items, categories: ["All", ...categories] }
        }
    } catch (error) {
        console.error("Failed to fetch articles:", error)
    }

    // Return empty if API fails
    return { items: [], categories: ["All"] }
}

export default async function BlogPage() {
    const { items, categories } = await getArticles()
    return <BlogPageClient articles={items} categories={categories} />
}
