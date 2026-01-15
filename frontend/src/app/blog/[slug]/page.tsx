import { Metadata } from "next"
import { notFound } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Calendar, Clock, User, Eye, Video, Tag, Share2, Bookmark } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LegalLink } from "@/components/legal-modal"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
// Base URL without /api/v1 for serving images
const BASE_URL = API_URL.replace(/\/api\/v1$/, "")

interface Article {
    id: string
    title: string
    slug: string
    excerpt: string | null
    content: string
    category: string
    tags: string[] | null
    featured_image: string | null
    meta_title: string | null
    meta_description: string | null
    featured: boolean
    author_name: string
    view_count: number
    read_time_minutes: number
    published_at: string | null
}

interface PageProps {
    params: Promise<{ slug: string }>
}

async function getArticle(slug: string): Promise<Article | null> {
    try {
        const response = await fetch(`${API_URL}/blog/articles/${slug}`, { next: { revalidate: 60 } })
        if (response.ok) return await response.json()
    } catch (error) {
        console.error("Failed to fetch article:", error)
    }
    return null
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    const { slug } = await params
    const article = await getArticle(slug)
    if (!article) return { title: "Article Not Found" }

    const title = article.meta_title || article.title
    const description = article.meta_description || article.excerpt || ""
    const imageUrl = article.featured_image
        ? (article.featured_image.startsWith("http") ? article.featured_image : `${BASE_URL}${article.featured_image}`)
        : undefined

    return {
        title,
        description,
        openGraph: { title: `${title} | YT Automation Blog`, description, type: "article", publishedTime: article.published_at || undefined, images: imageUrl ? [imageUrl] : undefined },
        twitter: { card: "summary_large_image", title, description, images: imageUrl ? [imageUrl] : undefined },
    }
}

export default async function ArticlePage({ params }: PageProps) {
    const { slug } = await params
    const article = await getArticle(slug)
    if (!article) notFound()

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return ""
        return new Date(dateStr).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })
    }

    const getImageUrl = (image: string | null) => {
        if (!image) return null
        // Already a full URL (cloud storage presigned URL)
        if (image.startsWith("http://") || image.startsWith("https://")) return image
        // Local storage - prepend base URL (without /api/v1)
        return `${BASE_URL}${image}`
    }

    return (
        <div className="min-h-screen bg-white">
            {/* HEADER */}
            <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <Link href="/" className="flex items-center gap-2 group">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg blur opacity-50" />
                                <div className="relative bg-gradient-to-r from-red-500 to-orange-500 p-2 rounded-lg">
                                    <Video className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">YT Automation</span>
                        </Link>
                        <nav className="hidden md:flex items-center gap-8">
                            <Link href="/#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">Features</Link>
                            <Link href="/blog" className="text-sm font-medium text-gray-600 hover:text-gray-900">Blog</Link>
                            <Link href="/#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">Pricing</Link>
                        </nav>
                        <div className="flex items-center gap-3">
                            <Link href="/login"><Button variant="ghost">Sign In</Button></Link>
                            <Link href="/register"><Button className="bg-gradient-to-r from-red-500 to-orange-500 text-white">Get Started</Button></Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero Image */}
            {getImageUrl(article.featured_image) && (
                <div className="pt-16">
                    <div className="relative h-[50vh] min-h-[400px]">
                        <img src={getImageUrl(article.featured_image)!} alt={article.title} className="absolute inset-0 w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                    </div>
                </div>
            )}

            {/* Article Content */}
            <article className={cn("pb-16", !getImageUrl(article.featured_image) && "pt-24")}>
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="max-w-3xl mx-auto">
                        {/* Back Link */}
                        <Link href="/blog" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 transition-colors">
                            <ArrowLeft className="w-4 h-4" />Back to Blog
                        </Link>

                        {/* Article Header */}
                        <header className={cn("mb-8", getImageUrl(article.featured_image) ? "-mt-32 relative z-10" : "")}>
                            <div className={cn("rounded-2xl p-8", getImageUrl(article.featured_image) ? "bg-white shadow-xl" : "")}>
                                <div className="flex items-center gap-3 mb-4">
                                    <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">{article.category}</Badge>
                                    {article.tags?.slice(0, 2).map(tag => (
                                        <Badge key={tag} variant="outline" className="text-gray-600"><Tag className="w-3 h-3 mr-1" />{tag}</Badge>
                                    ))}
                                </div>

                                <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-6 leading-tight">{article.title}</h1>

                                {article.excerpt && (
                                    <p className="text-xl text-gray-600 mb-6 leading-relaxed">{article.excerpt}</p>
                                )}

                                <div className="flex flex-wrap items-center gap-6 text-gray-500 text-sm">
                                    <span className="flex items-center gap-2"><User className="w-4 h-4" />{article.author_name}</span>
                                    <span className="flex items-center gap-2"><Calendar className="w-4 h-4" />{formatDate(article.published_at)}</span>
                                    <span className="flex items-center gap-2"><Clock className="w-4 h-4" />{article.read_time_minutes} min read</span>
                                    <span className="flex items-center gap-2"><Eye className="w-4 h-4" />{article.view_count} views</span>
                                </div>

                                {/* Share buttons */}
                                <div className="flex items-center gap-3 mt-6 pt-6 border-t">
                                    <span className="text-sm text-gray-500">Share:</span>
                                    <Button variant="outline" size="sm"><Share2 className="w-4 h-4 mr-2" />Share</Button>
                                    <Button variant="outline" size="sm"><Bookmark className="w-4 h-4 mr-2" />Save</Button>
                                </div>
                            </div>
                        </header>

                        {/* Article Body */}
                        <div
                            className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-headings:font-bold prose-p:text-gray-600 prose-p:leading-relaxed prose-a:text-purple-600 prose-a:no-underline hover:prose-a:underline prose-strong:text-gray-900 prose-img:rounded-xl prose-blockquote:border-purple-500 prose-blockquote:bg-purple-50 prose-blockquote:py-1 prose-blockquote:not-italic prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none"
                            dangerouslySetInnerHTML={{ __html: article.content }}
                        />

                        {/* Tags */}
                        {article.tags && article.tags.length > 0 && (
                            <div className="mt-12 pt-8 border-t">
                                <h3 className="text-sm font-semibold text-gray-500 mb-4">Tags</h3>
                                <div className="flex flex-wrap gap-2">
                                    {article.tags.map((tag) => (
                                        <Badge key={tag} variant="outline" className="text-gray-600 hover:bg-gray-100 cursor-pointer">{tag}</Badge>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Author Card */}
                        <div className="mt-12 p-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xl font-bold">
                                    {article.author_name.charAt(0)}
                                </div>
                                <div>
                                    <p className="font-semibold text-gray-900">{article.author_name}</p>
                                    <p className="text-sm text-gray-600">Content Writer at YT Automation</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </article>

            {/* CTA */}
            <section className="py-24 bg-gradient-to-br from-purple-500 to-pink-500">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">Ready to Automate Your YouTube Channel?</h2>
                    <p className="text-white/90 mb-8 max-w-2xl mx-auto">Join thousands of creators using YT Automation to grow their channels.</p>
                    <Link href="/register">
                        <Button size="lg" className="bg-white text-purple-600 hover:bg-gray-100 shadow-xl">Start Free Today</Button>
                    </Link>
                </div>
            </section>

            {/* FOOTER */}
            <footer className="bg-gray-900 text-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-16 grid md:grid-cols-2 lg:grid-cols-5 gap-12">
                        <div className="lg:col-span-2">
                            <Link href="/" className="flex items-center gap-3 mb-6">
                                <div className="bg-gradient-to-r from-red-500 to-orange-500 p-2.5 rounded-xl">
                                    <Video className="h-6 w-6 text-white" />
                                </div>
                                <span className="text-2xl font-bold">YT Automation</span>
                            </Link>
                            <p className="text-gray-400 max-w-sm">The all-in-one platform for YouTube creators.</p>
                        </div>
                        <div>
                            <h4 className="font-semibold mb-5">Product</h4>
                            <ul className="space-y-3 text-gray-400">
                                <li><Link href="/#features" className="hover:text-white">Features</Link></li>
                                <li><Link href="/#pricing" className="hover:text-white">Pricing</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold mb-5">Company</h4>
                            <ul className="space-y-3 text-gray-400">
                                <li><Link href="/about" className="hover:text-white">About Us</Link></li>
                                <li><Link href="/blog" className="hover:text-white">Blog</Link></li>
                                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold mb-5">Legal</h4>
                            <ul className="space-y-3 text-gray-400">
                                <li><LegalLink type="privacy" className="hover:text-white">Privacy Policy</LegalLink></li>
                                <li><LegalLink type="terms" className="hover:text-white">Terms of Service</LegalLink></li>
                            </ul>
                        </div>
                    </div>
                    <div className="py-6 border-t border-gray-800 text-center text-sm text-gray-500">
                        © {new Date().getFullYear()} YT Automation. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    )
}

function cn(...classes: (string | boolean | undefined)[]) {
    return classes.filter(Boolean).join(" ")
}
