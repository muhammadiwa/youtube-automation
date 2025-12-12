"use client"

import Link from "next/link"
import {
    Users,
    CreditCard,
    Shield,
    ChevronRight,
    BarChart3,
    Server,
    FileText,
    Settings,
    MessageSquare,
    Zap,
    Database,
    Bell,
    Flag,
    TrendingUp,
    Activity,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent } from "@/components/ui/card"

const adminLinks = [
    {
        title: "Users",
        description: "Manage platform users, suspensions, and impersonation",
        href: "/admin/users",
        icon: Users,
    },
    {
        title: "Subscriptions",
        description: "Manage subscriptions, upgrades, and refunds",
        href: "/admin/subscriptions",
        icon: CreditCard,
    },
    {
        title: "Moderation",
        description: "Review reported content and manage warnings",
        href: "/admin/moderation",
        icon: Shield,
    },
    {
        title: "Support Tickets",
        description: "Handle support requests and user communications",
        href: "/admin/support",
        icon: MessageSquare,
    },
    {
        title: "System Health",
        description: "Monitor system components and job queues",
        href: "/admin/system",
        icon: Server,
    },
    {
        title: "Quota Management",
        description: "Monitor YouTube API quota usage",
        href: "/admin/quota",
        icon: Zap,
    },
    {
        title: "Payment Gateways",
        description: "Configure and manage payment gateway integrations",
        href: "/admin/payment-gateways",
        icon: CreditCard,
    },
    {
        title: "AI Services",
        description: "Monitor AI usage, costs, and configuration",
        href: "/admin/ai",
        icon: Database,
    },
    {
        title: "Audit Logs",
        description: "View all admin and system actions",
        href: "/admin/audit-logs",
        icon: FileText,
    },
    {
        title: "Security",
        description: "Monitor failed logins and security events",
        href: "/admin/security",
        icon: Shield,
    },
    {
        title: "Data Requests",
        description: "Handle export and deletion requests",
        href: "/admin/compliance",
        icon: Flag,
    },
    {
        title: "Global Config",
        description: "Configure system-wide settings",
        href: "/admin/config",
        icon: Settings,
    },
    {
        title: "Promotions",
        description: "Manage discount codes and referral programs",
        href: "/admin/promotions",
        icon: Bell,
    },
    {
        title: "Platform Analytics",
        description: "View platform-wide metrics and insights",
        href: "/admin/analytics",
        icon: BarChart3,
    },
    {
        title: "Backups",
        description: "Manage backups and disaster recovery",
        href: "/admin/backups",
        icon: Database,
    },
]

// Quick stats for dashboard overview
const quickStats = [
    { label: "Total Users", value: "-", icon: Users, color: "text-blue-500" },
    { label: "Active Streams", value: "-", icon: Activity, color: "text-green-500" },
    { label: "MRR", value: "-", icon: TrendingUp, color: "text-purple-500" },
    { label: "System Health", value: "Healthy", icon: Server, color: "text-emerald-500" },
]

export default function AdminPage() {
    return (
        <AdminLayout breadcrumbs={[{ label: "Dashboard" }]}>
            <div className="space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30">
                            <Shield className="h-5 w-5 text-white" />
                        </div>
                        Admin Dashboard
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        System administration and platform management
                    </p>
                </div>

                {/* Quick Stats */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {quickStats.map((stat) => (
                        <Card key={stat.label} className="border-0 shadow-md">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-muted ${stat.color}`}>
                                        <stat.icon className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">{stat.label}</p>
                                        <p className="text-xl font-bold">{stat.value}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Quick Links */}
                <div>
                    <h2 className="text-lg font-semibold mb-4">Quick Access</h2>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {adminLinks.map((link) => (
                            <Link key={link.href} href={link.href}>
                                <Card className="border-0 shadow-md hover:shadow-lg transition-all duration-300 cursor-pointer group h-full">
                                    <CardContent className="p-5">
                                        <div className="flex items-start gap-4">
                                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                                                <link.icon className="h-5 w-5 text-blue-500" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="font-semibold group-hover:text-blue-500 transition-colors">
                                                        {link.title}
                                                    </h3>
                                                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                                                </div>
                                                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                    {link.description}
                                                </p>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </AdminLayout>
    )
}
