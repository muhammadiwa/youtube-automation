"use client"

import { useState } from "react"
import Link from "next/link"
import {
    Book,
    Key,
    Webhook,
    Video,
    Radio,
    Users,
    BarChart3,
    CreditCard,
    Shield,
    Code,
    Zap,
    ChevronRight,
    ExternalLink,
    Copy,
    Check,
    Search,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const docCategories = [
    {
        title: "Getting Started",
        description: "Panduan dasar untuk memulai menggunakan platform",
        icon: Book,
        color: "bg-blue-500",
        href: "/dashboard/docs/getting-started",
        articles: [
            { title: "Pengenalan Platform", href: "/dashboard/docs/getting-started#intro" },
            { title: "Menghubungkan Akun YouTube", href: "/dashboard/docs/getting-started#connect" },
            { title: "Upload Video Pertama", href: "/dashboard/docs/getting-started#upload" },
        ]
    },
    {
        title: "API Integration",
        description: "Dokumentasi lengkap untuk integrasi API",
        icon: Code,
        color: "bg-purple-500",
        href: "/dashboard/docs/api",
        articles: [
            { title: "Authentication", href: "/dashboard/docs/api#auth" },
            { title: "API Keys", href: "/dashboard/docs/api#api-keys" },
            { title: "Rate Limiting", href: "/dashboard/docs/api#rate-limit" },
            { title: "Endpoints Reference", href: "/dashboard/docs/api#endpoints" },
        ]
    },
    {
        title: "Webhooks",
        description: "Setup dan konfigurasi webhooks",
        icon: Webhook,
        color: "bg-green-500",
        href: "/dashboard/docs/webhooks",
        articles: [
            { title: "Membuat Webhook", href: "/dashboard/docs/webhooks#create" },
            { title: "Event Types", href: "/dashboard/docs/webhooks#events" },
            { title: "Signature Verification", href: "/dashboard/docs/webhooks#signature" },
            { title: "Retry Policy", href: "/dashboard/docs/webhooks#retry" },
        ]
    },
    {
        title: "Video Management",
        description: "Panduan upload dan kelola video",
        icon: Video,
        color: "bg-red-500",
        href: "/dashboard/docs/videos",
        articles: [
            { title: "Upload Video", href: "/dashboard/docs/videos#upload" },
            { title: "Bulk Upload", href: "/dashboard/docs/videos#bulk" },
            { title: "Scheduling", href: "/dashboard/docs/videos#schedule" },
            { title: "Video Library", href: "/dashboard/docs/videos#library" },
        ]
    },
    {
        title: "Live Streaming",
        description: "Panduan live streaming ke YouTube",
        icon: Radio,
        color: "bg-orange-500",
        href: "/dashboard/docs/streaming",
        articles: [
            { title: "Setup Stream", href: "/dashboard/docs/streaming#setup" },
            { title: "Multi-destination", href: "/dashboard/docs/streaming#multi" },
            { title: "Stream Monitoring", href: "/dashboard/docs/streaming#monitor" },
        ]
    },
    {
        title: "Account Management",
        description: "Kelola multiple akun YouTube",
        icon: Users,
        color: "bg-cyan-500",
        href: "/dashboard/docs/accounts",
        articles: [
            { title: "Connect Account", href: "/dashboard/docs/accounts#connect" },
            { title: "Token Refresh", href: "/dashboard/docs/accounts#token" },
            { title: "Quota Management", href: "/dashboard/docs/accounts#quota" },
        ]
    },
    {
        title: "Analytics",
        description: "Memahami data analytics",
        icon: BarChart3,
        color: "bg-indigo-500",
        href: "/dashboard/docs/analytics",
        articles: [
            { title: "Dashboard Overview", href: "/dashboard/docs/analytics#overview" },
            { title: "Video Analytics", href: "/dashboard/docs/analytics#video" },
            { title: "Revenue Reports", href: "/dashboard/docs/analytics#revenue" },
        ]
    },
    {
        title: "Billing & Plans",
        description: "Informasi billing dan subscription",
        icon: CreditCard,
        color: "bg-pink-500",
        href: "/dashboard/docs/billing",
        articles: [
            { title: "Plans & Pricing", href: "/dashboard/docs/billing#plans" },
            { title: "Usage Limits", href: "/dashboard/docs/billing#limits" },
            { title: "Payment Methods", href: "/dashboard/docs/billing#payment" },
        ]
    },
]

const quickLinks = [
    { title: "API Reference", href: "/docs", icon: Code, external: true },
    { title: "Swagger UI", href: "/docs", icon: Zap, external: true },
    { title: "Status Page", href: "/status", icon: Shield, external: true },
]

export default function DocsPage() {
    const [searchQuery, setSearchQuery] = useState("")
    const [copiedCode, setCopiedCode] = useState<string | null>(null)

    const copyToClipboard = async (code: string, id: string) => {
        await navigator.clipboard.writeText(code)
        setCopiedCode(id)
        setTimeout(() => setCopiedCode(null), 2000)
    }

    const filteredCategories = docCategories.filter(cat =>
        cat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cat.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        cat.articles.some(a => a.title.toLowerCase().includes(searchQuery.toLowerCase()))
    )

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Documentation" },
            ]}
        >
            <div className="space-y-8">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto">
                    <div className="flex justify-center mb-4">
                        <div className="p-3 rounded-2xl bg-gradient-to-br from-red-500 to-orange-500">
                            <Book className="h-8 w-8 text-white" />
                        </div>
                    </div>
                    <h1 className="text-4xl font-bold mb-4">Documentation</h1>
                    <p className="text-lg text-muted-foreground mb-6">
                        Panduan lengkap untuk menggunakan YT Automation platform.
                        Temukan cara mengintegrasikan API, setup webhooks, dan kelola channel YouTube Anda.
                    </p>

                    {/* Search */}
                    <div className="relative max-w-md mx-auto">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Cari dokumentasi..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                </div>

                {/* Quick Start */}
                <Card className="border-0 shadow-lg bg-gradient-to-r from-red-500/10 via-orange-500/10 to-yellow-500/10">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-orange-500" />
                            Quick Start
                        </CardTitle>
                        <CardDescription>
                            Mulai integrasi dalam hitungan menit
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-3 gap-4">
                            <div className="p-4 rounded-lg bg-background/80 border">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-sm font-bold">1</div>
                                    <span className="font-medium">Buat API Key</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Buka Settings → API Keys → Create
                                </p>
                            </div>
                            <div className="p-4 rounded-lg bg-background/80 border">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm font-bold">2</div>
                                    <span className="font-medium">Test API</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Gunakan API key di header X-API-Key
                                </p>
                            </div>
                            <div className="p-4 rounded-lg bg-background/80 border">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-6 h-6 rounded-full bg-yellow-500 text-white flex items-center justify-center text-sm font-bold">3</div>
                                    <span className="font-medium">Setup Webhook</span>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Terima notifikasi real-time
                                </p>
                            </div>
                        </div>

                        {/* Code Example */}
                        <div className="mt-6">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium">Contoh Request</span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => copyToClipboard(
                                        `curl -X GET "${API_BASE_URL}/videos" \\
  -H "X-API-Key: your_api_key_here"`,
                                        "quick-start"
                                    )}
                                >
                                    {copiedCode === "quick-start" ? (
                                        <Check className="h-4 w-4 text-green-500" />
                                    ) : (
                                        <Copy className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                            <pre className="p-4 rounded-lg bg-slate-900 text-slate-100 text-sm overflow-x-auto">
                                <code>{`curl -X GET "${API_BASE_URL}/videos" \\
  -H "X-API-Key: your_api_key_here"`}</code>
                            </pre>
                        </div>
                    </CardContent>
                </Card>

                {/* Documentation Categories */}
                <div>
                    <h2 className="text-2xl font-bold mb-6">Dokumentasi</h2>
                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {filteredCategories.map((category) => (
                            <Link key={category.title} href={category.href}>
                                <Card className="h-full hover:shadow-lg transition-all hover:-translate-y-1 cursor-pointer group">
                                    <CardHeader className="pb-3">
                                        <div className={`w-10 h-10 rounded-lg ${category.color} flex items-center justify-center mb-3`}>
                                            <category.icon className="h-5 w-5 text-white" />
                                        </div>
                                        <CardTitle className="text-lg group-hover:text-primary transition-colors">
                                            {category.title}
                                        </CardTitle>
                                        <CardDescription className="text-sm">
                                            {category.description}
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="pt-0">
                                        <ul className="space-y-1">
                                            {category.articles.slice(0, 3).map((article) => (
                                                <li key={article.title} className="text-sm text-muted-foreground flex items-center gap-1">
                                                    <ChevronRight className="h-3 w-3" />
                                                    {article.title}
                                                </li>
                                            ))}
                                        </ul>
                                    </CardContent>
                                </Card>
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Quick Links */}
                <div>
                    <h2 className="text-2xl font-bold mb-6">Quick Links</h2>
                    <div className="grid md:grid-cols-3 gap-4">
                        <Link href="/dashboard/settings/api-keys">
                            <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                <CardContent className="p-4 flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/10">
                                        <Key className="h-5 w-5 text-purple-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium">Manage API Keys</p>
                                        <p className="text-sm text-muted-foreground">Buat dan kelola API keys</p>
                                    </div>
                                    <ChevronRight className="h-4 w-4 ml-auto text-muted-foreground" />
                                </CardContent>
                            </Card>
                        </Link>
                        <Link href="/dashboard/settings/webhooks">
                            <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                <CardContent className="p-4 flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-500/10">
                                        <Webhook className="h-5 w-5 text-green-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium">Configure Webhooks</p>
                                        <p className="text-sm text-muted-foreground">Setup webhook endpoints</p>
                                    </div>
                                    <ChevronRight className="h-4 w-4 ml-auto text-muted-foreground" />
                                </CardContent>
                            </Card>
                        </Link>
                        <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noopener noreferrer">
                            <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                <CardContent className="p-4 flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/10">
                                        <Code className="h-5 w-5 text-blue-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium">API Reference</p>
                                        <p className="text-sm text-muted-foreground">Swagger UI documentation</p>
                                    </div>
                                    <ExternalLink className="h-4 w-4 ml-auto text-muted-foreground" />
                                </CardContent>
                            </Card>
                        </a>
                    </div>
                </div>

                {/* Support */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="p-6">
                        <div className="flex flex-col md:flex-row items-center gap-6">
                            <div className="p-4 rounded-2xl bg-gradient-to-br from-red-500/10 to-orange-500/10">
                                <Shield className="h-12 w-12 text-red-500" />
                            </div>
                            <div className="flex-1 text-center md:text-left">
                                <h3 className="text-xl font-bold mb-2">Butuh Bantuan?</h3>
                                <p className="text-muted-foreground">
                                    Tim support kami siap membantu Anda. Buat tiket support atau hubungi kami langsung.
                                </p>
                            </div>
                            <div className="flex gap-3">
                                <Link href="/dashboard/support/create">
                                    <Button>Buat Tiket Support</Button>
                                </Link>
                                <Link href="/dashboard/support">
                                    <Button variant="outline">Lihat FAQ</Button>
                                </Link>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
