"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Shield } from "lucide-react"

export default function PrivacyPolicyPage() {
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
                        <Shield className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold">Privacy Policy</h1>
                        <p className="text-muted-foreground">Last updated: January 5, 2026</p>
                    </div>
                </div>

                <div className="prose prose-slate dark:prose-invert max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">1. Introduction</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            YouTube Automation Platform ("we", "our", or "us") is committed to protecting your privacy.
                            This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">2. Information We Collect</h2>

                        <h3 className="text-lg font-medium mt-4">2.1 Personal Information</h3>
                        <p className="text-muted-foreground leading-relaxed">We may collect:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Name and email address</li>
                            <li>Account credentials</li>
                            <li>Payment information (processed securely via third-party providers)</li>
                            <li>Profile information</li>
                        </ul>

                        <h3 className="text-lg font-medium mt-4">2.2 YouTube Account Data</h3>
                        <p className="text-muted-foreground leading-relaxed">When you connect your YouTube account, we access:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Channel information and statistics</li>
                            <li>Video metadata and analytics</li>
                            <li>Live stream data</li>
                            <li>Comments and engagement metrics</li>
                        </ul>

                        <h3 className="text-lg font-medium mt-4">2.3 Usage Data</h3>
                        <p className="text-muted-foreground leading-relaxed">We automatically collect:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>IP address and browser type</li>
                            <li>Device information</li>
                            <li>Pages visited and features used</li>
                            <li>Time and date of access</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">3. How We Use Your Information</h2>
                        <p className="text-muted-foreground leading-relaxed">We use collected information to:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Provide and maintain our Service</li>
                            <li>Process transactions and send related information</li>
                            <li>Send administrative information and updates</li>
                            <li>Respond to inquiries and offer support</li>
                            <li>Monitor and analyze usage patterns</li>
                            <li>Improve our Service and develop new features</li>
                            <li>Detect and prevent fraud or abuse</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">4. YouTube API Services</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Our Service uses YouTube API Services. Your use of YouTube data through our Service is also governed by:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>
                                <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                    Google Privacy Policy
                                </a>
                            </li>
                            <li>
                                <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                    YouTube Terms of Service
                                </a>
                            </li>
                        </ul>
                        <p className="text-muted-foreground leading-relaxed mt-4">
                            You can revoke our access to your YouTube data at any time through your
                            <a href="https://security.google.com/settings/security/permissions" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline mx-1">
                                Google Security Settings
                            </a>.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">5. Data Sharing and Disclosure</h2>
                        <p className="text-muted-foreground leading-relaxed">We may share your information with:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li><strong>Service Providers:</strong> Third parties that help us operate our Service (payment processors, hosting providers)</li>
                            <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
                            <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                        </ul>
                        <p className="text-muted-foreground leading-relaxed mt-4">
                            <strong>We do not sell your personal information to third parties.</strong>
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">6. Data Security</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We implement appropriate security measures to protect your information, including:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Encryption of data in transit and at rest</li>
                            <li>Regular security assessments</li>
                            <li>Access controls and authentication</li>
                            <li>Secure data storage practices</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">7. Data Retention</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We retain your information for as long as your account is active or as needed to provide services.
                            After account deletion, we may retain certain information for legal compliance or legitimate business purposes
                            for up to 30 days.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">8. Your Rights</h2>
                        <p className="text-muted-foreground leading-relaxed">You have the right to:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li><strong>Access:</strong> Request a copy of your personal data</li>
                            <li><strong>Correction:</strong> Request correction of inaccurate data</li>
                            <li><strong>Deletion:</strong> Request deletion of your data</li>
                            <li><strong>Portability:</strong> Request transfer of your data</li>
                            <li><strong>Objection:</strong> Object to certain processing of your data</li>
                            <li><strong>Withdraw Consent:</strong> Withdraw consent at any time</li>
                        </ul>
                        <p className="text-muted-foreground leading-relaxed mt-4">
                            To exercise these rights, contact us at
                            <a href="mailto:privacy@youtubeautomation.com" className="text-primary hover:underline mx-1">
                                privacy@youtubeautomation.com
                            </a>.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">9. Cookies and Tracking</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We use cookies and similar technologies to:
                        </p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                            <li>Maintain your session and preferences</li>
                            <li>Analyze usage patterns</li>
                            <li>Improve user experience</li>
                        </ul>
                        <p className="text-muted-foreground leading-relaxed mt-4">
                            You can control cookies through your browser settings.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">10. Children's Privacy</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Our Service is not intended for children under 13. We do not knowingly collect personal information
                            from children under 13. If you believe we have collected such information, please contact us immediately.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">11. International Data Transfers</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Your information may be transferred to and processed in countries other than your own.
                            We ensure appropriate safeguards are in place for such transfers.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">12. Changes to This Policy</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We may update this Privacy Policy from time to time. We will notify you of any changes by posting
                            the new Privacy Policy on this page and updating the "Last updated" date.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold border-b pb-2">13. Contact Us</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            If you have questions about this Privacy Policy, please contact us:
                        </p>
                        <ul className="list-none text-muted-foreground space-y-2 mt-2">
                            <li>Email: <a href="mailto:privacy@youtubeautomation.com" className="text-primary hover:underline">privacy@youtubeautomation.com</a></li>
                        </ul>
                    </section>
                </div>

                <div className="mt-12 pt-8 border-t flex justify-between items-center">
                    <Link href="/terms" className="text-primary hover:underline">
                        ← View Terms of Service
                    </Link>
                    <Button asChild>
                        <Link href="/register">Back to Registration</Link>
                    </Button>
                </div>
            </main>
        </div>
    )
}
