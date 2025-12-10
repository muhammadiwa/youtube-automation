"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { XCircle, ArrowLeft, RefreshCw, HelpCircle, Loader2 } from "lucide-react"

function FailedContent() {
    const searchParams = useSearchParams()
    const errorMessage = searchParams.get("error") || "Your payment could not be processed"
    const paymentId = searchParams.get("payment_id")

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Billing", href: "/dashboard/billing" },
                { label: "Payment Failed" },
            ]}
        >
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="border-0 shadow-xl max-w-md w-full">
                    <CardContent className="p-8 text-center">
                        <div className="flex justify-center mb-6">
                            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-500/10">
                                <XCircle className="h-10 w-10 text-red-500" />
                            </div>
                        </div>
                        <h1 className="text-2xl font-bold mb-2">Payment Failed</h1>
                        <p className="text-muted-foreground mb-6">
                            {errorMessage}. Please try again or use a different payment method.
                        </p>
                        <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 mb-6">
                            <div className="flex items-start gap-3 text-left">
                                <HelpCircle className="h-5 w-5 text-amber-500 mt-0.5" />
                                <div className="text-sm">
                                    <p className="font-medium text-amber-600 dark:text-amber-400">
                                        Common reasons for failure:
                                    </p>
                                    <ul className="mt-1 text-muted-foreground space-y-1">
                                        <li>• Insufficient funds</li>
                                        <li>• Card declined by bank</li>
                                        <li>• Incorrect card details</li>
                                        <li>• Network connectivity issues</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-3">
                            {paymentId ? (
                                <Link href={`/dashboard/billing/checkout?retry=${paymentId}`}>
                                    <Button className="w-full">
                                        <RefreshCw className="h-4 w-4 mr-2" />
                                        Try Different Payment Method
                                    </Button>
                                </Link>
                            ) : (
                                <Link href="/dashboard/billing">
                                    <Button className="w-full">
                                        <RefreshCw className="h-4 w-4 mr-2" />
                                        Try Again
                                    </Button>
                                </Link>
                            )}
                            <Link href="/dashboard/billing">
                                <Button variant="outline" className="w-full">
                                    <ArrowLeft className="h-4 w-4 mr-2" />
                                    Back to Billing
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}

export default function CheckoutFailedPage() {
    return (
        <Suspense fallback={
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Payment Failed" },
                ]}
            >
                <div className="flex items-center justify-center min-h-[60vh]">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardLayout>
        }>
            <FailedContent />
        </Suspense>
    )
}
