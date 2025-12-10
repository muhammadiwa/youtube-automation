"use client"

import Link from "next/link"
import {
    CreditCard,
    ChevronRight,
    Shield,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"

const adminLinks = [
    {
        title: "Payment Gateways",
        description: "Configure and manage payment gateway integrations",
        href: "/admin/payment-gateways",
        icon: CreditCard,
    },
]

export default function AdminPage() {
    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Admin" }]}
        >
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Shield className="h-8 w-8" />
                        Admin Panel
                    </h1>
                    <p className="text-muted-foreground">
                        System administration and configuration
                    </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {adminLinks.map((link) => (
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
            </div>
        </DashboardLayout>
    )
}
