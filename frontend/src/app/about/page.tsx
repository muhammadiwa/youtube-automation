"use client"

import { motion } from "framer-motion"
import {
    Target,
    Heart,
    Zap,
    Users,
    Globe,
    ArrowRight,
    Sparkles,
    Shield,
    Video,
    Clock,
    Rocket,
    // eslint-disable-next-line @typescript-eslint/no-deprecated
    Youtube
} from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LegalLink } from "@/components/legal-modal"

// Animation variants
const fadeInUp = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
}

const staggerContainer = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.1 } }
}

// Values data
const values = [
    { icon: Heart, title: "Creator First", description: "Every feature starts with one question: how does this help creators succeed?", bg: "bg-rose-50", iconBg: "bg-gradient-to-br from-rose-500 to-pink-600" },
    { icon: Zap, title: "Innovation", description: "We push boundaries to deliver cutting-edge automation that saves you hours.", bg: "bg-amber-50", iconBg: "bg-gradient-to-br from-amber-500 to-orange-600" },
    { icon: Shield, title: "Trust & Security", description: "Enterprise-grade security protects your channels and data 24/7.", bg: "bg-blue-50", iconBg: "bg-gradient-to-br from-blue-500 to-indigo-600" },
    { icon: Users, title: "Community", description: "Join 10,000+ creators who grow together and support each other.", bg: "bg-emerald-50", iconBg: "bg-gradient-to-br from-emerald-500 to-teal-600" }
]

// Why Choose Us
const whyChooseUs = [
    { icon: Clock, title: "Save 20+ Hours/Week", description: "Automate repetitive tasks and focus on creating content" },
    { icon: Rocket, title: "Grow 3x Faster", description: "Our creators see 3x faster channel growth on average" },
    { icon: Shield, title: "99.9% Uptime", description: "Enterprise-grade reliability you can count on" },
    { icon: Globe, title: "Global Support", description: "24/7 support team across multiple time zones" }
]

export default function AboutPage() {
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
            <section className="pt-32 pb-20 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-red-50 via-orange-50 to-white" />
                <div className="absolute top-20 right-0 w-96 h-96 bg-gradient-to-br from-red-200 to-orange-200 rounded-full blur-3xl opacity-30" />
                <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-br from-indigo-200 to-purple-200 rounded-full blur-3xl opacity-30" />

                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="text-center max-w-4xl mx-auto">
                        <motion.div variants={fadeInUp}>
                            <Badge className="mb-6 bg-red-50 text-red-600 border-red-200">
                                <Sparkles className="w-3 h-3 mr-1" />
                                About Us
                            </Badge>
                        </motion.div>
                        <motion.h1 variants={fadeInUp} className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                            Empowering <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">YouTube Creators</span> Worldwide
                        </motion.h1>
                        <motion.p variants={fadeInUp} className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
                            We&apos;re on a mission to help content creators automate their workflows, grow their channels, and focus on what they do best — creating amazing content.
                        </motion.p>
                    </motion.div>
                </div>
            </section>

            {/* Why Choose Us Section */}
            <section className="py-20 bg-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-14">
                        <Badge className="mb-4 bg-blue-50 text-blue-600 border-blue-200">Why Choose Us</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">The <span className="bg-gradient-to-r from-blue-500 to-indigo-500 bg-clip-text text-transparent">Smart Choice</span> for Creators</h2>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {whyChooseUs.map((item, i) => (
                            <motion.div key={item.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="relative group">
                                <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl blur-xl opacity-0 group-hover:opacity-20 transition-opacity duration-500" />
                                <div className="relative bg-white border border-gray-100 rounded-2xl p-6 hover:border-red-200 hover:shadow-xl transition-all duration-300">
                                    <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                        <item.icon className="w-6 h-6 text-white" />
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-2">{item.title}</h3>
                                    <p className="text-gray-600 text-sm">{item.description}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Story Section */}
            <section className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <motion.div initial={{ opacity: 0, x: -30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}>
                            <Badge className="mb-4 bg-orange-50 text-orange-600 border-orange-200">Our Story</Badge>
                            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
                                From Creators, <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">For Creators</span>
                            </h2>
                            <div className="space-y-4 text-gray-600 leading-relaxed">
                                <p>YT Automation was born out of frustration. As content creators ourselves, we spent countless hours managing multiple channels, scheduling streams, and monitoring analytics across different platforms.</p>
                                <p>In 2022, we decided to build the tool we wished existed — a unified platform that handles all the tedious work so creators can focus on what matters most: creating content that inspires and entertains.</p>
                                <p>Today, we&apos;re proud to serve over 10,000 creators worldwide, helping them save time, grow their audiences, and turn their passion into sustainable careers.</p>
                            </div>
                        </motion.div>
                        <motion.div initial={{ opacity: 0, x: 30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }} className="relative">
                            <div className="bg-gradient-to-br from-red-500 to-orange-500 rounded-3xl p-8 text-white">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
                                        <Target className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <h3 className="text-2xl font-bold">Our Mission</h3>
                                        <p className="text-white/80">What drives us every day</p>
                                    </div>
                                </div>
                                <p className="text-lg leading-relaxed text-white/90">&quot;To democratize YouTube success by providing every creator — regardless of their technical skills or budget — with the tools they need to automate, optimize, and scale their channels.&quot;</p>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Values Section - FIXED ICONS */}
            <section className="py-24 bg-gradient-to-b from-gray-50 to-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
                        <Badge className="mb-4 bg-purple-50 text-purple-600 border-purple-200">Our Values</Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">What We <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">Stand For</span></h2>
                        <p className="text-gray-600 max-w-2xl mx-auto">The principles that guide everything we build and every decision we make.</p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
                        {values.map((value, i) => (
                            <motion.div key={value.title} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className={`${value.bg} rounded-3xl p-8 hover:shadow-xl transition-all duration-300 group`}>
                                <div className="flex items-start gap-5">
                                    <div className={`w-14 h-14 ${value.iconBg} rounded-2xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform shadow-lg`}>
                                        <value.icon className="w-7 h-7 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-gray-900 mb-2">{value.title}</h3>
                                        <p className="text-gray-600 leading-relaxed">{value.description}</p>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Our Journey Timeline Section */}
            <section className="py-24 bg-gray-900 text-white relative overflow-hidden">
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500 rounded-full blur-3xl" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500 rounded-full blur-3xl" />
                </div>

                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
                        <Badge className="mb-4 bg-white/10 text-white border-white/20">
                            <Rocket className="w-3 h-3 mr-1" />
                            Our Journey
                        </Badge>
                        <h2 className="text-3xl sm:text-4xl font-bold mb-4">From <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">Idea to Impact</span></h2>
                        <p className="text-gray-400 max-w-2xl mx-auto">Key milestones in our mission to empower YouTube creators worldwide.</p>
                    </motion.div>

                    <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto">
                        {[
                            { year: "2022", title: "Founded", description: "Started with a simple idea to help creators automate their channels", icon: Sparkles },
                            { year: "2023", title: "1K Users", description: "Reached our first thousand creators and launched 24/7 streaming", icon: Users },
                            { year: "2024", title: "10K Users", description: "Expanded globally with support for 150+ countries", icon: Globe },
                            { year: "2025", title: "AI Launch", description: "Introduced AI-powered features for smarter automation", icon: Zap }
                        ].map((milestone, i) => (
                            <motion.div key={milestone.year} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="relative group">
                                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 h-full">
                                    <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                        <milestone.icon className="w-6 h-6 text-white" />
                                    </div>
                                    <div className="text-2xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent mb-1">{milestone.year}</div>
                                    <h3 className="text-lg font-semibold text-white mb-2">{milestone.title}</h3>
                                    <p className="text-gray-400 text-sm">{milestone.description}</p>
                                </div>
                                {i < 3 && (
                                    <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gradient-to-r from-red-500 to-orange-500" />
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center max-w-3xl mx-auto">
                        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">Ready to Join <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">Our Community?</span></h2>
                        <p className="text-lg text-gray-600 mb-10">Start automating your YouTube channels today and join thousands of creators who are growing smarter.</p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link href="/register"><Button size="lg" className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white shadow-lg">Get Started Free <ArrowRight className="ml-2 h-5 w-5" /></Button></Link>
                            <Link href="/contact"><Button size="lg" variant="outline">Contact Us</Button></Link>
                        </div>
                    </motion.div>
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
                            <div className="flex items-center gap-3">
                                <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-gradient-to-r hover:from-red-500 hover:to-orange-500 rounded-lg flex items-center justify-center transition-all duration-300 group">
                                    <Youtube className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
                                </a>
                            </div>
                        </div>
                        <div>
                            <h4 className="font-semibold text-white mb-5 flex items-center gap-2"><div className="w-1 h-4 bg-gradient-to-b from-red-500 to-orange-500 rounded-full" />Product</h4>
                            <ul className="space-y-3">
                                <li><Link href="/#features" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Features</Link></li>
                                <li><Link href="/#pricing" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />Pricing</Link></li>
                                <li><Link href="/#how-it-works" className="text-gray-400 hover:text-white transition-colors flex items-center gap-2 group"><ArrowRight className="w-3 h-3 opacity-0 -ml-5 group-hover:opacity-100 group-hover:ml-0 transition-all" />How It Works</Link></li>
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
