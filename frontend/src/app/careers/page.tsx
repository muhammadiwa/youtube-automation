"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
    ArrowRight,
    Video,
    MapPin,
    Briefcase,
    Clock,
    Heart,
    Coffee,
    Laptop,
    Globe,
    // eslint-disable-next-line @typescript-eslint/no-deprecated
    Youtube
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LegalLink } from "@/components/legal-modal"

// Benefits data
const benefits = [
    { icon: Heart, title: "Health Insurance", description: "Comprehensive health, dental, and vision coverage." },
    { icon: Coffee, title: "Unlimited PTO", description: "Take the time you need to recharge." },
    { icon: Laptop, title: "Remote First", description: "Work from anywhere in the world." },
    { icon: Globe, title: "Learning Budget", description: "$2,000 annual budget for courses and conferences." },
]

// Jobs data
const jobs = [
    { id: 1, title: "Senior Frontend Engineer", department: "Engineering", location: "Remote", type: "Full-time" },
    { id: 2, title: "Backend Engineer", department: "Engineering", location: "Remote", type: "Full-time" },
    { id: 3, title: "Product Designer", department: "Design", location: "Remote", type: "Full-time" },
    { id: 4, title: "DevOps Engineer", department: "Engineering", location: "Remote", type: "Full-time" },
    { id: 5, title: "Customer Success Manager", department: "Support", location: "Remote", type: "Full-time" },
    { id: 6, title: "Content Marketing Manager", department: "Marketing", location: "Remote", type: "Full-time" },
]

export default function CareersPage() {
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
                <div className="absolute inset-0 bg-gradient-to-br from-green-50 via-emerald-50 to-white" />
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-3xl mx-auto">
                        <Badge className="mb-4 bg-green-50 text-green-600 border-green-200">We're Hiring</Badge>
                        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
                            Join Our <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">Mission</span>
                        </h1>
                        <p className="text-xl text-gray-600 mb-8">Help us empower YouTube creators worldwide. We're looking for passionate people to join our team.</p>
                        <Button size="lg" className="bg-gradient-to-r from-green-500 to-emerald-500 text-white">
                            View Open Positions <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                    </motion.div>
                </div>
            </section>

            {/* Stats */}
            <section className="py-16 bg-white border-y border-gray-100">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                        <div><div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">50+</div><div className="text-sm text-gray-600 mt-1">Team Members</div></div>
                        <div><div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">15+</div><div className="text-sm text-gray-600 mt-1">Countries</div></div>
                        <div><div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">100%</div><div className="text-sm text-gray-600 mt-1">Remote</div></div>
                        <div><div className="text-3xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">4.9</div><div className="text-sm text-gray-600 mt-1">Glassdoor Rating</div></div>
                    </div>
                </div>
            </section>

            {/* Benefits */}
            <section className="py-24">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-gray-900 mb-4">Why Work With Us</h2>
                        <p className="text-gray-600 max-w-2xl mx-auto">We offer competitive benefits to help you do your best work.</p>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {benefits.map((benefit, i) => (
                            <motion.div key={benefit.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="bg-white rounded-2xl p-6 shadow-lg text-center">
                                <div className="w-14 h-14 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                                    <benefit.icon className="w-7 h-7 text-green-500" />
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{benefit.title}</h3>
                                <p className="text-gray-600 text-sm">{benefit.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Open Positions */}
            <section className="py-24 bg-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-gray-900 mb-4">Open Positions</h2>
                        <p className="text-gray-600 max-w-2xl mx-auto">Find your next opportunity with us.</p>
                    </div>
                    <div className="max-w-3xl mx-auto space-y-4">
                        {jobs.map((job, i) => (
                            <motion.div key={job.id} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="bg-gray-50 rounded-xl p-6 hover:bg-gray-100 transition-colors cursor-pointer group">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">{job.title}</h3>
                                        <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-500">
                                            <span className="flex items-center gap-1"><Briefcase className="w-4 h-4" />{job.department}</span>
                                            <span className="flex items-center gap-1"><MapPin className="w-4 h-4" />{job.location}</span>
                                            <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{job.type}</span>
                                        </div>
                                    </div>
                                    <Button variant="outline" className="group-hover:bg-green-500 group-hover:text-white group-hover:border-green-500 transition-all">
                                        Apply <ArrowRight className="ml-2 w-4 h-4" />
                                    </Button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-24 bg-gradient-to-br from-green-500 to-emerald-500">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">Don't See Your Role?</h2>
                    <p className="text-white/90 mb-8 max-w-2xl mx-auto">We're always looking for talented people. Send us your resume and we'll keep you in mind for future opportunities.</p>
                    <Button size="lg" className="bg-white text-green-600 hover:bg-gray-100">
                        Send Your Resume <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
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
