"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import {
    ShoppingCart,
    CreditCard,
    Check,
    X,
    Loader2,
    ArrowLeft,
    Shield,
    Lock,
    Wallet,
    Building2,
    QrCode,
    Sparkles,
    Zap,
    Crown,
} from "lucide-react"
import billingApi, { Plan, GatewayProvider, GatewayPublicInfo, PlanTier } from "@/lib/api/billing"
import Link from "next/link"
import { cn } from "@/lib/utils"

const gatewayIcons: Record<GatewayProvider, React.ComponentType<{ className?: string }>> = {
    stripe: CreditCard,
    paypal: Wallet,
    midtrans: QrCode,
    xendit: Building2,
}

const gatewayColors: Record<GatewayProvider, string> = {
    stripe: "from-indigo-500 to-indigo-600",
    paypal: "from-blue-500 to-blue-600",
    midtrans: "from-teal-500 to-teal-600",
    xendit: "from-cyan-500 to-cyan-600",
}

const gatewayDescriptions: Record<GatewayProvider, string> = {
    stripe: "Pay securely with credit or debit card",
    paypal: "Pay with your PayPal account",
    midtrans: "Indonesian payment methods (GoPay, OVO, DANA)",
    xendit: "Southeast Asian payment methods",
}

const planIcons: Record<PlanTier, React.ComponentType<{ className?: string }>> = {
    free: Sparkles,
    basic: Zap,
    pro: Crown,
    enterprise: Building2,
}

const planGradients: Record<PlanTier, string> = {
    free: "from-slate-500 to-slate-600",
    basic: "from-blue-500 to-cyan-500",
    pro: "from-violet-500 to-purple-600",
    enterprise: "from-amber-500 to-orange-500",
}

function CheckoutContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const planSlug = searchParams.get("plan") as PlanTier | null
    const cycle = (searchParams.get("cycle") as "monthly" | "yearly") || "monthly"

    const [plan, setPlan] = useState<Plan | null>(null)
    const [gateways, setGateways] = useState<GatewayPublicInfo[]>([])
    const [selectedGateway, setSelectedGateway] = useState<GatewayProvider | null>(null)
    const [rememberPreference, setRememberPreference] = useState(false)
    const [loading, setLoading] = useState(true)
    const [gatewaysLoading, setGatewaysLoading] = useState(true)
    const [processing, setProcessing] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadData()
    }, [planSlug])

    const loadData = async () => {
        if (!planSlug) {
            router.push("/dashboard/billing")
            return
        }

        setLoading(true)
        setGatewaysLoading(true)

        try {
            // Load plans and gateways in parallel
            const [plans, gatewayList] = await Promise.all([
                billingApi.getPlans(),
                billingApi.getEnabledGateways("USD"),
            ])

            // Find selected plan
            const selectedPlan = plans.find(p => p.slug === planSlug)
            if (selectedPlan) {
                setPlan(selectedPlan)
            } else {
                router.push("/dashboard/billing")
                return
            }

            // Set gateways
            setGateways(gatewayList)

            // Auto-select first gateway or default
            if (gatewayList.length > 0 && !selectedGateway) {
                setSelectedGateway(gatewayList[0].provider)
            }
        } catch (error) {
            console.error("Failed to load checkout data:", error)
            setError("Failed to load checkout data. Please try again.")
        } finally {
            setLoading(false)
            setGatewaysLoading(false)
        }
    }

    const handleCheckout = async () => {
        if (!plan || !selectedGateway) return

        setProcessing(true)
        setError(null)

        try {
            const price = cycle === "monthly" ? plan.price_monthly : plan.price_yearly
            const baseUrl = window.location.origin

            // Create payment through the payments API
            const session = await billingApi.createPayment({
                amount: price,
                currency: "USD",
                description: `${plan.name} Plan - ${cycle} subscription`,
                preferred_gateway: selectedGateway,
                success_url: `${baseUrl}/dashboard/billing/checkout/success?plan=${plan.slug}&cycle=${cycle}`,
                cancel_url: `${baseUrl}/dashboard/billing/checkout/failed?plan=${plan.slug}`,
                metadata: {
                    plan_id: plan.id,
                    plan_slug: plan.slug,
                    billing_cycle: cycle,
                },
            })

            // Redirect to gateway checkout URL if available
            if (session.checkout_url) {
                window.location.href = session.checkout_url
            } else {
                // If no checkout URL, redirect to success page (for demo/testing)
                router.push(`/dashboard/billing/checkout/success?plan=${plan.slug}&cycle=${cycle}&payment_id=${session.payment_id}`)
            }
        } catch (err: any) {
            console.error("Checkout error:", err)
            setError(err.message || "Failed to create checkout session. Please try again.")
            setProcessing(false)
        }
    }

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
        }).format(price)
    }

    const price = plan ? (cycle === "monthly" ? plan.price_monthly : plan.price_yearly) : 0
    const savings = plan ? (plan.price_monthly * 12 - plan.price_yearly) : 0
    const PlanIcon = plan ? planIcons[plan.slug] : Sparkles

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Checkout" },
                ]}
            >
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                            <ShoppingCart className="h-6 w-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <p className="text-muted-foreground animate-pulse">Loading checkout...</p>
                    </div>
                </div>
            </DashboardLayout>
        )
    }

    if (!plan) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Checkout" },
                ]}
            >
                <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                    <X className="h-16 w-16 text-muted-foreground" />
                    <p className="text-lg text-muted-foreground">Plan not found</p>
                    <Link href="/dashboard/billing">
                        <Button>Back to Billing</Button>
                    </Link>
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Billing", href: "/dashboard/billing" },
                { label: "Checkout" },
            ]}
        >
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/billing">
                        <Button variant="ghost" size="icon" className="rounded-xl">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                            <ShoppingCart className="h-7 w-7" />
                            Checkout
                        </h1>
                        <p className="text-muted-foreground">
                            Complete your subscription upgrade
                        </p>
                    </div>
                </div>

                <div className="grid gap-6 lg:grid-cols-5">
                    {/* Order Summary */}
                    <div className="lg:col-span-2">
                        <Card className="border-0 shadow-xl sticky top-6 overflow-hidden">
                            <div className={cn("h-2 bg-gradient-to-r", planGradients[plan.slug])} />
                            <CardHeader>
                                <CardTitle className="text-lg">Order Summary</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <div className={cn(
                                        "flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg",
                                        planGradients[plan.slug]
                                    )}>
                                        <PlanIcon className="h-7 w-7 text-white" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="font-semibold text-lg">{plan.name} Plan</p>
                                        <p className="text-sm text-muted-foreground capitalize">
                                            {cycle} billing
                                        </p>
                                    </div>
                                    <Badge variant="secondary" className="capitalize">
                                        {plan.slug}
                                    </Badge>
                                </div>

                                <Separator />

                                <div className="space-y-2">
                                    <p className="text-sm font-medium">Features included:</p>
                                    <ul className="space-y-2">
                                        {plan.features.filter(f => f.included).slice(0, 5).map((feature, idx) => (
                                            <li key={idx} className="flex items-center gap-2 text-sm">
                                                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/10">
                                                    <Check className="h-3 w-3 text-emerald-500" />
                                                </div>
                                                <span className="text-muted-foreground">{feature.name}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <Separator />

                                <div className="space-y-3">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">Subtotal</span>
                                        <span>{formatPrice(price)}</span>
                                    </div>
                                    {cycle === "yearly" && savings > 0 && (
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-emerald-600">Annual savings</span>
                                            <span className="text-emerald-600">-{formatPrice(savings)}</span>
                                        </div>
                                    )}
                                    <Separator />
                                    <div className="flex items-center justify-between">
                                        <span className="font-semibold">Total</span>
                                        <div className="text-right">
                                            <span className="text-2xl font-bold">{formatPrice(price)}</span>
                                            <p className="text-xs text-muted-foreground">
                                                {cycle === "monthly" ? "per month" : "per year"}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Payment Form */}
                    <div className="lg:col-span-3 space-y-6">
                        <Card className="border-0 shadow-xl">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <CreditCard className="h-5 w-5" />
                                    Payment Method
                                </CardTitle>
                                <CardDescription>
                                    Choose how you&apos;d like to pay
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {gatewaysLoading ? (
                                    <div className="grid gap-3 sm:grid-cols-2">
                                        {[1, 2].map((i) => (
                                            <div key={i} className="p-4 rounded-xl border bg-muted/50 animate-pulse">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-10 w-10 rounded-lg bg-muted" />
                                                    <div className="flex-1 space-y-2">
                                                        <div className="h-4 w-20 bg-muted rounded" />
                                                        <div className="h-3 w-32 bg-muted rounded" />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : gateways.length > 0 ? (
                                    <>
                                        <Label className="text-base font-semibold">Select Payment Method</Label>
                                        <div className="grid gap-3 sm:grid-cols-2">
                                            {gateways.map((gateway) => {
                                                const Icon = gatewayIcons[gateway.provider]
                                                const isSelected = selectedGateway === gateway.provider
                                                const gradient = gatewayColors[gateway.provider]

                                                return (
                                                    <div
                                                        key={gateway.provider}
                                                        className={cn(
                                                            "p-4 rounded-xl border-2 cursor-pointer transition-all duration-200",
                                                            isSelected
                                                                ? "border-primary bg-primary/5 shadow-lg"
                                                                : "border-transparent bg-muted/30 hover:bg-muted/50 hover:shadow-md"
                                                        )}
                                                        onClick={() => setSelectedGateway(gateway.provider)}
                                                    >
                                                        <div className="flex items-start gap-3">
                                                            <div className={cn(
                                                                "flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br shadow-md",
                                                                gradient
                                                            )}>
                                                                <Icon className="h-5 w-5 text-white" />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <span className="font-semibold">{gateway.display_name}</span>
                                                                <p className="text-sm text-muted-foreground mt-0.5">
                                                                    {gatewayDescriptions[gateway.provider]}
                                                                </p>
                                                            </div>
                                                            <div className={cn(
                                                                "h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors",
                                                                isSelected
                                                                    ? "border-primary bg-primary"
                                                                    : "border-muted-foreground/30"
                                                            )}>
                                                                {isSelected && (
                                                                    <div className="h-2 w-2 rounded-full bg-white" />
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )
                                            })}
                                        </div>

                                        <div className="flex items-center space-x-2 pt-2">
                                            <Checkbox
                                                id="remember"
                                                checked={rememberPreference}
                                                onCheckedChange={(checked) => setRememberPreference(checked as boolean)}
                                            />
                                            <Label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">
                                                Remember my preferred payment method
                                            </Label>
                                        </div>
                                    </>
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <CreditCard className="h-12 w-12 mx-auto mb-3 opacity-50" />
                                        <p>No payment methods available</p>
                                        <p className="text-sm">Please contact support</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Error Message */}
                        {error && (
                            <Card className="border-0 shadow-lg bg-red-500/10 border border-red-500/20">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/20">
                                            <X className="h-5 w-5 text-red-500" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-red-600 dark:text-red-400">
                                                Payment Error
                                            </p>
                                            <p className="text-sm text-muted-foreground">{error}</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Security Notice */}
                        <Card className="border-0 shadow-lg bg-emerald-500/5 border border-emerald-500/10">
                            <CardContent className="p-4">
                                <div className="flex items-start gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/20">
                                        <Shield className="h-5 w-5 text-emerald-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-emerald-600 dark:text-emerald-400">
                                            Secure Payment
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            Your payment information is encrypted and secure. We never store your full card details.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Checkout Button */}
                        <Button
                            className="w-full h-14 text-lg rounded-xl shadow-lg"
                            size="lg"
                            disabled={!selectedGateway || processing || gateways.length === 0}
                            onClick={handleCheckout}
                        >
                            {processing ? (
                                <>
                                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Lock className="h-5 w-5 mr-2" />
                                    Pay {formatPrice(price)}
                                </>
                            )}
                        </Button>

                        <p className="text-xs text-center text-muted-foreground">
                            By completing this purchase, you agree to our{" "}
                            <Link href="/terms" className="underline hover:text-foreground">
                                Terms of Service
                            </Link>{" "}
                            and{" "}
                            <Link href="/privacy" className="underline hover:text-foreground">
                                Privacy Policy
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    )
}

export default function CheckoutPage() {
    return (
        <Suspense fallback={
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Billing", href: "/dashboard/billing" },
                    { label: "Checkout" },
                ]}
            >
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                            <ShoppingCart className="h-6 w-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <p className="text-muted-foreground animate-pulse">Loading...</p>
                    </div>
                </div>
            </DashboardLayout>
        }>
            <CheckoutContent />
        </Suspense>
    )
}
