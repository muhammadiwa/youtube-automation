"use client"

import { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { OverviewCard } from "@/components/dashboard/overview-card"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    CreditCard,
    Wallet,
    Building2,
    QrCode,
    BarChart3,
    TrendingUp,
    DollarSign,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    ArrowLeft,
    Loader2,
} from "lucide-react"
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    Legend,
} from "recharts"
import { useTheme } from "next-themes"
import billingApi, { GatewayStatistics, GatewayProvider } from "@/lib/api/billing"
import Link from "next/link"
import { cn } from "@/lib/utils"

const gatewayIcons: Record<GatewayProvider, React.ComponentType<{ className?: string }>> = {
    stripe: CreditCard,
    paypal: Wallet,
    midtrans: QrCode,
    xendit: Building2,
}

const gatewayColors: Record<GatewayProvider, string> = {
    stripe: "#6366f1",
    paypal: "#3b82f6",
    midtrans: "#14b8a6",
    xendit: "#06b6d4",
}

export default function GatewayStatisticsPage() {
    const { theme } = useTheme()
    const isDark = theme === "dark"
    const [statistics, setStatistics] = useState<GatewayStatistics[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadStatistics()
    }, [])

    const loadStatistics = async () => {
        setLoading(true)
        try {
            const data = await billingApi.getGatewayStatistics()
            // API returns { gateways: [...], total_volume, total_transactions, overall_success_rate }
            setStatistics(data.gateways || [])
        } catch (error) {
            console.error("Failed to load statistics:", error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount)
    }

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
        return num.toString()
    }

    const getHealthBadge = (status: GatewayStatistics["health_status"]) => {
        switch (status) {
            case "healthy":
                return (
                    <Badge className="bg-green-500">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Healthy
                    </Badge>
                )
            case "degraded":
                return (
                    <Badge className="bg-amber-500">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Degraded
                    </Badge>
                )
            case "down":
                return (
                    <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        Down
                    </Badge>
                )
        }
    }

    // Calculate totals
    const totals = statistics.reduce(
        (acc, stat) => ({
            transactions: acc.transactions + stat.total_transactions,
            successful: acc.successful + stat.successful_transactions,
            failed: acc.failed + stat.failed_transactions,
            volume: acc.volume + stat.total_volume,
        }),
        { transactions: 0, successful: 0, failed: 0, volume: 0 }
    )

    const overallSuccessRate = totals.transactions > 0
        ? ((totals.successful / totals.transactions) * 100).toFixed(1)
        : "0"

    // Prepare chart data
    const volumeChartData = statistics.map(stat => ({
        name: stat.provider.charAt(0).toUpperCase() + stat.provider.slice(1),
        volume: stat.total_volume,
        fill: gatewayColors[stat.provider],
    }))

    const transactionChartData = statistics.map(stat => ({
        name: stat.provider.charAt(0).toUpperCase() + stat.provider.slice(1),
        successful: stat.successful_transactions,
        failed: stat.failed_transactions,
    }))

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border rounded-xl p-3 shadow-xl">
                    <p className="font-semibold text-sm mb-2">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                            <div
                                className="h-2.5 w-2.5 rounded-full"
                                style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-muted-foreground capitalize">{entry.name}:</span>
                            <span className="font-medium">
                                {entry.name === "volume" ? formatCurrency(entry.value) : formatNumber(entry.value)}
                            </span>
                        </div>
                    ))}
                </div>
            )
        }
        return null
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Admin", href: "/admin" },
                    { label: "Payment Gateways", href: "/admin/payment-gateways" },
                    { label: "Statistics" },
                ]}
            >
                <div className="flex items-center justify-center min-h-[400px]">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Admin", href: "/admin" },
                { label: "Payment Gateways", href: "/admin/payment-gateways" },
                { label: "Statistics" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Link href="/admin/payment-gateways">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                            <BarChart3 className="h-7 w-7" />
                            Gateway Statistics
                        </h1>
                        <p className="text-muted-foreground">
                            Transaction metrics and performance data
                        </p>
                    </div>
                </div>

                {/* Overview Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <OverviewCard
                        title="Total Transactions"
                        value={formatNumber(totals.transactions)}
                        icon={CreditCard}
                        gradient="from-blue-500 to-blue-600"
                    />
                    <OverviewCard
                        title="Success Rate"
                        value={`${overallSuccessRate}%`}
                        icon={TrendingUp}
                        gradient="from-green-500 to-green-600"
                    />
                    <OverviewCard
                        title="Total Volume"
                        value={formatCurrency(totals.volume)}
                        icon={DollarSign}
                        gradient="from-purple-500 to-purple-600"
                    />
                    <OverviewCard
                        title="Failed Transactions"
                        value={formatNumber(totals.failed)}
                        icon={XCircle}
                        gradient="from-red-500 to-red-600"
                    />
                </div>

                {/* Charts */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Volume by Gateway */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="text-lg">Volume by Gateway</CardTitle>
                            <CardDescription>Total transaction volume per gateway</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={volumeChartData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={2}
                                        dataKey="volume"
                                    >
                                        {volumeChartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.fill} />
                                        ))}
                                    </Pie>
                                    <Tooltip content={<CustomTooltip />} />
                                    <Legend
                                        verticalAlign="bottom"
                                        height={36}
                                        formatter={(value) => (
                                            <span className="text-sm text-foreground">{value}</span>
                                        )}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* Transactions by Gateway */}
                    <Card className="border-0 shadow-lg">
                        <CardHeader>
                            <CardTitle className="text-lg">Transactions by Gateway</CardTitle>
                            <CardDescription>Successful vs failed transactions</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={transactionChartData}>
                                    <CartesianGrid
                                        strokeDasharray="3 3"
                                        stroke={isDark ? "#374151" : "#e5e7eb"}
                                        vertical={false}
                                    />
                                    <XAxis
                                        dataKey="name"
                                        stroke={isDark ? "#6b7280" : "#9ca3af"}
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        stroke={isDark ? "#6b7280" : "#9ca3af"}
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(value) => formatNumber(value)}
                                    />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar dataKey="successful" fill="#22c55e" radius={[4, 4, 0, 0]} name="Successful" />
                                    <Bar dataKey="failed" fill="#ef4444" radius={[4, 4, 0, 0]} name="Failed" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>

                {/* Detailed Statistics Table */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="text-lg">Gateway Details</CardTitle>
                        <CardDescription>Detailed statistics per payment gateway</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Gateway</TableHead>
                                    <TableHead className="text-right">Transactions</TableHead>
                                    <TableHead className="text-right">Success Rate</TableHead>
                                    <TableHead className="text-right">Volume</TableHead>
                                    <TableHead className="text-right">Avg. Transaction</TableHead>
                                    <TableHead className="text-right">Last Transaction</TableHead>
                                    <TableHead className="text-right">Health</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {statistics.map((stat) => {
                                    const Icon = gatewayIcons[stat.provider]
                                    return (
                                        <TableRow key={stat.provider}>
                                            <TableCell>
                                                <div className="flex items-center gap-3">
                                                    <div
                                                        className="flex h-8 w-8 items-center justify-center rounded-lg"
                                                        style={{ backgroundColor: `${gatewayColors[stat.provider]}20` }}
                                                    >
                                                        <Icon className="h-4 w-4" />
                                                    </div>
                                                    <span className="font-medium capitalize">{stat.provider}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                {formatNumber(stat.total_transactions)}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <span className={cn(
                                                    "font-medium",
                                                    stat.success_rate >= 95 ? "text-green-500" :
                                                        stat.success_rate >= 90 ? "text-amber-500" : "text-red-500"
                                                )}>
                                                    {stat.success_rate.toFixed(1)}%
                                                </span>
                                            </TableCell>
                                            <TableCell className="text-right font-medium">
                                                {formatCurrency(stat.total_volume)}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                {formatCurrency(stat.average_transaction)}
                                            </TableCell>
                                            <TableCell className="text-right text-muted-foreground">
                                                {stat.last_transaction_at
                                                    ? new Date(stat.last_transaction_at).toLocaleDateString()
                                                    : "N/A"}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                {getHealthBadge(stat.health_status)}
                                            </TableCell>
                                        </TableRow>
                                    )
                                })}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
