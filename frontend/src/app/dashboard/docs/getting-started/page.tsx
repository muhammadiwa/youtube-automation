"use client"

import { useState } from "react"
import Link from "next/link"
import {
    Book,
    Youtube,
    Video,
    Radio,
    Check,
    ChevronRight,
    ArrowRight,
    Zap,
    Shield,
    Users,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const steps = [
    {
        number: 1,
        title: "Buat Akun",
        description: "Daftar dan verifikasi email Anda",
        status: "completed",
        details: [
            "Kunjungi halaman registrasi",
            "Isi form dengan email dan password",
            "Verifikasi email Anda",
            "Login ke dashboard"
        ]
    },
    {
        number: 2,
        title: "Hubungkan YouTube",
        description: "Koneksikan akun YouTube Anda",
        status: "current",
        details: [
            "Buka menu Accounts",
            "Klik 'Connect YouTube Account'",
            "Login ke Google dan berikan izin",
            "Akun akan muncul di dashboard"
        ],
        link: "/dashboard/accounts"
    },
    {
        number: 3,
        title: "Upload Video",
        description: "Upload video pertama Anda",
        status: "upcoming",
        details: [
            "Buka menu Videos",
            "Klik 'Upload Video'",
            "Pilih file dan isi metadata",
            "Video akan diupload ke YouTube"
        ],
        link: "/dashboard/videos"
    },
    {
        number: 4,
        title: "Mulai Streaming",
        description: "Setup live streaming",
        status: "upcoming",
        details: [
            "Buka menu Streams",
            "Klik 'Create Stream'",
            "Pilih akun dan konfigurasi",
            "Mulai streaming!"
        ],
        link: "/dashboard/streams"
    },
]

const features = [
    {
        icon: Users,
        title: "Multi-Account",
        description: "Kelola banyak channel YouTube dari satu dashboard"
    },
    {
        icon: Video,
        title: "Bulk Upload",
        description: "Upload banyak video sekaligus dengan CSV"
    },
    {
        icon: Radio,
        title: "Live Streaming",
        description: "Stream ke multiple platform secara bersamaan"
    },
    {
        icon: Shield,
        title: "API Integration",
        description: "Integrasikan dengan aplikasi Anda via API"
    },
]

export default function GettingStartedPage() {
    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Documentation", href: "/dashboard/docs" },
                { label: "Getting Started" },
            ]}
        >
            <div className="space-y-8 max-w-4xl">
                {/* Header */}
                <div>
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-lg bg-blue-500">
                            <Book className="h-6 w-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">Getting Started</h1>
                            <p className="text-muted-foreground">
                                Panduan langkah demi langkah untuk memulai
                            </p>
                        </div>
                    </div>
                </div>

                {/* Welcome Card */}
                <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10">
                    <CardContent className="p-6">
                        <div className="flex flex-col md:flex-row items-center gap-6">
                            <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500">
                                <Youtube className="h-12 w-12 text-white" />
                            </div>
                            <div className="flex-1 text-center md:text-left">
                                <h2 className="text-2xl font-bold mb-2">Selamat Datang di YT Automation!</h2>
                                <p className="text-muted-foreground">
                                    Platform all-in-one untuk mengelola channel YouTube Anda.
                                    Upload video, live streaming, dan analytics dalam satu tempat.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Steps */}
                <div>
                    <h2 className="text-2xl font-bold mb-6">Langkah-langkah Setup</h2>
                    <div className="space-y-4">
                        {steps.map((step, index) => (
                            <Card key={step.number} className={step.status === "current" ? "border-primary" : ""}>
                                <CardContent className="p-6">
                                    <div className="flex gap-4">
                                        <div className={`
                                            w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0
                                            ${step.status === "completed" ? "bg-green-500 text-white" :
                                                step.status === "current" ? "bg-primary text-primary-foreground" :
                                                    "bg-muted text-muted-foreground"}
                                        `}>
                                            {step.status === "completed" ? (
                                                <Check className="h-5 w-5" />
                                            ) : (
                                                <span className="font-bold">{step.number}</span>
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-semibold text-lg">{step.title}</h3>
                                                {step.status === "current" && (
                                                    <Badge>Current Step</Badge>
                                                )}
                                            </div>
                                            <p className="text-muted-foreground mb-4">{step.description}</p>
                                            <ul className="space-y-2">
                                                {step.details.map((detail, idx) => (
                                                    <li key={idx} className="flex items-center gap-2 text-sm">
                                                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                                        {detail}
                                                    </li>
                                                ))}
                                            </ul>
                                            {step.link && (
                                                <Link href={step.link}>
                                                    <Button className="mt-4" size="sm">
                                                        {step.status === "current" ? "Mulai Sekarang" : "Buka"}
                                                        <ArrowRight className="h-4 w-4 ml-2" />
                                                    </Button>
                                                </Link>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Features */}
                <div>
                    <h2 className="text-2xl font-bold mb-6">Fitur Utama</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {features.map((feature) => (
                            <Card key={feature.title}>
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className="p-2 rounded-lg bg-primary/10">
                                            <feature.icon className="h-6 w-6 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold mb-1">{feature.title}</h3>
                                            <p className="text-sm text-muted-foreground">{feature.description}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>

                {/* Next Steps */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Zap className="h-5 w-5 text-yellow-500" />
                            Langkah Selanjutnya
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid md:grid-cols-3 gap-4">
                            <Link href="/dashboard/docs/api">
                                <div className="p-4 rounded-lg border hover:bg-muted transition-colors cursor-pointer">
                                    <h4 className="font-medium mb-1">API Integration</h4>
                                    <p className="text-sm text-muted-foreground">Integrasikan dengan aplikasi Anda</p>
                                </div>
                            </Link>
                            <Link href="/dashboard/docs/webhooks">
                                <div className="p-4 rounded-lg border hover:bg-muted transition-colors cursor-pointer">
                                    <h4 className="font-medium mb-1">Setup Webhooks</h4>
                                    <p className="text-sm text-muted-foreground">Terima notifikasi real-time</p>
                                </div>
                            </Link>
                            <Link href="/dashboard/billing">
                                <div className="p-4 rounded-lg border hover:bg-muted transition-colors cursor-pointer">
                                    <h4 className="font-medium mb-1">Upgrade Plan</h4>
                                    <p className="text-sm text-muted-foreground">Dapatkan fitur lebih banyak</p>
                                </div>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
