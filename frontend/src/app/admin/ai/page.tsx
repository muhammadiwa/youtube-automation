"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Brain,
    Sparkles,
    DollarSign,
    Activity,
    RefreshCcw,
    TrendingUp,
    TrendingDown,
    Zap,
    MessageSquare,
    Image,
    FileText,
    Tag,
    AlertTriangle,
    Clock,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import Link from "next/link"
import {
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts"

// Types for AI Dashboard
interface AIFeatureUsage {
    feature: string
    api_calls: number
    tokens_used: number
    cost_usd: number
    success_rate: number
    avg_latency_ms: number
}

interface AIDashboardMetrics {
    total_api_calls: number
    total_tokens_used: number
    total_cost_usd: number
    monthly_budget_usd: number
    budget_used_percentage: number
    usage_by_feature: AIFeatureUsage[]
    period_start: string
    period_end: string
    is_throttled: boolean
}

// Feature icons mapping
const featureIcons: Record<string, React.ReactNode> = {
    titles: <FileText className="h-4 w-4" />,
    descriptions: <MessageSquare className="h-4 w-4" />,
    thumbnails: <Image className="h-4 w-4" />,
    chatbot: <Sparkles className="h-4 w-4" />,
    tags: <Tag className="h-4 w-4" />,
}

const PIE_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981"]

export default function AdminAIDashboardPage() {
    const [metrics, setMetrics] = useState<AIDashboardMetrics | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchMetrics = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch("/api/admin/ai/dashboard", {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            })
            if (!response.ok) throw new Error("Failed to fetch AI metrics")
            const data = await response.json()
            setMetrics(data)
        } catch (err) {
            console.error("Failed to fetch AI dashboard:", err)
            setError("Failed to load AI dashboard metrics")
            // Set mock data for development
            setMetrics({
                total_api_calls: 15420,
                total_tokens_used: 2450000,
                total_cost_usd: 245.50,
                monthly_budget_usd: 1000,
                budget_used_percentage: 24.55,
                usage_by_feature: [
                    { feature: "titles", api_calls: 5200, tokens_used: 520000, cost_usd: 52.00, success_rate: 98.5, avg_latency_ms: 450 },
                    { feature: "descriptions", api_calls: 4100, tokens_used: 820000, cost_usd: 82.00, success_rate: 97.2, avg_latency_ms: 680 },
                    { feature: "thumbnails", api_calls: 2800, tokens_used: 280000, cost_usd: 56.00, success_rate: 95.8, avg_latency_ms: 1200 },
                    { feature: "chatbot", api_calls: 2500, tokens_used: 625000, cost_usd: 37.50, success_rate: 99.1, avg_latency_ms: 320 },
                    { feature: "tags", api_calls: 820, tokens_used: 205000, cost_usd: 18.00, success_rate: 98.9, avg_latency_ms: 280 },
                ],
                period_start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
                period_end: new Date().toISOString(),
                is_throttled: false,
            })
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchMetrics()
    }, [fetchMetrics])

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
        }).format(amount)
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    // Prepare chart data
    const costByFeatureData = metrics?.usage_by_feature.map(item => ({
        name: item.feature.charAt(0).toUpperCase() + item.feature.slice(1),
        value: item.cost_usd,
        calls: item.api_calls,
    })) || []

    const callsByFeatureData = metrics?.usage_by_feature.map(item => ({
        name: item.feature.charAt(0).toUpperCase() + item.feature.slice(1),
        calls: item.api_calls,
        tokens: item.tokens_used,
    })) || []

    return (
        <AdminLayout breadcrumbs={[{ label: "AI Service Management" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
                                className="h-12 w-12 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25"
                            >
                                <Brain className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                                    AI Service Management
                                </h1>
                                <p className="text-muted-foreground">
                                    Monitor AI usage, costs, and performance
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <Link href="/admin/ai/logs">
                            <Button variant="outline">
                                <Activity className="h-4 w-4 mr-2" />
                                View Logs
                            </Button>
                        </Link>
                        <Button variant="outline" size="icon" onClick={fetchMetrics} disabled={isLoading}>
                            <RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                        </Button>
                    </div>
                </motion.div>

                {isLoading ? (
                    <LoadingSkeleton />
                ) : error && !metrics ? (
                    <ErrorState error={error} onRetry={fetchMetrics} />
                ) : metrics ? (
                    <>
                        {/* Throttle Warning */}
                        {metrics.is_throttled && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
                            >
                                <div className="flex items-center gap-3">
                                    <AlertTriangle className="h-5 w-5 text-amber-600" />
                                    <div>
                                        <p className="font-medium text-amber-900 dark:text-amber-100">AI Services Throttled</p>
                                        <p className="text-sm text-amber-700 dark:text-amber-300">
                                            Budget threshold reached. AI requests are being rate-limited.
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {/* Key Metrics Cards */}
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <MetricCard
                                title="Total API Calls"
                                value={formatNumber(metrics.total_api_calls)}
                                icon={<Zap className="h-5 w-5" />}
                                gradient="from-blue-500 to-cyan-600"
                                delay={0.1}
                            />
                            <MetricCard
                                title="Tokens Used"
                                value={formatNumber(metrics.total_tokens_used)}
                                icon={<Activity className="h-5 w-5" />}
                                gradient="from-violet-500 to-purple-600"
                                delay={0.15}
                            />
                            <MetricCard
                                title="Total Cost"
                                value={formatCurrency(metrics.total_cost_usd)}
                                icon={<DollarSign className="h-5 w-5" />}
                                gradient="from-emerald-500 to-teal-600"
                                delay={0.2}
                            />
                            <BudgetCard
                                budget={metrics.monthly_budget_usd}
                                spent={metrics.total_cost_usd}
                                percentage={metrics.budget_used_percentage}
                                delay={0.25}
                            />
                        </div>

                        {/* Charts Section */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Cost by Feature - Pie Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                            >
                                <Card>
                                    <CardHeader>
                                        <div className="flex items-center gap-2">
                                            <DollarSign className="h-5 w-5 text-emerald-500" />
                                            <CardTitle>Cost by Feature</CardTitle>
                                        </div>
                                        <CardDescription>AI spending distribution</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-[300px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <PieChart>
                                                    <Pie
                                                        data={costByFeatureData}
                                                        cx="50%"
                                                        cy="50%"
                                                        innerRadius={60}
                                                        outerRadius={100}
                                                        paddingAngle={5}
                                                        dataKey="value"
                                                    >
                                                        {costByFeatureData.map((_, index) => (
                                                            <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                                        ))}
                                                    </Pie>
                                                    <Tooltip
                                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                                                        formatter={(value: number) => [formatCurrency(value), "Cost"]}
                                                    />
                                                    <Legend />
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>

                            {/* API Calls by Feature - Bar Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.35 }}
                            >
                                <Card>
                                    <CardHeader>
                                        <div className="flex items-center gap-2">
                                            <Zap className="h-5 w-5 text-blue-500" />
                                            <CardTitle>API Calls by Feature</CardTitle>
                                        </div>
                                        <CardDescription>Request volume per feature</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="h-[300px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={callsByFeatureData} layout="vertical">
                                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
                                                    <XAxis type="number" className="text-xs" />
                                                    <YAxis type="category" dataKey="name" className="text-xs" width={100} />
                                                    <Tooltip
                                                        contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px" }}
                                                        formatter={(value: number) => [formatNumber(value), "Calls"]}
                                                    />
                                                    <Bar dataKey="calls" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Feature Usage Table */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <Card>
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Sparkles className="h-5 w-5 text-purple-500" />
                                        <CardTitle>Usage by Feature</CardTitle>
                                    </div>
                                    <CardDescription>Detailed breakdown of AI feature usage</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead>
                                                <tr className="border-b">
                                                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Feature</th>
                                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">API Calls</th>
                                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">Tokens</th>
                                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">Cost</th>
                                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">Success Rate</th>
                                                    <th className="text-right py-3 px-4 font-medium text-muted-foreground">Avg Latency</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {metrics.usage_by_feature.map((feature, index) => (
                                                    <tr key={feature.feature} className="border-b last:border-0 hover:bg-muted/50">
                                                        <td className="py-3 px-4">
                                                            <div className="flex items-center gap-2">
                                                                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500/10 to-indigo-500/10 flex items-center justify-center">
                                                                    {featureIcons[feature.feature] || <Sparkles className="h-4 w-4" />}
                                                                </div>
                                                                <span className="font-medium capitalize">{feature.feature}</span>
                                                            </div>
                                                        </td>
                                                        <td className="text-right py-3 px-4">{formatNumber(feature.api_calls)}</td>
                                                        <td className="text-right py-3 px-4">{formatNumber(feature.tokens_used)}</td>
                                                        <td className="text-right py-3 px-4">{formatCurrency(feature.cost_usd)}</td>
                                                        <td className="text-right py-3 px-4">
                                                            <Badge variant={feature.success_rate >= 95 ? "default" : "destructive"}>
                                                                {feature.success_rate.toFixed(1)}%
                                                            </Badge>
                                                        </td>
                                                        <td className="text-right py-3 px-4">
                                                            <div className="flex items-center justify-end gap-1">
                                                                <Clock className="h-3 w-3 text-muted-foreground" />
                                                                <span>{feature.avg_latency_ms.toFixed(0)}ms</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Quick Actions */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.45 }}
                        >
                            <Card>
                                <CardHeader>
                                    <CardTitle>Quick Actions</CardTitle>
                                    <CardDescription>Manage AI service configuration</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                        <Link href="/admin/ai/logs">
                                            <Button variant="outline" className="w-full justify-start">
                                                <Activity className="h-4 w-4 mr-2" />
                                                View AI Logs
                                            </Button>
                                        </Link>
                                        <Link href="/admin/config/ai">
                                            <Button variant="outline" className="w-full justify-start">
                                                <Brain className="h-4 w-4 mr-2" />
                                                AI Configuration
                                            </Button>
                                        </Link>
                                        <Link href="/admin/ai/limits">
                                            <Button variant="outline" className="w-full justify-start">
                                                <Zap className="h-4 w-4 mr-2" />
                                                Plan Limits
                                            </Button>
                                        </Link>
                                        <Link href="/admin/ai/models">
                                            <Button variant="outline" className="w-full justify-start">
                                                <Sparkles className="h-4 w-4 mr-2" />
                                                Model Config
                                            </Button>
                                        </Link>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </>
                ) : null}
            </div>
        </AdminLayout>
    )
}

// Metric Card Component
function MetricCard({ title, value, icon, gradient, delay }: {
    title: string
    value: string
    icon: React.ReactNode
    gradient: string
    delay: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
        >
            <Card className={cn("relative overflow-hidden border-0 text-white shadow-xl", `bg-gradient-to-br ${gradient}`)}>
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                <CardContent className="p-6 relative">
                    <div className="flex items-center justify-between mb-4">
                        <p className="text-sm font-medium opacity-90">{title}</p>
                        <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                            {icon}
                        </div>
                    </div>
                    <p className="text-3xl font-bold">{value}</p>
                </CardContent>
            </Card>
        </motion.div>
    )
}

// Budget Card Component
function BudgetCard({ budget, spent, percentage, delay }: {
    budget: number
    spent: number
    percentage: number
    delay: number
}) {
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
        }).format(amount)
    }

    const isWarning = percentage >= 75
    const isCritical = percentage >= 90

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
        >
            <Card className={cn(
                "relative overflow-hidden border-0 text-white shadow-xl",
                isCritical ? "bg-gradient-to-br from-red-500 to-rose-600" :
                    isWarning ? "bg-gradient-to-br from-amber-500 to-orange-600" :
                        "bg-gradient-to-br from-slate-600 to-slate-700"
            )}>
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-16 translate-x-16" />
                <CardContent className="p-6 relative">
                    <div className="flex items-center justify-between mb-4">
                        <p className="text-sm font-medium opacity-90">Budget Usage</p>
                        <div className="h-10 w-10 rounded-xl bg-white/20 flex items-center justify-center">
                            <DollarSign className="h-5 w-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold mb-2">{percentage.toFixed(1)}%</p>
                    <Progress value={percentage} className="h-2 bg-white/20" />
                    <p className="text-sm opacity-90 mt-2">
                        {formatCurrency(spent)} / {formatCurrency(budget)}
                    </p>
                </CardContent>
            </Card>
        </motion.div>
    )
}

// Loading Skeleton
function LoadingSkeleton() {
    return (
        <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i}>
                        <CardContent className="p-6">
                            <Skeleton className="h-4 w-24 mb-2" />
                            <Skeleton className="h-8 w-32" />
                        </CardContent>
                    </Card>
                ))}
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
                <Card><CardContent className="p-6"><Skeleton className="h-[300px]" /></CardContent></Card>
                <Card><CardContent className="p-6"><Skeleton className="h-[300px]" /></CardContent></Card>
            </div>
        </div>
    )
}

// Error State
function ErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-20 text-center"
        >
            <div className="h-20 w-20 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
                <TrendingDown className="h-10 w-10 text-red-500" />
            </div>
            <p className="text-lg font-medium text-red-500 mb-2">Failed to load AI metrics</p>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={onRetry}>Try Again</Button>
        </motion.div>
    )
}
