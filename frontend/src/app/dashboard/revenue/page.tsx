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
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    DollarSign,
    TrendingUp,
    Calendar,
    ArrowRight,
    Target,
    FileText,
    Play,
    Eye,
} from "lucide-react";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    PieChart,
    Pie,
    Cell,
    Legend,
} from "recharts";
import { useTheme } from "next-themes";
import Link from "next/link";
import analyticsApi, {
    RevenueBreakdown,
    RevenueTrend,
    TopEarningVideo,
} from "@/lib/api/analytics";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";

type Period = "7d" | "30d" | "90d" | "1y";

const COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6"];

export default function RevenuePage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [period, setPeriod] = useState<Period>("30d");
    const [selectedAccount, setSelectedAccount] = useState<string>("all");
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([]);
    const [revenue, setRevenue] = useState<RevenueBreakdown | null>(null);
    const [trends, setTrends] = useState<RevenueTrend[]>([]);
    const [topVideos, setTopVideos] = useState<TopEarningVideo[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAccounts();
    }, []);

    useEffect(() => {
        loadRevenueData();
    }, [period, selectedAccount]);

    const loadAccounts = async () => {
        const data = await accountsApi.getAccounts();
        setAccounts(data);
    };

    const loadRevenueData = async () => {
        setLoading(true);
        try {
            const params = {
                period,
                account_id: selectedAccount !== "all" ? selectedAccount : undefined,
            };

            const [revenueData, trendsData, videosData] = await Promise.all([
                analyticsApi.getRevenueOverview(params),
                analyticsApi.getMonthlyRevenueTrends({
                    account_id: params.account_id,
                    year: new Date().getFullYear(),
                }),
                analyticsApi.getTopEarningVideos({ ...params, limit: 5 }),
            ]);

            setRevenue(revenueData);
            setTrends(trendsData.length > 0 ? trendsData : generateMockTrends());
            setTopVideos(videosData.length > 0 ? videosData : generateMockVideos());
        } catch (error) {
            console.error("Failed to load revenue data:", error);
        } finally {
            setLoading(false);
        }
    };

    // Generate mock data for demo
    const generateMockTrends = (): RevenueTrend[] => {
        const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const currentMonth = new Date().getMonth();
        return months.slice(0, currentMonth + 1).map((month, i) => ({
            date: month,
            amount: Math.floor(Math.random() * 5000) + 1000,
            source: "total",
        }));
    };

    const generateMockVideos = (): TopEarningVideo[] => {
        return [
            {
                video_id: "1",
                title: "How to Build a YouTube Automation System",
                thumbnail_url: "/placeholder-video.jpg",
                revenue: 1250.50,
                views: 125000,
                cpm: 10.00,
                published_at: "2024-11-15",
            },
            {
                video_id: "2",
                title: "Complete Guide to Live Streaming",
                thumbnail_url: "/placeholder-video.jpg",
                revenue: 980.25,
                views: 98000,
                cpm: 10.00,
                published_at: "2024-11-10",
            },
            {
                video_id: "3",
                title: "AI Tools for Content Creators",
                thumbnail_url: "/placeholder-video.jpg",
                revenue: 750.00,
                views: 75000,
                cpm: 10.00,
                published_at: "2024-11-05",
            },
            {
                video_id: "4",
                title: "Monetization Strategies 2024",
                thumbnail_url: "/placeholder-video.jpg",
                revenue: 620.75,
                views: 62000,
                cpm: 10.01,
                published_at: "2024-10-28",
            },
            {
                video_id: "5",
                title: "Growing Your Channel Fast",
                thumbnail_url: "/placeholder-video.jpg",
                revenue: 450.00,
                views: 45000,
                cpm: 10.00,
                published_at: "2024-10-20",
            },
        ];
    };

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
        }).format(amount);
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    // Prepare pie chart data
    const pieData = revenue ? [
        { name: "Ads", value: revenue.ads, color: COLORS[0] },
        { name: "Memberships", value: revenue.memberships, color: COLORS[1] },
        { name: "Super Chat", value: revenue.super_chat, color: COLORS[2] },
        { name: "Super Stickers", value: revenue.super_stickers, color: COLORS[3] },
        { name: "Merchandise", value: revenue.merchandise, color: COLORS[4] },
        { name: "YT Premium", value: revenue.youtube_premium, color: COLORS[5] },
    ].filter(item => item.value > 0) : [];

    // Prepare line chart data
    const chartData = trends.map(t => ({
        date: t.date,
        revenue: t.amount,
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
                            <span className="font-medium">{formatCurrency(entry.value)}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    const PieTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0];
            return (
                <div className="bg-popover border rounded-xl p-3 shadow-xl">
                    <div className="flex items-center gap-2 text-sm">
                        <div
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: data.payload.color }}
                        />
                        <span className="font-medium">{data.name}:</span>
                        <span>{formatCurrency(data.value)}</span>
                    </div>
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
                { label: "Revenue" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Revenue Dashboard</h1>
                        <p className="text-muted-foreground">
                            Track earnings across all your monetized channels
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
                    </div>
                </div>

                {/* Total Earnings Card */}
                <Card className="border-0 bg-gradient-to-br from-green-500 to-emerald-600 text-white shadow-xl">
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-green-100 text-sm font-medium">Total Earnings</p>
                                <p className="text-4xl font-bold mt-1">
                                    {formatCurrency(revenue?.total || 0)}
                                </p>
                                <p className="text-green-100 text-sm mt-2">
                                    {periodLabels[period]}
                                </p>
                            </div>
                            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 backdrop-blur">
                                <DollarSign className="h-8 w-8" />
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Revenue Breakdown Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                    <OverviewCard
                        title="Ad Revenue"
                        value={formatCurrency(revenue?.ads || 0)}
                        icon={Play}
                        gradient="from-red-500 to-red-600"
                    />
                    <OverviewCard
                        title="Memberships"
                        value={formatCurrency(revenue?.memberships || 0)}
                        icon={DollarSign}
                        gradient="from-orange-500 to-orange-600"
                    />
                    <OverviewCard
                        title="Super Chat"
                        value={formatCurrency(revenue?.super_chat || 0)}
                        icon={DollarSign}
                        gradient="from-yellow-500 to-yellow-600"
                    />
                    <OverviewCard
                        title="Super Stickers"
                        value={formatCurrency(revenue?.super_stickers || 0)}
                        icon={DollarSign}
                        gradient="from-green-500 to-green-600"
                    />
                    <OverviewCard
                        title="Merchandise"
                        value={formatCurrency(revenue?.merchandise || 0)}
                        icon={DollarSign}
                        gradient="from-blue-500 to-blue-600"
                    />
                    <OverviewCard
                        title="YT Premium"
                        value={formatCurrency(revenue?.youtube_premium || 0)}
                        icon={DollarSign}
                        gradient="from-purple-500 to-purple-600"
                    />
                </div>

                {/* Charts Section */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Revenue by Source Pie Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center gap-2">
                                <DollarSign className="h-5 w-5 text-green-500" />
                                <CardTitle className="text-lg">Revenue by Source</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {pieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={2}
                                            dataKey="value"
                                        >
                                            {pieData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<PieTooltip />} />
                                        <Legend
                                            verticalAlign="bottom"
                                            height={36}
                                            formatter={(value) => (
                                                <span className="text-sm text-foreground">{value}</span>
                                            )}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                                    No revenue data available
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Monthly Trend Line Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <TrendingUp className="h-5 w-5 text-blue-500" />
                                    <CardTitle className="text-lg">Monthly Trend</CardTitle>
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {new Date().getFullYear()}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={300}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
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
                                        tickFormatter={(value) => `$${formatNumber(value)}`}
                                    />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Area
                                        type="monotone"
                                        dataKey="revenue"
                                        stroke="#10b981"
                                        strokeWidth={2.5}
                                        fill="url(#revenueGradient)"
                                        dot={{ fill: "#10b981", strokeWidth: 0, r: 3 }}
                                        activeDot={{ r: 5, strokeWidth: 0 }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>

                {/* Top Earning Videos Table */}
                <Card className="border-0 bg-card shadow-lg">
                    <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Play className="h-5 w-5 text-red-500" />
                                <CardTitle className="text-lg">Top Earning Videos</CardTitle>
                            </div>
                            <Link href="/dashboard/videos">
                                <Button variant="ghost" size="sm" className="text-muted-foreground">
                                    View All
                                    <ArrowRight className="h-4 w-4 ml-1" />
                                </Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Video</TableHead>
                                    <TableHead className="text-right">Views</TableHead>
                                    <TableHead className="text-right">CPM</TableHead>
                                    <TableHead className="text-right">Revenue</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {topVideos.map((video) => (
                                    <TableRow key={video.video_id}>
                                        <TableCell>
                                            <div className="flex items-center gap-3">
                                                <div className="h-10 w-16 rounded bg-muted flex items-center justify-center">
                                                    <Play className="h-4 w-4 text-muted-foreground" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium truncate">{video.title}</p>
                                                    <p className="text-xs text-muted-foreground">
                                                        {new Date(video.published_at).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex items-center justify-end gap-1">
                                                <Eye className="h-3 w-3 text-muted-foreground" />
                                                {formatNumber(video.views)}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {formatCurrency(video.cpm)}
                                        </TableCell>
                                        <TableCell className="text-right font-medium text-green-600">
                                            {formatCurrency(video.revenue)}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>

                {/* Quick Links */}
                <div className="grid gap-4 sm:grid-cols-2">
                    <Link href="/dashboard/revenue/goals">
                        <Card className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer group">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg">
                                            <Target className="h-5 w-5 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Revenue Goals</h3>
                                            <p className="text-sm text-muted-foreground">
                                                Set and track your earnings targets
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>

                    <Link href="/dashboard/revenue/tax">
                        <Card className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer group">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
                                            <FileText className="h-5 w-5 text-white" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Tax Reports</h3>
                                            <p className="text-sm text-muted-foreground">
                                                Generate tax-relevant summaries
                                            </p>
                                        </div>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                                </div>
                            </CardContent>
                        </Card>
                    </Link>
                </div>
            </div>
        </DashboardLayout>
    );
}
