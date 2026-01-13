"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
    ArrowRight,
    Video,
    Calendar,
    Clock,
    Search,
    // eslint-disable-next-line @typescript-eslint/no-deprecated
    Youtube
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { LegalLink } from "@/components/legal-modal"

// Blog posts data
const posts = [
    { id: 1, title: "10 Tips to Grow Your YouTube Channel in 2024", excerpt: "Learn the latest strategies to boost your subscriber count and engagement.", category: "Growth", date: "Jan 10, 2024", readTime: "5 min read", featured: true },
    { id: 2, title: "How to Set Up 24/7 Live Streams", excerpt: "A complete guide to running continuous live streams on your channel.", category: "Tutorial", date: "Jan 8, 2024", readTime: "8 min read", featured: false },
    { id: 3, title: "Understanding YouTube Analytics", excerpt: "Deep dive into the metrics that matter for your channel's success.", category: "Analytics", date: "Jan 5, 2024", readTime: "6 min read", featured: false },
    { id: 4, title: "Best Practices for Video SEO", excerpt: "Optimize your videos to rank higher in YouTube search results.", category: "SEO", date: "Jan 3, 2024", readTime: "7 min read", featured: false },
    { id: 5, title: "Monetization Strategies Beyond AdSense", excerpt: "Explore alternative revenue streams for content creators.", category: "Monetization", date: "Dec 28, 2023", readTime: "10 min read", featured: false },
    { id: 6, title: "Building a Community Around Your Channel", excerpt: "Tips for engaging with your audience and building loyal fans.", category: "Community", date: "Dec 25, 2023", readTime: "6 min read", featured: false },
]

const categories = ["All", "Growth", "Tutorial", "Analytics", "SEO", "Monetization", "Community"]

export default function BlogPage() {
    const featuredPost = posts.find(p => p.featured)
    const regularPosts = posts.filter(p => !p.featured)

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
                                    <Youtube className="h-5 w-5 text-white" />
                                </div>
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">YT Automation</span>
                        </Link>
                        <nav className="hidden md:flex items-center gap-8">
                            <Link href="/#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Features</Link>
                            <Link href="/#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">How it Works</Link>
                            <Link href="/#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Pricing</Link>
                        </nav>
                        <div className="flex items-center gap-3">
                            <Link href="/login"><Button variant="ghost" className="text-gray-600 hover:text-gray-900">Sign In</Button></Link>
                            <Link href="/register"><Button className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-lg shadow-red-500/25">Get Started</Button></Link>
                        </div>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="pt-32 pb-16 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-purple-50 to-white" />
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-3xl mx-auto">
                        <Badge className="mb-4 bg-indigo-50 text-indigo-600 border-indigo-200">Blog</Badge>
                        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
                            Insights for <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">YouTube Creators</span>
                        </h1>
                        <p className="text-xl text-gray-600 mb-8">Tips, tutorials, and strategies to help you grow your channel.</p>
                        <div className="relative max-w-md mx-auto">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <Input placeholder="Search articles..." className="pl-10 h-12" />
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Categories */}
            <section className="py-8 bg-white border-y border-gray-100">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex flex-wrap gap-2 justify-center">
                        {categories.map((cat) => (
                            <Button key={cat} variant={cat === "All" ? "default" : "outline"} size="sm" className={cat === "All" ? "bg-gradient-to-r from-red-500 to-orange-500 text-white" : ""}>
                                {cat}
                            </Button>
                        ))}
                    </div>
                </div>
            </section>

            {/* Featured Post */}
            {featuredPost && (
                <section className="py-16">
                    <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="bg-white rounded-3xl shadow-xl overflow-hidden">
                            <div className="grid lg:grid-cols-2">
                                <div className="bg-gradient-to-br from-red-500 to-orange-500 p-12 flex items-center justify-center">
                                    <div className="text-center text-white">
                                        <Badge className="bg-white/20 text-white border-white/30 mb-4">Featured</Badge>
                                        <h2 className="text-3xl font-bold">{featuredPost.title}</h2>
                                    </div>
                                </div>
                                <div className="p-12">
                                    <Badge className="mb-4">{featuredPost.category}</Badge>
                                    <h3 className="text-2xl font-bold text-gray-900 mb-4">{featuredPost.title}</h3>
                                    <p className="text-gray-600 mb-6">{featuredPost.excerpt}</p>
                                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
                                        <span className="flex items-center gap-1"><Calendar className="w-4 h-4" />{featuredPost.date}</span>
                                        <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{featuredPost.readTime}</span>
                                    </div>
                                    <Button className="bg-gradient-to-r from-red-500 to-orange-500 text-white">Read Article <ArrowRight className="ml-2 w-4 h-4" /></Button>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </section>
            )}

            {/* Blog Grid */}
            <section className="py-16">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {regularPosts.map((post, i) => (
                            <motion.article key={post.id} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow group cursor-pointer">
                                <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                                    <Video className="w-12 h-12 text-gray-400" />
                                </div>
                                <div className="p-6">
                                    <Badge variant="secondary" className="mb-3">{post.category}</Badge>
                                    <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-red-500 transition-colors">{post.title}</h3>
                                    <p className="text-gray-600 text-sm mb-4">{post.excerpt}</p>
                                    <div className="flex items-center gap-4 text-xs text-gray-500">
                                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{post.date}</span>
                                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{post.readTime}</span>
                                    </div>
                                </div>
                            </motion.article>
                        ))}
                    </div>
                    <div className="text-center mt-12">
                        <Button variant="outline" size="lg">Load More Articles</Button>
                    </div>
                </div>
            </section>

            {/* Newsletter */}
            <section className="py-24 bg-gradient-to-br from-indigo-500 to-purple-500">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl font-bold text-white mb-4">Subscribe to Our Newsletter</h2>
                    <p className="text-white/90 mb-8 max-w-2xl mx-auto">Get the latest tips and strategies delivered to your inbox.</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
                        <Input placeholder="Enter your email" className="bg-white/10 border-white/20 text-white placeholder:text-white/60" />
                        <Button className="bg-white text-indigo-600 hover:bg-gray-100">Subscribe</Button>
                    </div>
                </div>
            </section>

            {/* FOOTER */}
            <footer className="relative bg-gray-900 text-white overflow-hidden">
                <div className="absolute inset-0 opacity-5">
                    <div className="absolute inset-0" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")` }} />
                </div>
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 via-orange-500 to-amber-500" />
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <div className="py-16 grid md:grid-cols-2 lg:grid-cols-5 gap-12">
                        <div className="lg:col-span-2">
                            <Link href="/" className="flex items-center gap-3 mb-6 group">
                                <div className="relative">
                                    <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl blur opacity-50 group-hover:opacity-75 transition-opacity" />
                                    <div className="relative bg-gradient-to-r from-red-500 to-orange-500 p-2.5 rounded-xl">
                                        <Video className="h-6 w-6 text-white" />
                                    </div>
                                </div>
                                <span className="text-2xl font-bold">YT Automation</span>
                            </Link>
                            <p className="text-gray-400 leading-relaxed mb-6 max-w-sm">The all-in-one platform for YouTube creators who want to scale their channels efficiently.</p>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-5 flex items-center gap-2"><div className="w-1 h-4 bg-gradient-to-b from-red-500 to-orange-500 rounded-full" />Product</h4>
                            <ul className="space-y-3">
                                <li><Link href="/#features" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Features</Link></li>
                                <li><Link href="/#pricing" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Pricing</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-5 flex items-center gap-2"><div className="w-1 h-4 bg-gradient-to-b from-orange-500 to-amber-500 rounded-full" />Company</h4>
                            <ul className="space-y-3">
                                <li><Link href="/about" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />About Us</Link></li>
                                <li><Link href="/blog" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Blog</Link></li>
                                <li><Link href="/careers" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Careers</Link></li>
                                <li><Link href="/contact" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Contact</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-5 flex items-center gap-2"><div className="w-1 h-4 bg-gradient-to-b from-amber-500 to-yellow-500 rounded-full" />Legal</h4>
                            <ul className="space-y-3">
                                <li><LegalLink type="privacy" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Privacy Policy</LegalLink></li>
                                <li><LegalLink type="terms" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Terms of Service</LegalLink></li>
                            </ul>
                        </div>
                    </div>
                    <div className="py-6 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <p className="text-sm text-gray-500">© {new Date().getFullYear()} YT Automation. All rights reserved.</p>
                        <div className="flex items-center gap-6 text-sm text-gray-500">
                            <span className="flex items-center gap-2"><div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />All systems operational</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    )
}
