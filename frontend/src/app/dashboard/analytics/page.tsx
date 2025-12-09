"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { OverviewCard } from "@/components/dashboard/overview-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
    Eye,
    Users,
    Clock,
    DollarSign,
    TrendingUp,
    Calendar,
    ArrowRight,
    BarChart3,
} from "lucide-react";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    Legend,
} from "recharts";
import { useTheme } from "next-themes";
import Link from "next/link";
import analyticsApi, { AnalyticsOverview, TimeSeriesData } from "@/lib/api/analytics";
import { AIInsightsPanel } from "@/components/dashboard/ai-insights-panel";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";

type Period = "7d" | "30d" | "90d" | "1y";

export default function AnalyticsPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [period, setPeriod] = useState<Period>("30d");
    const [compareEnabled, setCompareEnabled] = useState(false);
    const [selectedAccount, setSelectedAccount] = useState<string>("all");
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([]);
    const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
    const [viewsData, setViewsData] = useState<TimeSeriesData[]>([]);
    const [subscribersData, setSubscribersData] = useState<TimeSeriesData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAccounts();
    }, []);

    useEffect(() => {
        loadAnalytics();
    }, [period, selectedAccount]);

    const loadAccounts = async () => {
        const data = await accountsApi.getAccounts();
        setAccounts(data);
    };

    const loadAnalytics = async () => {
        setLoading(true);
        try {
            const params = {
                period,
                account_id: selectedAccount !== "all" ? selectedAccount : undefined,
            };

            const [overviewData, views, subscribers] = await Promise.all([
                analyticsApi.getOverview(params),
                analyticsApi.getViewsTimeSeries({
                    ...params,
                    granularity: period === "7d" ? "day" : period === "30d" ? "day" : "week",
                }),
                analyticsApi.getSubscribersTimeSeries({
                    ...params,
                    granularity: period === "7d" ? "day" : period === "30d" ? "day" : "week",
                }),
            ]);

            setOverview(overviewData);
            setViewsData(views);
            setSubscribersData(subscribers);
        } catch (error) {
            console.error("Failed to load analytics:", error);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    const formatWatchTime = (minutes: number): string => {
        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            return `${formatNumber(hours)}h`;
        }
        return `${minutes}m`;
    };

    // Combine views and subscribers data for chart
    const chartData = viewsData.map((v, i) => ({
        date: new Date(v.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        views: v.value,
        subscribers: subscribersData[i]?.value || 0,
    }));

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
                            <span className="font-medium">{formatNumber(entry.value)}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    const periodLabels: Record<Period, string> = {
        "7d": "Last 7 days",
        "30d": "Last 30 days",
        "90d": "Last 90 days",
        "1y": "Last year",
    };

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Analytics" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Analytics Overview</h1>
                        <p className="text-muted-foreground">
                            Track performance across all your channels
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        {/* Account Filter */}
                        <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="All Accounts" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Accounts</SelectItem>
                                {accounts.map((account) => (
                                    <SelectItem key={account.id} value={account.id}>
                                        {account.channelTitle}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        {/* Date Range Selector */}
                        <Select value={period} onValueChange={(v) => setPeriod(v as Period)}>
                            <SelectTrigger className="w-[150px]">
                                <Calendar className="h-4 w-4 mr-2" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="7d">Last 7 days</SelectItem>
                                <SelectItem value="30d">Last 30 days</SelectItem>
                                <SelectItem value="90d">Last 90 days</SelectItem>
                                <SelectItem value="1y">Last year</SelectItem>
                            </SelectContent>
                        </Select>

                        {/* Period Comparison Toggle */}
                        <div className="flex items-center gap-2 px-3 py-2 bg-muted/50 rounded-lg">
                            <Switch
                                id="compare"
                                checked={compareEnabled}
                                onCheckedChange={setCompareEnabled}
                            />
                            <Label htmlFor="compare" className="text-sm cursor-pointer">
                                Compare
                            </Label>
                        </div>
                    </div>
                </div>

                {/* Key Metrics Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <OverviewCard
                        title="Total Views"
                        value={formatNumber(overview?.total_views || 0)}
                        icon={Eye}
                        trend={overview ? {
                            value: Math.abs(overview.views_change),
                            isPositive: overview.views_change >= 0,
                        } : undefined}
                        gradient="from-blue-500 to-blue-600"
                    />
                    <OverviewCard
                        title="Subscribers"
                        value={formatNumber(overview?.total_subscribers || 0)}
                        icon={Users}
                        trend={overview ? {
                            value: Math.abs(overview.subscribers_change),
                            isPositive: overview.subscribers_change >= 0,
                        } : undefined}
                        gradient="from-green-500 to-green-600"
                    />
                    <OverviewCard
                        title="Watch Time"
                        value={formatWatchTime(overview?.total_watch_time || 0)}
                        icon={Clock}
                        trend={overview ? {
                            value: Math.abs(overview.watch_time_change),
                            isPositive: overview.watch_time_change >= 0,
                        } : undefined}
                        gradient="from-purple-500 to-purple-600"
                    />
                    <OverviewCard
                        title="Revenue"
                        value={`$${formatNumber(overview?.total_revenue || 0)}`}
                        icon={DollarSign}
                        trend={overview ? {
                            value: Math.abs(overview.revenue_change),
                            isPositive: overview.revenue_change >= 0,
                        } : undefined}
                        gradient="from-amber-500 to-amber-600"
                    />
                </div>

                {/* Charts Section */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Views Over Time Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Eye className="h-5 w-5 text-blue-500" />
                                    <CardTitle className="text-lg">Views Over Time</CardTitle>
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {periodLabels[period]}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={300}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid
                                        strokeDasharray="3 3"
                                        stroke={isDark ? "#374151" : "#e5e7eb"}
                                        vertical={false}
                                    />
                                    <XAxis
                                        dataKey="date"
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
                                    <Area
                                        type="monotone"
                                        dataKey="views"
                                        stroke="#3b82f6"
                                        strokeWidth={2.5}
                                        fill="url(#viewsGradient)"
                                        dot={{ fill: "#3b82f6", strokeWidth: 0, r: 3 }}
                                        activeDot={{ r: 5, strokeWidth: 0 }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* Subscribers Growth Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Users className="h-5 w-5 text-green-500" />
                                    <CardTitle className="text-lg">Subscribers Growth</CardTitle>
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {periodLabels[period]}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={300}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="subscribersGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid
                                        strokeDasharray="3 3"
                                        stroke={isDark ? "#374151" : "#e5e7eb"}
                                        vertical={false}
                                    />
                                    <XAxis
                                        dataKey="date"
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
                                    <Area
                                        type="monotone"
                                        dataKey="subscribers"
                                        stroke="#10b981"
                                        strokeWidth={2.5}
                                        fill="url(#subscribersGradient)"
                                        dot={{ fill: "#10b981", strokeWidth: 0, r: 3 }}
                                        activeDot={{ r: 5, strokeWidth: 0 }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>

                {/* Quick Links */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <Link href="/dashboard/analytics/compare">
                        <Card className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer group">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 shadow-lg">
                                            <BarChart3 className="h-5 w-5 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Compare Channels</h3>
                                            <p className="text-sm text-muted-foreground">
                                                Side-by-side metrics
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>

                    <Link href="/dashboard/analytics/reports">
                        <Card className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer group">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
                                            <TrendingUp className="h-5 w-5 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Generate Reports</h3>
                                            <p className="text-sm text-muted-foreground">
                                                Export PDF & CSV
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>

                    <Link href="/dashboard/revenue">
                        <Card className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer group">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg">
                                            <DollarSign className="h-5 w-5 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Revenue Dashboard</h3>
                                            <p className="text-sm text-muted-foreground">
                                                Track earnings
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                </div>

                {/* AI Insights Panel */}
                <AIInsightsPanel
                    accountId={selectedAccount !== "all" ? selectedAccount : undefined}
                    limit={5}
                />
            </div>
        </DashboardLayout>
    );
}
