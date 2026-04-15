"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft, FileText } from "lucide-react"

export default function TermsOfServicePage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
            {/* Header */}
            <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
                <div className="container flex h-16 items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 font-bold text-xl">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center">
                            <span className="text-white text-sm">YT</span>
                        </div>
                        YouTube Automation
                    </Link>
                    <Button variant="ghost" asChild>
                        <Link href="/">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Home
                        </Link>
                    </Button>
                </div>
            </header>

            {/* Content */}
            <main className="container max-w-4xl py-12">
                <div className="flex items-center gap-3 mb-8">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                        <FileText className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">Terms of Service</h1>
                        <p className="text-muted-foreground">Last updated: January 5, 2026</p>
                    </div>
                </div>

                <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">1. Acceptance of Terms</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            By accessing or using YouTube Automation Platform ("Service"), you agree to be bound by these Terms of Service ("Terms").
                            If you do not agree to these Terms, please do not use our Service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">2. Description of Service</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            YouTube Automation Platform provides tools for managing YouTube channels, including but not limited to:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Video upload and scheduling</li>
                            <li>Live streaming management</li>
                            <li>Analytics and reporting</li>
                            <li>Channel moderation tools</li>
                            <li>AI-powered content optimization</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">3. User Accounts</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            To use our Service, you must create an account. You are responsible for:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Maintaining the confidentiality of your account credentials</li>
                            <li>All activities that occur under your account</li>
                            <li>Notifying us immediately of any unauthorized use</li>
                            <li>Ensuring your account information is accurate and up-to-date</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">4. YouTube API Services</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Our Service uses YouTube API Services. By using our Service, you also agree to be bound by the
                            <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline mx-1">
                                YouTube Terms of Service
                            </a>
                            and
                            <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline mx-1">
                                Google Privacy Policy
                            </a>.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">5. Acceptable Use</h2>
                        <p className="text-muted-foreground leading-relaxed">You agree not to:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Violate any applicable laws or regulations</li>
                            <li>Infringe on intellectual property rights</li>
                            <li>Upload or distribute malicious content</li>
                            <li>Attempt to gain unauthorized access to our systems</li>
                            <li>Use the Service to spam or harass others</li>
                            <li>Violate YouTube's Community Guidelines</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">6. Subscription and Payments</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Some features require a paid subscription. By subscribing, you agree to:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Pay all applicable fees as described in your chosen plan</li>
                            <li>Automatic renewal unless cancelled before the renewal date</li>
                            <li>No refunds for partial subscription periods</li>
                            <li>Price changes with 30 days advance notice</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">7. Intellectual Property</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            The Service and its original content, features, and functionality are owned by YouTube Automation Platform
                            and are protected by international copyright, trademark, and other intellectual property laws.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">8. Limitation of Liability</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            To the maximum extent permitted by law, YouTube Automation Platform shall not be liable for any indirect,
                            incidental, special, consequential, or punitive damages, including loss of profits, data, or other intangible losses.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">9. Termination</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We may terminate or suspend your account immediately, without prior notice, for any breach of these Terms.
                            Upon termination, your right to use the Service will cease immediately.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">10. Changes to Terms</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We reserve the right to modify these Terms at any time. We will notify users of any material changes
                            via email or through the Service. Continued use after changes constitutes acceptance of the new Terms.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">11. Contact Us</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            If you have any questions about these Terms, please contact us at:
                        </p>
                        <p className="text-muted-foreground">
                            Email: <a href="mailto:legal@youtubeautomation.com" className="text-primary hover:underline">legal@youtubeautomation.com</a>
                        </p>
                    </section>
                </div>

                <div className="mt-12 pt-8 border-t flex justify-between items-center">
                    <Link href="/privacy" className="text-primary hover:underline">
                        View Privacy Policy →
                    </Link>
                    <Button asChild>
                        <Link href="/register">Back to Registration</Link>
                    </Button>
                </div>
            </main>
        </div>
    )
}
