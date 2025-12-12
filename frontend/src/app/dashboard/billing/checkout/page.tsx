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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Input } from "@/components/ui/input"
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
    Clock,
    Gift,
    AlertCircle,
    CheckCircle2,
    Info,
    Tag,
    Percent,
} from "lucide-react"
import billingApi, { Plan, GatewayProvider, GatewayPublicInfo, PlanTier } from "@/lib/api/billing"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useAuth } from "@/hooks/use-auth"
import apiClient from "@/lib/api/client"

const gatewayIcons: Record<GatewayProvider, React.ComponentType<{ className?: string }>> = {
    stripe: CreditCard,
    paypal: Wallet,
    midtrans: QrCode,
    xendit: Building2,
}

const gatewayColors: Record<GatewayProvider, string> = {
    stripe: "from-indigo-500 to-purple-600",
    paypal: "from-blue-500 to-blue-600",
    midtrans: "from-teal-500 to-emerald-600",
    xendit: "from-cyan-500 to-blue-600",
}

const gatewayBgColors: Record<GatewayProvider, string> = {
    stripe: "bg-indigo-500/10 border-indigo-500/20",
    paypal: "bg-blue-500/10 border-blue-500/20",
    midtrans: "bg-teal-500/10 border-teal-500/20",
    xendit: "bg-cyan-500/10 border-cyan-500/20",
}

const gatewayDescriptions: Record<GatewayProvider, string> = {
    stripe: "Credit/Debit Card, Apple Pay, Google Pay",
    paypal: "PayPal Balance, Credit Card via PayPal",
    midtrans: "GoPay, OVO, DANA, Bank Transfer, QRIS",
    xendit: "E-Wallet, Virtual Account, Retail Outlets",
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
    const { user, isLoading: authLoading } = useAuth()
    const planSlug = searchParams.get("plan") as PlanTier | null
    const cycle = (searchParams.get("cycle") as "monthly" | "yearly") || "monthly"

    const [plan, setPlan] = useState<Plan | null>(null)
    const [gateways, setGateways] = useState<GatewayPublicInfo[]>([])
    const [selectedGateway, setSelectedGateway] = useState<GatewayProvider | null>(null)
    const [agreeTerms, setAgreeTerms] = useState(false)
    const [loading, setLoading] = useState(true)
    const [processing, setProcessing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [convertedPrice, setConvertedPrice] = useState<{ amount: number; currency: string; rate: number } | null>(null)
    const [convertingCurrency, setConvertingCurrency] = useState(false)

    // Promo code state
    const [promoCode, setPromoCode] = useState("")
    const [promoCodeValidating, setPromoCodeValidating] = useState(false)
    const [promoCodeApplied, setPromoCodeApplied] = useState<{
        code: string
        discount_type: "percentage" | "fixed"
        discount_value: number
        discount_amount: number
        final_amount: number
    } | null>(null)
    const [promoCodeError, setPromoCodeError] = useState<string | null>(null)

    // Ensure user ID is set in apiClient when user is available
    useEffect(() => {
        if (user?.id) {
            apiClient.setUserId(user.id)
        }
    }, [user])

    useEffect(() => {
        if (!authLoading) {
            loadData()
        }
    }, [planSlug, authLoading])

    const loadData = async () => {
        if (!planSlug) {
            router.push("/dashboard/billing")
            return
        }

        setLoading(true)

        try {
            const [plans, gatewayList] = await Promise.all([
                billingApi.getPlans(),
                billingApi.getEnabledGateways(), // Get all enabled gateways, no currency filter
            ])

            console.log("Loaded plans:", plans)
            console.log("Loaded gateways:", gatewayList)

            const selectedPlan = plans.find(p => p.slug === planSlug)
            if (selectedPlan) {
                setPlan(selectedPlan)
            } else {
                router.push("/dashboard/billing")
                return
            }

            setGateways(gatewayList)
            if (gatewayList.length > 0 && !selectedGateway) {
                // Find default gateway first, then fallback to first gateway
                const defaultGateway = gatewayList.find(g => g.is_default) || gatewayList[0]
                setSelectedGateway(defaultGateway.provider)
            }
        } catch (error) {
            console.error("Failed to load checkout data:", error)
            setError("Failed to load checkout data. Please try again.")
        } finally {
            setLoading(false)
        }
    }

    // Convert currency when gateway changes (for gateways that don't support USD)
    useEffect(() => {
        const convertPrice = async () => {
            if (!plan || !selectedGateway) return

            const gateway = gateways.find(g => g.provider === selectedGateway)
            if (!gateway) return

            // Check if gateway supports USD
            const supportsUSD = gateway.supported_currencies.includes("USD")

            if (!supportsUSD && gateway.supported_currencies.length > 0) {
                // Need to convert to gateway's currency
                const targetCurrency = gateway.supported_currencies[0] // Use first supported currency
                const price = cycle === "monthly" ? plan.price_monthly : plan.price_yearly

                setConvertingCurrency(true)
                try {
                    const result = await billingApi.convertCurrency(price, "USD", targetCurrency)
                    setConvertedPrice({
                        amount: result.converted_amount,
                        currency: targetCurrency,
                        rate: result.exchange_rate,
                    })
                } catch (err) {
                    console.error("Currency conversion failed:", err)
                    setConvertedPrice(null)
                } finally {
                    setConvertingCurrency(false)
                }
            } else {
                setConvertedPrice(null)
            }
        }

        convertPrice()
    }, [selectedGateway, plan, cycle, gateways])

    // Handle promo code validation
    const handleApplyPromoCode = async () => {
        if (!promoCode.trim() || !plan) return

        setPromoCodeValidating(true)
        setPromoCodeError(null)

        try {
            const basePrice = cycle === "monthly" ? plan.price_monthly : plan.price_yearly
            const result = await billingApi.validateDiscountCode(promoCode.trim(), plan.slug, basePrice)

            if (result.is_valid && result.code) {
                setPromoCodeApplied({
                    code: result.code,
                    discount_type: result.discount_type as "percentage" | "fixed",
                    discount_value: result.discount_value || 0,
                    discount_amount: result.discount_amount || 0,
                    final_amount: result.final_amount || basePrice,
                })
                setPromoCodeError(null)
            } else {
                setPromoCodeError(result.message)
                setPromoCodeApplied(null)
            }
        } catch (err) {
            console.error("Failed to validate promo code:", err)
            setPromoCodeError("Failed to validate promo code. Please try again.")
            setPromoCodeApplied(null)
        } finally {
            setPromoCodeValidating(false)
        }
    }

    const handleRemovePromoCode = () => {
        setPromoCodeApplied(null)
        setPromoCode("")
        setPromoCodeError(null)
    }

    const handleCheckout = async () => {
        if (!plan || !selectedGateway || !agreeTerms) return

        // Ensure user is logged in
        if (!user?.id) {
            setError("Please log in to continue with checkout.")
            return
        }

        // Ensure user ID is set in apiClient
        apiClient.setUserId(user.id)

        setProcessing(true)
        setError(null)

        try {
            const basePrice = cycle === "monthly" ? plan.price_monthly : plan.price_yearly
            const baseUrl = window.location.origin

            // Apply discount if promo code is applied
            let finalPrice = basePrice
            if (promoCodeApplied) {
                finalPrice = promoCodeApplied.final_amount
            }

            // Determine amount and currency based on gateway support
            // If gateway doesn't support USD and we have converted price, use that
            let paymentAmount = finalPrice
            let paymentCurrency = "USD"

            if (convertedPrice) {
                // Recalculate converted price with discount
                if (promoCodeApplied) {
                    const discountRatio = finalPrice / basePrice
                    paymentAmount = Math.round(convertedPrice.amount * discountRatio)
                } else {
                    paymentAmount = convertedPrice.amount
                }
                paymentCurrency = convertedPrice.currency
            }

            // Debug logging
            console.log("Creating payment:", {
                amount: paymentAmount,
                currency: paymentCurrency,
                gateway: selectedGateway,
                convertedPrice,
                promoCode: promoCodeApplied?.code,
                userId: user.id,
            })

            // Note: For PayPal, the success_url will have additional params added by PayPal (token, PayerID)
            // We include plan and cycle for display purposes
            const session = await billingApi.createPayment({
                amount: paymentAmount,
                currency: paymentCurrency,
                description: `${plan.name} Plan - ${cycle} subscription${promoCodeApplied ? ` (Promo: ${promoCodeApplied.code})` : ""}`,
                preferred_gateway: selectedGateway,
                success_url: `${baseUrl}/dashboard/billing/checkout/success?plan=${plan.slug}&cycle=${cycle}${promoCodeApplied ? `&promo=${promoCodeApplied.code}` : ""}`,
                cancel_url: `${baseUrl}/dashboard/billing/checkout/failed?plan=${plan.slug}&reason=cancelled`,
                metadata: {
                    plan_id: plan.id,
                    plan_slug: plan.slug,
                    billing_cycle: cycle,
                    original_amount_usd: basePrice, // Store original USD amount for reference
                    promo_code: promoCodeApplied?.code,
                    discount_amount: promoCodeApplied?.discount_amount,
                    discount_type: promoCodeApplied?.discount_type,
                },
            })

            // Check if payment failed
            if (session.status === "failed") {
                const errorMsg = session.error_message || "Payment processing failed. Please try a different payment method or contact support."
                setError(errorMsg)
                setProcessing(false)
                return
            }

            // Redirect to checkout URL if available
            if (session.checkout_url) {
                window.location.href = session.checkout_url
            } else if (session.status === "completed") {
                // Only redirect to success if payment is completed
                router.push(`/dashboard/billing/checkout/success?plan=${plan.slug}&cycle=${cycle}&payment_id=${session.payment_id}`)
            } else {
                // Payment is pending but no checkout URL - show error
                setError("Payment gateway is not properly configured. Please contact support or try a different payment method.")
                setProcessing(false)
            }
        } catch (err: any) {
            console.error("Checkout error:", err)
            setError(err.message || err.detail || "Failed to create checkout session. Please try again.")
            setProcessing(false)
        }
    }

    const formatPrice = (price: number, currency: string = "USD") => {
        return new Intl.NumberFormat(currency === "IDR" ? "id-ID" : "en-US", {
            style: "currency",
            currency: currency,
            minimumFractionDigits: currency === "IDR" ? 0 : 2,
            maximumFractionDigits: currency === "IDR" ? 0 : 2,
        }).format(price)
    }

    const price = plan ? (cycle === "monthly" ? plan.price_monthly : plan.price_yearly) : 0
    const monthlyEquivalent = plan && cycle === "yearly" ? plan.price_yearly / 12 : price
    const savings = plan ? (plan.price_monthly * 12 - plan.price_yearly) : 0
    const PlanIcon = plan ? planIcons[plan.slug] : Sparkles

    if (loading || authLoading) {
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
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard/billing">
                            <Button variant="ghost" size="icon" className="rounded-xl">
                                <ArrowLeft className="h-5 w-5" />
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold flex items-center gap-2">
                                <ShoppingCart className="h-8 w-8" />
                                Checkout
                            </h1>
                            <p className="text-muted-foreground">
                                Complete your subscription upgrade
                            </p>
                        </div>
                    </div>
                    <Badge variant="outline" className="text-sm px-3 py-1">
                        <Lock className="h-3 w-3 mr-1" />
                        Secure Checkout
                    </Badge>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Left Column - Plan & Payment */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Selected Plan Card */}
                        <Card className="border-0 shadow-lg overflow-hidden">
                            <div className={cn("h-2 bg-gradient-to-r", planGradients[plan.slug])} />
                            <CardHeader className="pb-4">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-xl">Selected Plan</CardTitle>
                                    <Badge className={cn("bg-gradient-to-r text-white", planGradients[plan.slug])}>
                                        {plan.name}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-start gap-6">
                                    <div className={cn(
                                        "flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg shrink-0",
                                        planGradients[plan.slug]
                                    )}>
                                        <PlanIcon className="h-10 w-10 text-white" />
                                    </div>
                                    <div className="flex-1 space-y-4">
                                        <div>
                                            <h3 className="text-2xl font-bold">{plan.name} Plan</h3>
                                            <p className="text-muted-foreground">
                                                {cycle === "monthly" ? "Billed monthly" : "Billed annually (save 17%)"}
                                            </p>
                                        </div>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-4xl font-bold">{formatPrice(price)}</span>
                                            <span className="text-muted-foreground">/{cycle === "monthly" ? "month" : "year"}</span>
                                        </div>
                                        {cycle === "yearly" && (
                                            <div className="flex items-center gap-2 text-sm">
                                                <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                                                    <Gift className="h-3 w-3 mr-1" />
                                                    Save {formatPrice(savings)}/year
                                                </Badge>
                                                <span className="text-muted-foreground">
                                                    ({formatPrice(monthlyEquivalent)}/month equivalent)
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <Separator className="my-6" />

                                {/* Features Grid */}
                                <div>
                                    <h4 className="font-semibold mb-4">What&apos;s included:</h4>
                                    <div className="grid sm:grid-cols-2 gap-3">
                                        {plan.features.map((feature, idx) => (
                                            <div key={idx} className="flex items-center gap-3">
                                                {feature.included ? (
                                                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/10">
                                                        <Check className="h-4 w-4 text-emerald-500" />
                                                    </div>
                                                ) : (
                                                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted">
                                                        <X className="h-4 w-4 text-muted-foreground" />
                                                    </div>
                                                )}
                                                <span className={cn(
                                                    "text-sm",
                                                    feature.included ? "" : "text-muted-foreground"
                                                )}>
                                                    {feature.name}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Payment Method Card */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-xl flex items-center gap-2">
                                    <CreditCard className="h-5 w-5" />
                                    Payment Method
                                </CardTitle>
                                <CardDescription>
                                    Select your preferred payment method
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {gateways.length > 0 ? (
                                    <RadioGroup
                                        value={selectedGateway || ""}
                                        onValueChange={(value) => setSelectedGateway(value as GatewayProvider)}
                                        className="space-y-3"
                                    >
                                        {gateways.map((gateway) => {
                                            const Icon = gatewayIcons[gateway.provider]
                                            const isSelected = selectedGateway === gateway.provider

                                            return (
                                                <div
                                                    key={gateway.provider}
                                                    className={cn(
                                                        "relative flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all",
                                                        isSelected
                                                            ? cn("border-primary shadow-md", gatewayBgColors[gateway.provider])
                                                            : "border-border hover:border-primary/50 hover:bg-muted/50"
                                                    )}
                                                    onClick={() => setSelectedGateway(gateway.provider)}
                                                >
                                                    <RadioGroupItem value={gateway.provider} id={gateway.provider} className="sr-only" />
                                                    <div className={cn(
                                                        "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-md shrink-0",
                                                        gatewayColors[gateway.provider]
                                                    )}>
                                                        <Icon className="h-6 w-6 text-white" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <Label htmlFor={gateway.provider} className="text-base font-semibold cursor-pointer">
                                                            {gateway.display_name}
                                                        </Label>
                                                        <p className="text-sm text-muted-foreground">
                                                            {gatewayDescriptions[gateway.provider]}
                                                        </p>
                                                    </div>
                                                    <div className={cn(
                                                        "h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all shrink-0",
                                                        isSelected
                                                            ? "border-primary bg-primary"
                                                            : "border-muted-foreground/30"
                                                    )}>
                                                        {isSelected && <Check className="h-4 w-4 text-white" />}
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </RadioGroup>
                                ) : (
                                    <div className="text-center py-12 bg-muted/30 rounded-xl">
                                        <AlertCircle className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
                                        <p className="font-medium">No payment methods available</p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            Please contact support to enable payment gateways
                                        </p>
                                    </div>
                                )}

                                {/* Info Box */}
                                <div className="flex items-start gap-3 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                                    <Info className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
                                    <div className="text-sm">
                                        <p className="font-medium text-blue-600 dark:text-blue-400">
                                            Secure Payment Processing
                                        </p>
                                        <p className="text-muted-foreground">
                                            You&apos;ll be redirected to complete payment securely. Your card details are never stored on our servers.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Right Column - Order Summary */}
                    <div className="space-y-6">
                        <Card className="border-0 shadow-lg sticky top-6">
                            <CardHeader>
                                <CardTitle className="text-xl">Order Summary</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-muted-foreground">{plan.name} Plan ({cycle})</span>
                                        <span className={cn("font-medium", promoCodeApplied && "line-through text-muted-foreground")}>{formatPrice(price)}</span>
                                    </div>
                                    {cycle === "yearly" && savings > 0 && (
                                        <div className="flex items-center justify-between text-emerald-600">
                                            <span>Annual discount</span>
                                            <span>-{formatPrice(savings)}</span>
                                        </div>
                                    )}
                                    {promoCodeApplied && (
                                        <div className="flex items-center justify-between text-emerald-600">
                                            <span className="flex items-center gap-1.5">
                                                <Tag className="h-3.5 w-3.5" />
                                                Promo: {promoCodeApplied.code}
                                                <button
                                                    onClick={handleRemovePromoCode}
                                                    className="ml-1 text-muted-foreground hover:text-red-500 transition-colors"
                                                >
                                                    <X className="h-3.5 w-3.5" />
                                                </button>
                                            </span>
                                            <span>-{formatPrice(promoCodeApplied.discount_amount)}</span>
                                        </div>
                                    )}
                                </div>

                                <Separator />

                                {/* Promo Code Input */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium flex items-center gap-2">
                                        <Percent className="h-4 w-4" />
                                        Promo Code
                                    </Label>
                                    {!promoCodeApplied ? (
                                        <div className="flex gap-2">
                                            <Input
                                                placeholder="Enter code"
                                                value={promoCode}
                                                onChange={(e) => {
                                                    setPromoCode(e.target.value.toUpperCase())
                                                    setPromoCodeError(null)
                                                }}
                                                className="flex-1 uppercase"
                                                disabled={promoCodeValidating}
                                            />
                                            <Button
                                                variant="outline"
                                                onClick={handleApplyPromoCode}
                                                disabled={!promoCode.trim() || promoCodeValidating}
                                            >
                                                {promoCodeValidating ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    "Apply"
                                                )}
                                            </Button>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                            <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
                                            <div className="flex-1">
                                                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                                                    {promoCodeApplied.code} applied!
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {promoCodeApplied.discount_type === "percentage"
                                                        ? `${promoCodeApplied.discount_value}% off`
                                                        : `$${promoCodeApplied.discount_value} off`}
                                                </p>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={handleRemovePromoCode}
                                                className="h-8 w-8 p-0 text-muted-foreground hover:text-red-500"
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    )}
                                    {promoCodeError && (
                                        <p className="text-xs text-red-500 flex items-center gap-1">
                                            <AlertCircle className="h-3 w-3" />
                                            {promoCodeError}
                                        </p>
                                    )}
                                </div>

                                <Separator />

                                <div className="flex items-center justify-between text-lg font-bold">
                                    <span>Total</span>
                                    <span>{formatPrice(promoCodeApplied ? promoCodeApplied.final_amount : price)}</span>
                                </div>

                                {/* Show converted price for non-USD gateways */}
                                {convertingCurrency && (
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        <span>Converting currency...</span>
                                    </div>
                                )}
                                {convertedPrice && !convertingCurrency && (
                                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                        <div className="flex items-center justify-between text-sm">
                                            <span className="text-amber-600 dark:text-amber-400">
                                                Charged in {convertedPrice.currency}
                                            </span>
                                            <span className="font-semibold text-amber-600 dark:text-amber-400">
                                                {formatPrice(
                                                    promoCodeApplied
                                                        ? Math.round(convertedPrice.amount * (promoCodeApplied.final_amount / price))
                                                        : convertedPrice.amount,
                                                    convertedPrice.currency
                                                )}
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Rate: 1 USD = {convertedPrice.rate.toLocaleString()} {convertedPrice.currency}
                                        </p>
                                    </div>
                                )}

                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Clock className="h-4 w-4" />
                                    <span>
                                        {cycle === "monthly" ? "Renews monthly" : "Renews annually"}
                                    </span>
                                </div>

                                <Separator />

                                {/* Terms Agreement */}
                                <div className="flex items-start gap-3">
                                    <Checkbox
                                        id="terms"
                                        checked={agreeTerms}
                                        onCheckedChange={(checked) => setAgreeTerms(checked as boolean)}
                                        className="mt-1"
                                    />
                                    <Label htmlFor="terms" className="text-sm text-muted-foreground cursor-pointer leading-relaxed">
                                        I agree to the{" "}
                                        <Link href="/terms" className="text-primary underline hover:no-underline">
                                            Terms of Service
                                        </Link>{" "}
                                        and{" "}
                                        <Link href="/privacy" className="text-primary underline hover:no-underline">
                                            Privacy Policy
                                        </Link>
                                    </Label>
                                </div>

                                {/* Error Message */}
                                {error && (
                                    <div className="flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
                                        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                                    </div>
                                )}

                                {/* Checkout Button */}
                                <Button
                                    className={cn(
                                        "w-full h-14 text-lg rounded-xl shadow-lg transition-all",
                                        "bg-gradient-to-r",
                                        planGradients[plan.slug],
                                        "hover:opacity-90"
                                    )}
                                    size="lg"
                                    disabled={!selectedGateway || processing || convertingCurrency || gateways.length === 0 || !agreeTerms}
                                    onClick={handleCheckout}
                                >
                                    {processing ? (
                                        <>
                                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                            Processing...
                                        </>
                                    ) : convertingCurrency ? (
                                        <>
                                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                            Converting...
                                        </>
                                    ) : (
                                        <>
                                            <Lock className="h-5 w-5 mr-2" />
                                            Pay {convertedPrice
                                                ? formatPrice(
                                                    promoCodeApplied
                                                        ? Math.round(convertedPrice.amount * (promoCodeApplied.final_amount / price))
                                                        : convertedPrice.amount,
                                                    convertedPrice.currency
                                                )
                                                : formatPrice(promoCodeApplied ? promoCodeApplied.final_amount : price)}
                                        </>
                                    )}
                                </Button>

                                {/* Security Badge */}
                                <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                                    <Shield className="h-4 w-4" />
                                    <span>256-bit SSL Encrypted</span>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Trust Badges */}
                        <Card className="border-0 shadow-lg bg-gradient-to-br from-emerald-500/5 to-emerald-500/10">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/20">
                                        <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                                    </div>
                                    <div>
                                        <p className="font-medium text-emerald-600 dark:text-emerald-400">
                                            Money-back Guarantee
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            30-day refund if not satisfied
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
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
