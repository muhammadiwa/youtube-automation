"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
    ArrowRight,
    Video,
    Mail,
    MessageSquare,
    MapPin,
    Phone,
    Clock,
    Send,
    // eslint-disable-next-line @typescript-eslint/no-deprecated
    Youtube
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { LegalLink } from "@/components/legal-modal"

// Contact info data
const contactInfo = [
    { icon: Mail, title: "Email Us", value: "support@ytautomation.com", description: "We'll respond within 24 hours" },
    { icon: MessageSquare, title: "Live Chat", value: "Available 24/7", description: "Chat with our support team" },
    { icon: Phone, title: "Phone", value: "+1 (555) 123-4567", description: "Mon-Fri, 9am-6pm EST" },
    { icon: MapPin, title: "Office", value: "San Francisco, CA", description: "Visit us by appointment" },
]

// FAQ data
const faqs = [
    { q: "How quickly do you respond to inquiries?", a: "We typically respond within 24 hours on business days." },
    { q: "Do you offer phone support?", a: "Yes, phone support is available for Pro and Enterprise plans." },
    { q: "Can I schedule a demo?", a: "Absolutely! Fill out the form and select 'Request Demo' as the subject." },
    { q: "Where are you located?", a: "Our headquarters is in San Francisco, but we're a remote-first company." },
]

export default function ContactPage() {
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
                <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-cyan-50 to-white" />
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center max-w-3xl mx-auto">
                        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
                            Get in <span className="bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent">Touch</span>
                        </h1>
                        <p className="text-xl text-gray-600">Have questions? We'd love to hear from you. Send us a message and we'll respond as soon as possible.</p>
                    </motion.div>
                </div>
            </section>

            {/* Contact Info Cards */}
            <section className="py-16">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {contactInfo.map((info, i) => (
                            <motion.div key={info.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="bg-white rounded-2xl p-6 shadow-lg text-center hover:shadow-xl transition-shadow">
                                <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                                    <info.icon className="w-7 h-7 text-blue-500" />
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-1">{info.title}</h3>
                                <p className="text-blue-600 font-medium mb-1">{info.value}</p>
                                <p className="text-gray-500 text-sm">{info.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Contact Form & FAQ */}
            <section className="py-16 bg-white">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid lg:grid-cols-2 gap-16">
                        {/* Contact Form */}
                        <motion.div initial={{ opacity: 0, x: -30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
                            <h2 className="text-2xl font-bold text-gray-900 mb-6">Send Us a Message</h2>
                            <form className="space-y-6">
                                <div className="grid sm:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
                                        <Input placeholder="John" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
                                        <Input placeholder="Doe" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                                    <Input type="email" placeholder="john@example.com" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
                                    <Input placeholder="How can we help?" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">Message</label>
                                    <Textarea placeholder="Tell us more about your inquiry..." rows={5} />
                                </div>
                                <Button size="lg" className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600">
                                    Send Message <Send className="ml-2 w-5 h-5" />
                                </Button>
                            </form>
                        </motion.div>

                        {/* FAQ */}
                        <motion.div initial={{ opacity: 0, x: 30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
                            <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
                            <div className="space-y-4">
                                {faqs.map((faq, i) => (
                                    <div key={i} className="bg-gray-50 rounded-xl p-5">
                                        <h3 className="font-semibold text-gray-900 mb-2">{faq.q}</h3>
                                        <p className="text-gray-600 text-sm">{faq.a}</p>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-8 p-6 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl">
                                <div className="flex items-center gap-3 mb-3">
                                    <Clock className="w-6 h-6 text-blue-500" />
                                    <h3 className="font-semibold text-gray-900">Support Hours</h3>
                                </div>
                                <p className="text-gray-600 text-sm">Our support team is available Monday through Friday, 9am to 6pm EST. For urgent issues, Pro and Enterprise customers have access to 24/7 priority support.</p>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-24 bg-gradient-to-br from-blue-500 to-cyan-500">
                <div className="container mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">Ready to Get Started?</h2>
                    <p className="text-white/90 mb-8 max-w-2xl mx-auto">Join thousands of creators who are already automating their YouTube channels with YT Automation.</p>
                    <Link href="/register">
                        <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 shadow-xl">
                            Start Free Today <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                    </Link>
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
