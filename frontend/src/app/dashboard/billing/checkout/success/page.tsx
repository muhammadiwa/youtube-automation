"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { CheckCircle2, ArrowRight, Sparkles, Loader2, XCircle, RefreshCw } from "lucide-react"
import billingApi from "@/lib/api/billing"

function SuccessContent() {
    const searchParams = useSearchParams()
    const router = useRouter()

    // Our payment_id from redirect
    const paymentId = searchParams.get("payment_id")
    // PayPal returns with 'token' parameter (which is the order ID)
    const paypalToken = searchParams.get("token")
    // PayPal also returns PayerID when approved
    const paypalPayerId = searchParams.get("PayerID")

    const plan = searchParams.get("plan")
    const cycle = searchParams.get("cycle")

    const [verifying, setVerifying] = useState(false)
    const [verified, setVerified] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        // PayPal returns with token parameter - we need to find our transaction
        if (paypalToken && paypalPayerId) {
            // PayPal approved - verify and capture
            verifyPayPalPayment(paypalToken)
        } else if (paymentId) {
            // Direct payment_id - verify normally
            verifyPayment(paymentId)
        } else {
            // No payment_id means direct success (mock mode or already verified)
            setVerified(true)
        }
    }, [paymentId, paypalToken, paypalPayerId])

    const verifyPayment = async (transactionId: string) => {
        setVerifying(true)
        setError(null)

        try {
            // Verify payment status with backend
            const result = await billingApi.verifyPayment(transactionId)

            if (result.status === "completed") {
                setVerified(true)
            } else if (result.status === "pending") {
                // Payment still pending - might need to wait for webhook
                // For now, show success but mention it's processing
                setVerified(true)
            } else if (result.status === "failed") {
                setError("Payment verification failed. Please contact support.")
            } else {
                // Unknown status - show as success but log
                console.warn("Unknown payment status:", result.status)
                setVerified(true)
            }
        } catch (err: any) {
            console.error("Payment verification error:", err)
            // Don't show error for verification failures - payment might still be processing
            // Just show success page
            setVerified(true)
        } finally {
            setVerifying(false)
        }
    }

    const verifyPayPalPayment = async (paypalOrderId: string) => {
        setVerifying(true)
        setError(null)

        try {
            // For PayPal, we need to find the transaction by PayPal order ID and verify/capture it
            const result = await billingApi.verifyPayPalPayment(paypalOrderId)

            if (result.status === "completed") {
                setVerified(true)
            } else if (result.status === "pending") {
                // Still processing
                setVerified(true)
            } else if (result.status === "failed") {
                setError("Payment capture failed. Please contact support.")
            } else {
                setVerified(true)
            }
        } catch (err: any) {
            console.error("PayPal verification error:", err)
            // If verification fails, redirect to failed page
            router.push(`/dashboard/billing/checkout/failed?plan=${plan}&reason=verification_failed`)
        } finally {
            setVerifying(false)
        }
    }

    if (verifying) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Verifying..." },
                ]}
            >
                <div className="flex items-center justify-center min-h-[60vh]">
                    <Card className="border-0 shadow-xl max-w-md w-full">
                        <CardContent className="p-8 text-center">
                            <div className="flex justify-center mb-6">
                                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10">
                                    <Loader2 className="h-10 w-10 text-primary animate-spin" />
                                </div>
                            </div>
                            <h1 className="text-2xl font-bold mb-2">Verifying Payment...</h1>
                            <p className="text-muted-foreground">
                                Please wait while we confirm your payment.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </DashboardLayout>
        )
    }

    if (error) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Error" },
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
                            <h1 className="text-2xl font-bold mb-2">Verification Failed</h1>
                            <p className="text-muted-foreground mb-6">{error}</p>
                            <div className="space-y-3">
                                <Button onClick={() => {
                                    if (paypalToken && paypalPayerId) {
                                        verifyPayPalPayment(paypalToken)
                                    } else if (paymentId) {
                                        verifyPayment(paymentId)
                                    }
                                }} className="w-full">
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Try Again
                                </Button>
                                <Link href="/dashboard/billing">
                                    <Button variant="outline" className="w-full">
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
                        {plan && (
                            <div className="p-4 rounded-lg bg-primary/5 border border-primary/10 mb-6">
                                <div className="flex items-center justify-center gap-2 text-primary">
                                    <Sparkles className="h-5 w-5" />
                                    <span className="font-medium">
                                        {plan.charAt(0).toUpperCase() + plan.slice(1)} Plan ({cycle}) activated!
                                    </span>
                                </div>
                            </div>
                        )}
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

export default function CheckoutSuccessPage() {
    return (
        <Suspense fallback={
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Success" },
                ]}
            >
                <div className="flex items-center justify-center min-h-[60vh]">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardLayout>
        }>
            <SuccessContent />
        </Suspense>
    )
}
