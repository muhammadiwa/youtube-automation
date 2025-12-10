"use client"

import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle2, ArrowRight, Sparkles } from "lucide-react"

export default function CheckoutSuccessPage() {
    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Billing", href: "/dashboard/billing" },
                { label: "Success" },
            ]}
        >
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="border-0 shadow-xl max-w-md w-full">
                    <CardContent className="p-8 text-center">
                        <div className="flex justify-center mb-6">
                            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-green-500/10 animate-pulse">
                                <CheckCircle2 className="h-10 w-10 text-green-500" />
                            </div>
                        </div>
                        <h1 className="text-2xl font-bold mb-2">Payment Successful!</h1>
                        <p className="text-muted-foreground mb-6">
                            Thank you for your purchase. Your subscription has been activated and you now have access to all premium features.
                        </p>
                        <div className="p-4 rounded-lg bg-primary/5 border border-primary/10 mb-6">
                            <div className="flex items-center justify-center gap-2 text-primary">
                                <Sparkles className="h-5 w-5" />
                                <span className="font-medium">Premium features unlocked!</span>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <Link href="/dashboard">
                                <Button className="w-full">
                                    Go to Dashboard
                                    <ArrowRight className="h-4 w-4 ml-2" />
                                </Button>
                            </Link>
                            <Link href="/dashboard/billing">
                                <Button variant="outline" className="w-full">
                                    View Subscription
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
