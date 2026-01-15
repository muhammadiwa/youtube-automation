"use client"

import { useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import {
    ArrowRight,
    Video,
    Calendar,
    Clock,
    Search,
    User,
    Eye,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
    category: string
    featured: boolean
    author_name: string
    read_time_minutes: number
    published_at: string | null
    featured_image: string | null
    view_count: number
}

interface BlogPageClientProps {
    articles: Article[]
    categories: string[]
}

export default function BlogPageClient({ articles, categories }: BlogPageClientProps) {
    const [selectedCategory, setSelectedCategory] = useState("All")
    const [searchQuery, setSearchQuery] = useState("")

    const filteredPosts = articles.filter(post => {
        const matchesCategory = selectedCategory === "All" || post.category === selectedCategory
        const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (post.excerpt?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
        return matchesCategory && matchesSearch
    })

    const featuredPost = filteredPosts.find(p => p.featured)
    const regularPosts = filteredPosts.filter(p => !p.featured)

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return ""
        return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    }

    const getImageUrl = (image: string | null) => {
        if (!image) return null
        // Already a full URL (cloud storage presigned URL)
        if (image.startsWith("http://") || image.startsWith("https://")) return image
        // Local storage - prepend base URL (without /api/v1)
        return `${BASE_URL}${image}`
    }

    return (
        <div className="min-h-screen bg-[#F9FAFB]">
            {/* HEADER */}
            <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <Link href="/" className="flex items-center gap-2 group">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg blur opacity-50 group-hover:opacity-75 transition-opacity" />
                                <div className="relative bg-gradient-to-r from-red-500 to-orange-500 p-2 rounded-lg">
                                    <Video className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">YT Automation</span>
                        </Link>
                        <nav className="hidden md:flex items-center gap-8">
                            <Link href="/#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">Features</Link>
                            <Link href="/#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900">How it Works</Link>
                            <Link href="/#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">Pricing</Link>
                        </nav>
                        <div className="flex items-center gap-3">
                            <Link href="/login"><Button variant="ghost">Sign In</Button></Link>
                            <Link href="/register"><Button className="bg-gradient-to-r from-red-500 to-orange-500 text-white">Get Started</Button></Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero */}
            <section className="pt-32 pb-16 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-pink-50 to-white" />
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-3xl mx-auto">
                        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
                            YT Automation <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">Blog</span>
                        </h1>
                        <p className="text-xl text-gray-600 mb-8">Tips, tutorials, and insights to help you grow your YouTube channel.</p>
                        <div className="relative max-w-md mx-auto">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <Input placeholder="Search articles..." className="pl-12 h-12 rounded-full" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Categories */}
            <section className="py-8">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-wrap justify-center gap-3">
                        {categories.map((cat) => (
                            <Button key={cat} variant={selectedCategory === cat ? "default" : "outline"}
                                className={selectedCategory === cat ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white border-0" : ""}
                                onClick={() => setSelectedCategory(cat)}>{cat}</Button>
                        ))}
                    </div>
                </div>
            </section>

            {/* Featured Post */}
            {featuredPost && (
                <section className="py-8">
                    <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                            <Link href={`/blog/${featuredPost.slug}`}>
                                <div className="relative rounded-3xl overflow-hidden group cursor-pointer">
                                    <div className="aspect-[21/9] relative">
                                        {getImageUrl(featuredPost.featured_image) ? (
                                            <img src={getImageUrl(featuredPost.featured_image)!} alt={featuredPost.title} className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                                        ) : (
                                            <div className="w-full h-full bg-gradient-to-br from-purple-500 to-pink-500" />
                                        )}
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                                    </div>
                                    <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
                                        <Badge className="bg-white/20 text-white mb-4">Featured</Badge>
                                        <h2 className="text-2xl md:text-4xl font-bold mb-4">{featuredPost.title}</h2>
                                        <p className="text-white/90 mb-6 max-w-2xl line-clamp-2">{featuredPost.excerpt}</p>
                                        <div className="flex items-center gap-6 text-white/80 text-sm">
                                            <span className="flex items-center gap-2"><User className="w-4 h-4" />{featuredPost.author_name}</span>
                                            <span className="flex items-center gap-2"><Calendar className="w-4 h-4" />{formatDate(featuredPost.published_at)}</span>
                                            <span className="flex items-center gap-2"><Clock className="w-4 h-4" />{featuredPost.read_time_minutes} min read</span>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        </motion.div>
                    </div>
                </section>
            )}

            {/* Blog Posts Grid */}
            <section className="py-16">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    {regularPosts.length === 0 && !featuredPost ? (
                        <div className="text-center py-12">
                            <p className="text-gray-500 text-lg">No articles found.</p>
                        </div>
                    ) : (
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {regularPosts.map((post, i) => (
                                <motion.div key={post.id} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}>
                                    <Link href={`/blog/${post.slug}`}>
                                        <article className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 group h-full flex flex-col">
                                            <div className="aspect-video relative overflow-hidden">
                                                {getImageUrl(post.featured_image) ? (
                                                    <img src={getImageUrl(post.featured_image)!} alt={post.title} className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                                                ) : (
                                                    <div className="w-full h-full bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                                                        <Video className="w-12 h-12 text-purple-300" />
                                                    </div>
                                                )}
                                                <Badge className="absolute top-4 left-4 bg-white/90 text-gray-700">{post.category}</Badge>
                                            </div>
                                            <div className="p-6 flex-1 flex flex-col">
                                                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors line-clamp-2">{post.title}</h3>
                                                <p className="text-gray-600 text-sm mb-4 flex-1 line-clamp-3">{post.excerpt}</p>
                                                <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t">
                                                    <div className="flex items-center gap-4">
                                                        <span className="flex items-center gap-1"><Calendar className="w-4 h-4" />{formatDate(post.published_at)}</span>
                                                        <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{post.read_time_minutes} min</span>
                                                    </div>
                                                    <span className="flex items-center gap-1"><Eye className="w-4 h-4" />{post.view_count}</span>
                                                </div>
                                            </div>
                                        </article>
                                    </Link>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </section>

            {/* Newsletter CTA */}
            <section className="py-24 bg-gradient-to-br from-purple-500 to-pink-500">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">Stay Updated</h2>
                    <p className="text-white/90 mb-8 max-w-2xl mx-auto">Get the latest tips and tutorials delivered to your inbox.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
                        <Input placeholder="Enter your email" className="bg-white/10 border-white/20 text-white placeholder:text-white/60" />
                        <Button className="bg-white text-purple-600 hover:bg-gray-100">Subscribe</Button>
                    </div>
                </div>
            </section>

            {/* FOOTER */}
            <footer className="bg-gray-900 text-white">
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-orange-500 to-amber-500" />
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
