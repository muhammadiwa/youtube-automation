"use client"

import { Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { XCircle, ArrowLeft, RefreshCw, Loader2, HelpCircle } from "lucide-react"

function FailedContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const plan = searchParams.get("plan")
    const reason = searchParams.get("reason")

    const getErrorMessage = () => {
        switch (reason) {
            case "cancelled":
                return "You cancelled the payment process."
            case "declined":
                return "Your payment was declined. Please try a different payment method."
            case "expired":
                return "The payment session has expired. Please try again."
            default:
                return "The payment could not be completed. Please try again or use a different payment method."
        }
    }

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
                            {getErrorMessage()}
                        </p>
                        <div className="space-y-3">
                            {plan && (
                                <Link href={`/dashboard/billing/checkout?plan=${plan}`}>
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
                            <Link href="/support">
                                <Button variant="ghost" className="w-full text-muted-foreground">
                                    <HelpCircle className="h-4 w-4 mr-2" />
                                    Contact Support
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
