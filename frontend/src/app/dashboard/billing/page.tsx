"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Wallet,
    BarChart3,
    Receipt,
    Check,
    X,
    Crown,
    Zap,
    Building2,
    Sparkles,
    AlertTriangle,
    Calendar,
    RefreshCw,
    Users,
    Video,
    Radio,
    HardDrive,
    Wifi,
    Download,
    Filter,
    Loader2,
    TrendingUp,
    Shield,
    Rocket,
    Gift,
    Star,
    CreditCard,
    ChevronLeft,
    ChevronRight,
} from "lucide-react"
import billingApi, {
    Subscription,
    Plan,
    UsageMetrics,
    UsageWarning,
    Invoice,
} from "@/lib/api/billing"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

// Default plans data - used as fallback when backend is unavailable
// These should match the plans seeded in the database (backend/scripts/seed_plans.py)
const defaultPlans: Plan[] = [
    {
        id: "free",
        name: "Free",
        slug: "free",
        price_monthly: 0,
        price_yearly: 0,
        features: [
            { name: "1 YouTube Account", included: true },
            { name: "5 Videos/month", included: true },
            { name: "Basic Analytics", included: true },
            { name: "AI Features", included: false },
            { name: "Live Streaming", included: false },
        ],
        limits: { max_accounts: 1, max_videos_per_month: 5, max_streams_per_month: 0, max_storage_gb: 1, max_bandwidth_gb: 5, ai_generations_per_month: 0 },
    },
    {
        id: "basic",
        name: "Basic",
        slug: "basic",
        price_monthly: 9.99,
        price_yearly: 99.99,
        features: [
            { name: "3 YouTube Accounts", included: true },
            { name: "50 Videos/month", included: true },
            { name: "Advanced Analytics", included: true },
            { name: "AI Features (100/month)", included: true },
            { name: "Live Streaming (5/month)", included: true },
        ],
        limits: { max_accounts: 3, max_videos_per_month: 50, max_streams_per_month: 5, max_storage_gb: 10, max_bandwidth_gb: 50, ai_generations_per_month: 100 },
    },
    {
        id: "pro",
        name: "Pro",
        slug: "pro",
        price_monthly: 29.99,
        price_yearly: 299.99,
        features: [
            { name: "10 YouTube Accounts", included: true },
            { name: "Unlimited Videos", included: true },
            { name: "Full Analytics Suite", included: true },
            { name: "AI Features (500/month)", included: true },
            { name: "Unlimited Streaming", included: true },
        ],
        limits: { max_accounts: 10, max_videos_per_month: -1, max_streams_per_month: -1, max_storage_gb: 100, max_bandwidth_gb: 500, ai_generations_per_month: 500 },
    },
    {
        id: "enterprise",
        name: "Enterprise",
        slug: "enterprise",
        price_monthly: 99.99,
        price_yearly: 999.99,
        features: [
            { name: "Unlimited Accounts", included: true },
            { name: "Unlimited Everything", included: true },
            { name: "Priority Support", included: true },
            { name: "Custom Integrations", included: true },
            { name: "Dedicated Account Manager", included: true },
        ],
        limits: { max_accounts: -1, max_videos_per_month: -1, max_streams_per_month: -1, max_storage_gb: -1, max_bandwidth_gb: -1, ai_generations_per_month: -1 },
    },
]

function BillingContent() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const tabParam = searchParams.get("tab")
    const [activeTab, setActiveTab] = useState(tabParam || "subscription")
    const [loading, setLoading] = useState(true)
    const [subscription, setSubscription] = useState<Subscription | null>(null)
    const [plans, setPlans] = useState<Plan[]>(defaultPlans)
    const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly")
    const [cancelDialogOpen, setCancelDialogOpen] = useState(false)
    const [cancelling, setCancelling] = useState(false)
    const [usage, setUsage] = useState<UsageMetrics | null>(null)
    const [warnings, setWarnings] = useState<UsageWarning[]>([])
    const [invoices, setInvoices] = useState<Invoice[]>([])
    const [dateFilter, setDateFilter] = useState<string>("all")
    const [currentPage, setCurrentPage] = useState(1)
    const itemsPerPage = 10

    useEffect(() => {
        if (tabParam && ["subscription", "usage", "history"].includes(tabParam)) setActiveTab(tabParam)
    }, [tabParam])

    useEffect(() => { loadAllData() }, [])

    const loadAllData = async () => {
        setLoading(true)
        try {
            // Load all billing data from backend
            const [sub, planList, usageData, warningsData, invoiceData] = await Promise.all([
                billingApi.getSubscription(),
                billingApi.getPlans().catch(() => []),
                billingApi.getUsage().catch(() => null),
                billingApi.getUsageWarnings().catch(() => []),
                billingApi.getInvoices().catch(() => []),
            ])
            setSubscription(sub)
            // Set billing cycle toggle to match user's current subscription
            if (sub?.billing_cycle) {
                setBillingCycle(sub.billing_cycle)
            }
            // Use backend plans if available, otherwise use default plans for UI display
            setPlans(Array.isArray(planList) && planList.length > 0 ? planList : defaultPlans)
            setUsage(usageData)
            setWarnings(warningsData)
            setInvoices(invoiceData)
        } catch (error) {
            console.error("Failed to load billing data:", error)
            // Keep default plans for UI but show empty data for other sections
            setPlans(defaultPlans)
            setUsage(null)
            setWarnings([])
            setInvoices([])
        } finally {
            setLoading(false)
        }
    }

    const handleUpgrade = (planSlug: string) => router.push(`/dashboard/billing/checkout?plan=${planSlug}&cycle=${billingCycle}`)
    const handleCancelSubscription = async () => {
        setCancelling(true)
        try { await billingApi.cancelSubscription(); await loadAllData(); setCancelDialogOpen(false) }
        catch (error) { console.error("Failed to cancel:", error) }
        finally { setCancelling(false) }
    }
    const handleResumeSubscription = async () => { try { await billingApi.resumeSubscription(); await loadAllData() } catch (error) { console.error("Failed to resume:", error) } }

    const getPlanIcon = (slug: string) => ({ free: Sparkles, basic: Zap, pro: Crown, enterprise: Building2 }[slug] || Sparkles)
    const getPlanGradient = (slug: string) => ({ free: "from-slate-500 to-slate-600", basic: "from-blue-500 to-cyan-500", pro: "from-violet-500 to-purple-600", enterprise: "from-amber-500 to-orange-500" }[slug] || "from-slate-500 to-slate-600")
    const getPlanBg = (slug: string) => ({ free: "bg-slate-500/5 border-slate-500/20", basic: "bg-blue-500/5 border-blue-500/20", pro: "bg-violet-500/5 border-violet-500/20", enterprise: "bg-amber-500/5 border-amber-500/20" }[slug] || "bg-slate-500/5")
    const formatPrice = (price: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(price)
    const formatCurrency = (amount: number, currency: string = "USD") => new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount)
    const getUsagePercentage = (used: number, limit: number): number => (limit === -1 || limit === 0) ? 0 : Math.min((used / limit) * 100, 100)
    const getUsageColor = (percentage: number): string => percentage >= 90 ? "text-red-500" : percentage >= 75 ? "text-amber-500" : "text-emerald-500"
    const getProgressGradient = (percentage: number): string => percentage >= 90 ? "from-red-500 to-red-600" : percentage >= 75 ? "from-amber-500 to-orange-500" : "from-emerald-500 to-green-500"
    const getStatusBadge = (status: Invoice["status"]) => {
        const styles: Record<string, string> = { paid: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", open: "bg-blue-500/10 text-blue-500 border-blue-500/20", draft: "bg-slate-500/10 text-slate-500 border-slate-500/20", void: "bg-red-500/10 text-red-500 border-red-500/20" }
        return <Badge variant="outline" className={cn("capitalize", styles[status] || styles.draft)}>{status}</Badge>
    }

    const currentPlan = subscription?.plan_tier || "free"
    const currentBillingCycle = subscription?.billing_cycle || "monthly"
    // Show "Current" badge only if plan matches AND billing cycle matches
    const isCurrentPlan = (slug: string) => currentPlan === slug && billingCycle === currentBillingCycle
    const displayPlans = Array.isArray(plans) && plans.length > 0 ? plans : defaultPlans
    // Use actual data from backend - no dummy fallback
    const filteredInvoices = invoices.filter(invoice => {
        if (dateFilter === "all") return true
        const invoiceDate = new Date(invoice.created_at)
        const now = new Date()
        if (dateFilter === "30d") return invoiceDate >= new Date(now.setDate(now.getDate() - 30))
        if (dateFilter === "90d") return invoiceDate >= new Date(now.setDate(now.getDate() - 90))
        if (dateFilter === "1y") return invoiceDate >= new Date(now.setFullYear(now.getFullYear() - 1))
        return true
    })

    // Pagination logic
    const totalPages = Math.ceil(filteredInvoices.length / itemsPerPage)
    const paginatedInvoices = filteredInvoices.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    )

    // Reset to page 1 when filter changes
    useEffect(() => {
        setCurrentPage(1)
    }, [dateFilter])

    if (loading) {
        return (
            <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing" }]}>
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                            <Wallet className="h-6 w-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <p className="text-muted-foreground animate-pulse">Loading billing data...</p>
                    </div>
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing" }]}>
            <div className="space-y-6">
                {/* Header - Simple style like monitoring */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Wallet className="h-8 w-8" />
                            Billing & Subscription
                        </h1>
                        <p className="text-muted-foreground">
                            Manage your plan, usage, and payments
                        </p>
                    </div>
                    {subscription && (
                        <div className="flex items-center gap-3 bg-muted/50 rounded-xl px-4 py-3">
                            <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br", getPlanGradient(subscription.plan_tier))}>
                                {(() => { const Icon = getPlanIcon(subscription.plan_tier); return <Icon className="h-5 w-5 text-white" /> })()}
                            </div>
                            <div>
                                <p className="text-xs text-muted-foreground">Current Plan</p>
                                <p className="font-semibold capitalize">{subscription.plan_tier} <span className="text-xs text-muted-foreground">({subscription.billing_cycle})</span></p>
                            </div>
                            <Badge variant="outline" className="ml-2">
                                <Calendar className="h-3 w-3 mr-1" />
                                Renews {new Date(subscription.current_period_end).toLocaleDateString()}
                            </Badge>
                        </div>
                    )}
                </div>

                {/* Modern Tabs */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                    <div className="flex justify-center">
                        <TabsList className="grid grid-cols-3 gap-2 bg-muted/50 p-1.5 rounded-xl h-auto">
                            <TabsTrigger value="subscription" className="flex items-center gap-2 px-6 py-3 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:text-primary transition-all">
                                <CreditCard className="h-4 w-4" />
                                <span className="font-medium">Plans</span>
                            </TabsTrigger>
                            <TabsTrigger value="usage" className="flex items-center gap-2 px-6 py-3 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:text-primary transition-all">
                                <BarChart3 className="h-4 w-4" />
                                <span className="font-medium">Usage</span>
                            </TabsTrigger>
                            <TabsTrigger value="history" className="flex items-center gap-2 px-6 py-3 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-lg data-[state=active]:text-primary transition-all">
                                <Receipt className="h-4 w-4" />
                                <span className="font-medium">History</span>
                            </TabsTrigger>
                        </TabsList>
                    </div>

                    {/* ==================== SUBSCRIPTION TAB ==================== */}
                    <TabsContent value="subscription" className="space-y-8 animate-in fade-in-50 duration-500">
                        {/* Billing Cycle Toggle */}
                        <div className="flex flex-col items-center gap-4">
                            <div className="inline-flex items-center rounded-full bg-muted/50 p-1.5 shadow-inner">
                                <button
                                    onClick={() => setBillingCycle("monthly")}
                                    className={cn("px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300", billingCycle === "monthly" ? "bg-white shadow-lg text-primary" : "text-muted-foreground hover:text-foreground")}
                                >
                                    Monthly
                                </button>
                                <button
                                    onClick={() => setBillingCycle("yearly")}
                                    className={cn("px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-300 flex items-center gap-2", billingCycle === "yearly" ? "bg-white shadow-lg text-primary" : "text-muted-foreground hover:text-foreground")}
                                >
                                    Yearly
                                    <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-emerald-500 to-green-500 text-white text-xs font-bold">-17%</span>
                                </button>
                            </div>
                            <p className="text-sm text-muted-foreground">Save 2 months with yearly billing</p>
                        </div>

                        {/* Plans Grid */}
                        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 items-stretch">
                            {displayPlans.map((plan, index) => {
                                const Icon = getPlanIcon(plan.slug)
                                const isCurrent = isCurrentPlan(plan.slug)
                                const price = billingCycle === "monthly" ? plan.price_monthly : plan.price_yearly
                                const planIndex = displayPlans.findIndex(p => p.slug === plan.slug)
                                const currentIndex = displayPlans.findIndex(p => p.slug === currentPlan)
                                const isUpgrade = planIndex > currentIndex
                                const isPro = plan.slug === "pro"

                                // Button gradient colors matching plan icon colors
                                const getButtonGradient = (slug: string) => ({
                                    free: "bg-gradient-to-r from-slate-500 to-slate-600 hover:from-slate-600 hover:to-slate-700 shadow-lg shadow-slate-500/30",
                                    basic: "bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 shadow-lg shadow-blue-500/30",
                                    pro: "bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 shadow-lg shadow-purple-500/30",
                                    enterprise: "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-lg shadow-amber-500/30"
                                }[slug] || "bg-gradient-to-r from-slate-500 to-slate-600")

                                return (
                                    <div key={plan.id} className={cn("relative group flex", isPro && "lg:-mt-4 lg:mb-4")}>
                                        {isPro && (
                                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                                                <div className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-gradient-to-r from-violet-500 to-purple-600 text-white text-xs font-bold shadow-lg shadow-purple-500/30">
                                                    <Star className="h-3 w-3 fill-current" />
                                                    MOST POPULAR
                                                </div>
                                            </div>
                                        )}
                                        {/* Card wrapper with snake border animation for current plan */}
                                        <div className="relative w-full h-full flex">
                                            {/* Snake border animation - only visible for current plan */}
                                            {isCurrent && (
                                                <>
                                                    <div className="absolute inset-0 rounded-xl overflow-hidden">
                                                        <div
                                                            className="absolute inset-[-100%] animate-spin-slow"
                                                            style={{
                                                                background: "conic-gradient(from 0deg, transparent 0deg, transparent 60deg, #ff0000 120deg, #ff3333 180deg, #ff0000 240deg, transparent 300deg, transparent 360deg)"
                                                            }}
                                                        />
                                                    </div>
                                                    <div className="absolute inset-[3px] rounded-lg bg-background" />
                                                </>
                                            )}
                                            <Card className={cn(
                                                "relative overflow-hidden transition-all duration-500 hover:shadow-2xl flex flex-col w-full h-full",
                                                isCurrent ? "border-0 shadow-lg shadow-red-500/20" : "border-2 border-transparent hover:border-primary/30",
                                                isPro && !isCurrent && "shadow-xl shadow-purple-500/10",
                                                getPlanBg(plan.slug)
                                            )}>
                                                {isCurrent && (
                                                    <div className="absolute top-4 right-4">
                                                        <Badge className="bg-primary text-primary-foreground">Current</Badge>
                                                    </div>
                                                )}
                                                <CardHeader className="text-center pb-2 pt-8">
                                                    <div className={cn("mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg mb-4 transition-transform duration-300 group-hover:scale-110", getPlanGradient(plan.slug))}>
                                                        <Icon className="h-8 w-8 text-white" />
                                                    </div>
                                                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                                                    <div className="mt-4">
                                                        <span className="text-4xl font-bold">{formatPrice(price)}</span>
                                                        <span className="text-muted-foreground">/{billingCycle === "monthly" ? "mo" : "yr"}</span>
                                                    </div>
                                                    {billingCycle === "yearly" && plan.price_monthly > 0 && (
                                                        <p className="text-sm text-muted-foreground mt-1">
                                                            <span className="line-through">{formatPrice(plan.price_monthly * 12)}</span>
                                                            <span className="text-emerald-500 ml-2">Save {formatPrice(plan.price_monthly * 12 - plan.price_yearly)}</span>
                                                        </p>
                                                    )}
                                                </CardHeader>
                                                <CardContent className="flex flex-col flex-grow pb-8">
                                                    <ul className="space-y-3 flex-grow">
                                                        {plan.features.map((feature, idx) => (
                                                            <li key={idx} className="flex items-center gap-3 text-sm">
                                                                {feature.included ? (
                                                                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/10">
                                                                        <Check className="h-3 w-3 text-emerald-500" />
                                                                    </div>
                                                                ) : (
                                                                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted">
                                                                        <X className="h-3 w-3 text-muted-foreground" />
                                                                    </div>
                                                                )}
                                                                <span className={feature.included ? "" : "text-muted-foreground"}>{feature.name}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                    <div className="mt-6">
                                                        <Button
                                                            className={cn(
                                                                "w-full h-12 rounded-xl font-semibold transition-all duration-300",
                                                                !isCurrent && getButtonGradient(plan.slug),
                                                                !isCurrent && "text-white",
                                                                isCurrent && "border-2"
                                                            )}
                                                            variant={isCurrent ? "outline" : "default"}
                                                            disabled={isCurrent || plan.slug === "free"}
                                                            onClick={() => handleUpgrade(plan.slug)}
                                                        >
                                                            {isCurrent ? "Current Plan" : isUpgrade ? (
                                                                <span className="flex items-center gap-2">Upgrade <Rocket className="h-4 w-4" /></span>
                                                            ) : plan.slug === "free" ? "Free Plan" : "Downgrade"}
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>

                        {/* Features Comparison */}
                        <Card className="border-0 shadow-xl bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
                            <CardHeader className="text-center">
                                <CardTitle className="flex items-center justify-center gap-2">
                                    <Gift className="h-5 w-5 text-primary" />
                                    All Plans Include
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {[
                                        { icon: Shield, label: "SSL Security" },
                                        { icon: TrendingUp, label: "Analytics" },
                                        { icon: RefreshCw, label: "Auto Sync" },
                                        { icon: Sparkles, label: "24/7 Support" },
                                    ].map((item, idx) => (
                                        <div key={idx} className="flex items-center gap-3 p-4 rounded-xl bg-white dark:bg-slate-800 shadow-sm">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                                <item.icon className="h-5 w-5 text-primary" />
                                            </div>
                                            <span className="font-medium text-sm">{item.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* ==================== USAGE TAB ==================== */}
                    <TabsContent value="usage" className="space-y-6 animate-in fade-in-50 duration-500">
                        {/* Empty State when no usage data */}
                        {!usage && (
                            <Card className="border-0 shadow-lg">
                                <CardContent className="flex flex-col items-center justify-center py-16">
                                    <BarChart3 className="h-16 w-16 text-muted-foreground/30 mb-4" />
                                    <h3 className="text-lg font-semibold mb-2">No Usage Data Available</h3>
                                    <p className="text-muted-foreground text-center max-w-md">
                                        Usage data will appear here once you start using the platform.
                                        Connect a YouTube account to get started.
                                    </p>
                                    <Button className="mt-6" onClick={() => router.push("/dashboard/accounts")}>
                                        Connect YouTube Account
                                    </Button>
                                </CardContent>
                            </Card>
                        )}

                        {/* Warnings */}
                        {usage && warnings.length > 0 && (
                            <div className="space-y-3">
                                {warnings.map((warning, idx) => (
                                    <div key={idx} className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/20">
                                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-medium text-amber-600 dark:text-amber-400">{warning.message}</p>
                                            <p className="text-sm text-muted-foreground">{warning.current_usage} of {warning.limit} used ({warning.percentage.toFixed(0)}%)</p>
                                        </div>
                                        <Badge variant="outline" className="border-amber-500/50 text-amber-600">{warning.threshold}%</Badge>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Show usage content only when data is available */}

                        {/* Billing Period Card */}
                        {usage && (
                            <Card className="border-0 shadow-lg bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5">
                                <CardContent className="p-6">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                                                <Calendar className="h-6 w-6 text-primary" />
                                            </div>
                                            <div>
                                                <p className="text-sm text-muted-foreground">Current Billing Period</p>
                                                <p className="font-semibold">{new Date(usage.period_start).toLocaleDateString()} - {new Date(usage.period_end).toLocaleDateString()}</p>
                                            </div>
                                        </div>
                                        <Button variant="outline" className="gap-2">
                                            <Download className="h-4 w-4" />
                                            Export
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        )}

                        {/* Usage Meters Grid */}
                        {usage && (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {[
                                    { key: "accounts", label: "YouTube Accounts", icon: Users, used: usage.accounts_used, limit: usage.accounts_limit, gradient: "from-blue-500 to-cyan-500", bg: "bg-blue-500/10" },
                                    { key: "videos", label: "Videos Uploaded", icon: Video, used: usage.videos_uploaded, limit: usage.videos_limit, unit: "/month", gradient: "from-red-500 to-rose-500", bg: "bg-red-500/10" },
                                    { key: "streams", label: "Streams Created", icon: Radio, used: usage.streams_created, limit: usage.streams_limit, unit: "/month", gradient: "from-violet-500 to-purple-500", bg: "bg-violet-500/10" },
                                    { key: "storage", label: "Storage Used", icon: HardDrive, used: usage.storage_used_gb, limit: usage.storage_limit_gb, unit: " GB", gradient: "from-emerald-500 to-green-500", bg: "bg-emerald-500/10" },
                                    { key: "bandwidth", label: "Bandwidth Used", icon: Wifi, used: usage.bandwidth_used_gb, limit: usage.bandwidth_limit_gb, unit: " GB", gradient: "from-orange-500 to-amber-500", bg: "bg-orange-500/10" },
                                    { key: "ai", label: "AI Generations", icon: Sparkles, used: usage.ai_generations_used, limit: usage.ai_generations_limit, unit: "/month", gradient: "from-pink-500 to-rose-500", bg: "bg-pink-500/10" },
                                ].map((metric) => {
                                    const percentage = getUsagePercentage(metric.used, metric.limit)
                                    const Icon = metric.icon
                                    return (
                                        <Card key={metric.key} className="border-0 shadow-lg overflow-hidden group hover:shadow-xl transition-all duration-300">
                                            <CardContent className="p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg transition-transform duration-300 group-hover:scale-110", metric.gradient)}>
                                                            <Icon className="h-6 w-6 text-white" />
                                                        </div>
                                                        <div>
                                                            <p className="font-semibold">{metric.label}</p>
                                                            <p className="text-xs text-muted-foreground">{metric.unit || ""}</p>
                                                        </div>
                                                    </div>
                                                    {percentage >= 75 && (
                                                        <div className={cn("flex h-8 w-8 items-center justify-center rounded-full", percentage >= 90 ? "bg-red-500/10" : "bg-amber-500/10")}>
                                                            <AlertTriangle className={cn("h-4 w-4", percentage >= 90 ? "text-red-500" : "text-amber-500")} />
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="space-y-3">
                                                    <div className="flex items-baseline justify-between">
                                                        <span className={cn("text-3xl font-bold", getUsageColor(percentage))}>
                                                            {typeof metric.used === "number" && metric.used % 1 !== 0 ? metric.used.toFixed(1) : metric.used}
                                                        </span>
                                                        <span className="text-sm text-muted-foreground">
                                                            / {metric.limit === -1 ? "∞" : `${metric.limit}${metric.unit?.replace("/month", "") || ""}`}
                                                        </span>
                                                    </div>
                                                    <div className="relative h-3 rounded-full bg-muted overflow-hidden">
                                                        <div
                                                            className={cn("absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-all duration-500", getProgressGradient(percentage))}
                                                            style={{ width: `${percentage}%` }}
                                                        />
                                                    </div>
                                                    <p className="text-xs text-muted-foreground text-right">
                                                        {metric.limit === -1 ? "Unlimited" : `${percentage.toFixed(0)}% used`}
                                                    </p>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )
                                })}
                            </div>
                        )}
                    </TabsContent>

                    {/* ==================== HISTORY TAB ==================== */}
                    <TabsContent value="history" className="space-y-6 animate-in fade-in-50 duration-500">
                        {/* Payment History */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                                            <Receipt className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">Payment History</CardTitle>
                                            <CardDescription>Your payment transactions</CardDescription>
                                        </div>
                                    </div>
                                    <Select value={dateFilter} onValueChange={setDateFilter}>
                                        <SelectTrigger className="w-[150px] rounded-xl">
                                            <Filter className="h-4 w-4 mr-2" />
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Time</SelectItem>
                                            <SelectItem value="30d">Last 30 Days</SelectItem>
                                            <SelectItem value="90d">Last 90 Days</SelectItem>
                                            <SelectItem value="1y">Last Year</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="rounded-xl border overflow-hidden">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="bg-muted/50">
                                                <TableHead>Description</TableHead>
                                                <TableHead>Date</TableHead>
                                                <TableHead>Gateway</TableHead>
                                                <TableHead>Amount</TableHead>
                                                <TableHead>Status</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {paginatedInvoices.map((invoice) => (
                                                <TableRow key={invoice.id} className="hover:bg-muted/30">
                                                    <TableCell>
                                                        <div className="flex items-center gap-3">
                                                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                                                                <Receipt className="h-4 w-4 text-primary" />
                                                            </div>
                                                            <span className="font-medium">{invoice.number}</span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground">{new Date(invoice.created_at).toLocaleDateString()}</TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" className="capitalize">
                                                            {(invoice as any).gateway_provider || "N/A"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="font-semibold">{formatCurrency(invoice.amount, invoice.currency)}</TableCell>
                                                    <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                                                </TableRow>
                                            ))}
                                            {filteredInvoices.length === 0 && (
                                                <TableRow>
                                                    <TableCell colSpan={5} className="text-center py-12">
                                                        <div className="flex flex-col items-center gap-2">
                                                            <Receipt className="h-12 w-12 text-muted-foreground/30" />
                                                            <p className="text-muted-foreground">No payment history found</p>
                                                            <p className="text-sm text-muted-foreground">Your payment transactions will appear here</p>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            )}
                                        </TableBody>
                                    </Table>
                                </div>

                                {/* Pagination */}
                                {filteredInvoices.length > 0 && (
                                    <div className="flex items-center justify-between mt-4">
                                        <p className="text-sm text-muted-foreground">
                                            Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredInvoices.length)} of {filteredInvoices.length} transactions
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                                disabled={currentPage === 1}
                                                className="rounded-lg"
                                            >
                                                <ChevronLeft className="h-4 w-4 mr-1" />
                                                Previous
                                            </Button>
                                            <div className="flex items-center gap-1">
                                                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                                    <Button
                                                        key={page}
                                                        variant={currentPage === page ? "default" : "outline"}
                                                        size="sm"
                                                        onClick={() => setCurrentPage(page)}
                                                        className={cn(
                                                            "w-8 h-8 p-0 rounded-lg",
                                                            currentPage === page && "bg-primary text-primary-foreground"
                                                        )}
                                                    >
                                                        {page}
                                                    </Button>
                                                ))}
                                            </div>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                                disabled={currentPage === totalPages}
                                                className="rounded-lg"
                                            >
                                                Next
                                                <ChevronRight className="h-4 w-4 ml-1" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>

                {/* Dialogs */}
                <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
                    <DialogContent className="sm:max-w-md">
                        <DialogHeader>
                            <DialogTitle className="flex items-center gap-2">
                                <AlertTriangle className="h-5 w-5 text-amber-500" />
                                Cancel Subscription
                            </DialogTitle>
                            <DialogDescription>Are you sure? You will lose access to premium features at the end of your billing period.</DialogDescription>
                        </DialogHeader>
                        <DialogFooter className="gap-2">
                            <Button variant="outline" onClick={() => setCancelDialogOpen(false)}>Keep Subscription</Button>
                            <Button variant="destructive" onClick={handleCancelSubscription} disabled={cancelling}>
                                {cancelling ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Cancelling...</> : "Cancel Subscription"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>


            </div>
        </DashboardLayout>
    )
}

export default function BillingPage() {
    return (
        <Suspense fallback={
            <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Billing" }]}>
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="h-16 w-16 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                            <Wallet className="h-6 w-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                        </div>
                        <p className="text-muted-foreground animate-pulse">Loading...</p>
                    </div>
                </div>
            </DashboardLayout>
        }>
            <BillingContent />
        </Suspense>
    )
}
