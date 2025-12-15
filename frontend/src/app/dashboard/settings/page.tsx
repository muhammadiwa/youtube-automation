"use client"

import { useState } from "react"
import Link from "next/link"
import {
    User,
    Bell,
    Key,
    Webhook,
    ChevronRight,
    Settings,
    FileText,
    Shield,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { LegalModal } from "@/components/legal-modal"

const settingsLinks = [
    {
        title: "Profile",
        description: "Manage your account information, password, and 2FA settings",
        href: "/dashboard/settings/profile",
        icon: User,
    },
    {
        title: "Notifications",
        description: "Configure notification channels and event preferences",
        href: "/dashboard/settings/notifications",
        icon: Bell,
    },
    {
        title: "API Keys",
        description: "Create and manage API keys for external integrations",
        href: "/dashboard/settings/api-keys",
        icon: Key,
    },
    {
        title: "Webhooks",
        description: "Configure webhook endpoints for real-time event notifications",
        href: "/dashboard/settings/webhooks",
        icon: Webhook,
    },
]

type LegalModalType = "terms" | "privacy" | null

const legalItems = [
    {
        title: "Terms of Service",
        description: "Read our terms and conditions for using the platform",
        type: "terms" as const,
        icon: FileText,
    },
    {
        title: "Privacy Policy",
        description: "Learn how we collect, use, and protect your data",
        type: "privacy" as const,
        icon: Shield,
    },
]

export default function SettingsPage() {
    const [legalModal, setLegalModal] = useState<LegalModalType>(null)

    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings" }]}
        >
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Settings className="h-8 w-8" />
                        Settings
                    </h1>
                    <p className="text-muted-foreground">
                        Manage your account and application preferences
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    {settingsLinks.map((link) => (
                        <Link key={link.href} href={link.href}>
                            <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group h-full">
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
                                            <link.icon className="h-6 w-6 text-primary" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <h3 className="font-semibold group-hover:text-primary transition-colors">
                                                    {link.title}
                                                </h3>
                                                <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {link.description}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>

                {/* Legal Section */}
                <div className="pt-6 border-t">
                    <h2 className="text-lg font-semibold mb-4">Legal</h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        {legalItems.map((item) => (
                            <Card
                                key={item.type}
                                onClick={() => setLegalModal(item.type)}
                                className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group h-full bg-slate-50 dark:bg-slate-900/50"
                            >
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-200 dark:bg-slate-800 group-hover:bg-slate-300 dark:group-hover:bg-slate-700 transition-colors">
                                            <item.icon className="h-6 w-6 text-slate-600 dark:text-slate-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <h3 className="font-semibold group-hover:text-primary transition-colors">
                                                    {item.title}
                                                </h3>
                                                <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {item.description}
                                            </p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </div>

            {/* Legal Modal */}
            {legalModal && (
                <LegalModal type={legalModal} onClose={() => setLegalModal(null)} />
            )}
        </DashboardLayout>
    )
}
