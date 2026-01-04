"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard";
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
    Eye,
    Users,
    Clock,
    TrendingUp,
    Calendar,
    Play,
    Globe,
    ExternalLink,
    RefreshCw,
    Loader2,
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
    BarChart,
    Bar,
} from "recharts";
import { useTheme } from "next-themes";
import Link from "next/link";
import analyticsApi, { ChannelDetailedMetrics, TimeSeriesData, TopVideoData } from "@/lib/api/analytics";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";
import { useToast } from "@/hooks/use-toast";

type Period = "7d" | "30d" | "90d" | "1y";

// Helper function to calculate date range from period
function getDateRange(period: Period): { start_date: string; end_date: string; startLabel: string; endLabel: string } {
    const end = new Date();
    const start = new Date();

    switch (period) {
        case "7d":
            start.setDate(end.getDate() - 7);
            break;
        case "30d":
            start.setDate(end.getDate() - 30);
            break;
        case "90d":
            start.setDate(end.getDate() - 90);
            break;
        case "1y":
            start.setFullYear(end.getFullYear() - 1);
            break;
    }

    const formatDate = (d: Date) => d.toISOString().split('T')[0];
    const formatLabel = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

    return {
        start_date: formatDate(start),
        end_date: formatDate(end),
        startLabel: formatLabel(start),
        endLabel: formatLabel(end),
    };
}

// Traffic source colors
const TRAFFIC_SOURCE_COLORS: Record<string, string> = {
    "YT_SEARCH": "#3b82f6",
    "SUGGESTED": "#10b981",
    "EXT_URL": "#f59e0b",
    "BROWSE": "#8b5cf6",
    "NO_LINK_OTHER": "#ef4444",
    "PLAYLIST": "#06b6d4",
    "NOTIFICATION": "#ec4899",
    "END_SCREEN": "#84cc16",
};

// Traffic source display names
const TRAFFIC_SOURCE_NAMES: Record<string, string> = {
    "YT_SEARCH": "YouTube Search",
    "SUGGESTED": "Suggested Videos",
    "EXT_URL": "External",
    "BROWSE": "Browse Features",
    "NO_LINK_OTHER": "Direct/Other",
    "PLAYLIST": "Playlist",
    "NOTIFICATION": "Notifications",
    "END_SCREEN": "End Screen",
};

export default function ChannelAnalyticsPage() {
    const params = useParams();
    const accountId = params.id as string;
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const { addToast } = useToast();

    const [period, setPeriod] = useState<Period>("30d");
    const [account, setAccount] = useState<YouTubeAccount | null>(null);
    const [metrics, setMetrics] = useState<ChannelDetailedMetrics | null>(null);
    const [viewsData, setViewsData] = useState<TimeSeriesData[]>([]);
    const [subscribersData, setSubscribersData] = useState<TimeSeriesData[]>([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);

    useEffect(() => {
        loadData();
    }, [accountId, period]);

    // Calculate date range based on period
    const dateRange = useMemo(() => getDateRange(period), [period]);

    const loadData = async () => {
        setLoading(true);
        try {
            // Calculate granularity based on period for better chart display
            // 7d = daily (7 points), 30d = daily (30 points), 90d = weekly (~13 points), 1y = monthly (12 points)
            const granularity = period === "7d" ? "day" : period === "30d" ? "day" : period === "90d" ? "week" : "month";
            const { start_date, end_date } = getDateRange(period);

            const [accountData, channelMetrics, views, subscribers] = await Promise.all([
                accountsApi.getAccount(accountId),
                analyticsApi.getChannelDetailedMetrics(accountId, { period }).catch(() => null),
                analyticsApi.getViewsTimeSeries({
                    account_id: accountId,
                    start_date,
                    end_date,
                    granularity,
                }),
                analyticsApi.getSubscribersTimeSeries({
                    account_id: accountId,
                    start_date,
                    end_date,
                    granularity,
                }),
            ]);

            setAccount(accountData);

            // If no metrics from API, use account data as fallback
            if (channelMetrics) {
                // If metrics are all zero, use account stats
                if (channelMetrics.views === 0 && channelMetrics.subscribers === 0 && accountData) {
                    setMetrics({
                        ...channelMetrics,
                        views: accountData.viewCount || 0,
                        subscribers: accountData.subscriberCount || 0,
                    });
                } else {
                    setMetrics(channelMetrics);
                }
            } else if (accountData) {
                // Create fallback metrics from account data
                setMetrics({
                    account_id: accountId,
                    period: period,
                    start_date: "",
                    end_date: "",
                    subscribers: accountData.subscriberCount || 0,
                    subscriber_change: 0,
                    views: accountData.viewCount || 0,
                    views_change: 0,
                    watch_time: 0,
                    engagement_rate: 0,
                    traffic_sources: {},
                    demographics: { age_groups: {}, gender: { male: 0, female: 0 } },
                    top_videos: [],
                });
            }

            setViewsData(views);
            setSubscribersData(subscribers);
        } catch (error) {
            console.error("Failed to load channel analytics:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async () => {
        setSyncing(true);
        try {
            await analyticsApi.syncAccount(accountId);
            addToast({
                title: "Sync Started",
                description: "Analytics sync has been queued. Data will be updated shortly.",
                type: "success",
            });
            // Reload data after a short delay
            setTimeout(() => loadData(), 3000);
        } catch (error) {
            console.error("Failed to sync analytics:", error);
            addToast({
                title: "Sync Failed",
                description: "Failed to start analytics sync. Please try again.",
                type: "error",
            });
        } finally {
            setSyncing(false);
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

    const handleExport = async (format: "pdf" | "csv") => {
        try {
            await analyticsApi.generateReport({
                name: `${account?.channelTitle || "Channel"} Analytics Report`,
                type: "custom",
                metrics: ["views", "subscribers", "watch_time"],
                format,
                account_ids: [accountId],
            });
            addToast({
                title: "Report Generation Started",
                description: "You'll be notified when your report is ready.",
                type: "success",
            });
        } catch (error) {
            console.error("Failed to generate report:", error);
            addToast({
                title: "Failed to Generate Report",
                description: "Please try again later.",
                type: "error",
            });
        }
    };

    // Combine data for charts
    const chartData = viewsData.map((v, i) => {
        const dateObj = new Date(v.date);
        let dateLabel: string;

        // Format date label based on period
        if (period === "1y") {
            // Monthly: "Jan", "Feb", etc.
            dateLabel = dateObj.toLocaleDateString("en-US", { month: "short" });
        } else if (period === "90d") {
            // Weekly: "Jan 1", "Jan 8", etc.
            dateLabel = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        } else {
            // Daily: "Jan 1", "Jan 2", etc.
            dateLabel = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        }

        return {
            date: dateLabel,
            views: v.value,
            subscribers: subscribersData[i]?.value || 0,
        };
    });

    // Calculate XAxis interval based on data points for clean display
    const getXAxisInterval = () => {
        const dataLength = chartData.length;
        if (dataLength <= 7) return 0; // Show all
        if (dataLength <= 14) return 1; // Show every 2nd
        if (dataLength <= 31) return 4; // Show every 5th (for 30 days)
        return Math.floor(dataLength / 6); // Show ~6 labels
    };

    // Format date range for display
    const dateRangeLabel = `${dateRange.startLabel} - ${dateRange.endLabel}`;

    // Transform traffic sources for pie chart
    const trafficSourcesData = metrics?.traffic_sources
        ? Object.entries(metrics.traffic_sources).map(([key, value]) => ({
            name: TRAFFIC_SOURCE_NAMES[key] || key,
            value: value.views,
            color: TRAFFIC_SOURCE_COLORS[key] || "#6b7280",
        }))
        : [];

    // Calculate total views for percentage
    const totalTrafficViews = trafficSourcesData.reduce((sum, item) => sum + item.value, 0);
    const trafficSourcesWithPercent = trafficSourcesData.map(item => ({
        ...item,
        percent: totalTrafficViews > 0 ? Math.round((item.value / totalTrafficViews) * 100) : 0,
    }));

    // Transform demographics for bar chart
    const demographicsData = metrics?.demographics?.age_groups
        ? Object.entries(metrics.demographics.age_groups).map(([age, data]) => ({
            age,
            male: Math.round(data.male),
            female: Math.round(data.female),
        }))
        : [];

    // Top videos from API
    const topVideos: TopVideoData[] = metrics?.top_videos || [];

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

    const PieTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-popover border rounded-xl p-3 shadow-xl">
                    <div className="flex items-center gap-2 text-sm">
                        <div
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: payload[0].payload.color }}
                        />
                        <span className="font-medium">{payload[0].name}:</span>
                        <span>{formatNumber(payload[0].value)} views ({payload[0].payload.percent}%)</span>
                    </div>
                </div>
            );
        }
        return null;
    };

    const hasData = metrics && (metrics.views > 0 || metrics.subscribers > 0);

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Analytics", href: "/dashboard/analytics" },
                { label: account?.channelTitle || "Channel" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center gap-4">
                        {account?.thumbnailUrl && (
                            <img
                                src={account.thumbnailUrl}
                                alt={account.channelTitle}
                                className="h-12 w-12 rounded-full"
                            />
                        )}
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">
                                {account?.channelTitle || "Channel Analytics"}
                            </h1>
                            <p className="text-muted-foreground">
                                Detailed performance metrics
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        {/* Sync Button */}
                        <Button variant="outline" onClick={handleSync} disabled={syncing}>
                            {syncing ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <RefreshCw className="h-4 w-4 mr-2" />
                            )}
                            Sync
                        </Button>

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

                {/* No Data Message */}
                {!loading && !hasData && (
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-8 text-center">
                            <RefreshCw className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No Analytics Data Yet</h3>
                            <p className="text-muted-foreground mb-4">
                                Analytics data hasn't been synced for this channel yet. Click the Sync button to fetch the latest data from YouTube.
                            </p>
                            <Button onClick={handleSync} disabled={syncing}>
                                {syncing ? (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                ) : (
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                )}
                                Sync Now
                            </Button>
                        </CardContent>
                    </Card>
                )}

                {/* Key Metrics */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
                                    <Eye className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Views</p>
                                    <p className="text-2xl font-bold">{formatNumber(metrics?.views || 0)}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600 shadow-lg">
                                    <Users className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Subscribers</p>
                                    <p className="text-2xl font-bold">{formatNumber(metrics?.subscribers || 0)}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 shadow-lg">
                                    <Clock className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Watch Time</p>
                                    <p className="text-2xl font-bold">{formatWatchTime(metrics?.watch_time || 0)}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center gap-3">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 shadow-lg">
                                    <TrendingUp className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm text-muted-foreground">Engagement</p>
                                    <p className="text-2xl font-bold">{(metrics?.engagement_rate || 0).toFixed(1)}%</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Charts Row */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Views Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Eye className="h-5 w-5 text-blue-500" />
                                    <CardTitle className="text-lg">Views</CardTitle>
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {dateRangeLabel}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={250}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="viewsGradientChannel" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} vertical={false} />
                                    <XAxis dataKey="date" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} interval={getXAxisInterval()} />
                                    <YAxis stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Area type="monotone" dataKey="views" stroke="#3b82f6" strokeWidth={2} fill="url(#viewsGradientChannel)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* Subscribers Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Users className="h-5 w-5 text-green-500" />
                                    <CardTitle className="text-lg">Subscribers</CardTitle>
                                </div>
                                <span className="text-sm text-muted-foreground">
                                    {dateRangeLabel}
                                </span>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <ResponsiveContainer width="100%" height={250}>
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="subscribersGradientChannel" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} vertical={false} />
                                    <XAxis dataKey="date" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} interval={getXAxisInterval()} />
                                    <YAxis stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Area type="monotone" dataKey="subscribers" stroke="#10b981" strokeWidth={2} fill="url(#subscribersGradientChannel)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </div>

                {/* Traffic Sources & Demographics */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Traffic Sources Pie Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center gap-2">
                                <Globe className="h-5 w-5 text-purple-500" />
                                <CardTitle className="text-lg">Traffic Sources</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {trafficSourcesWithPercent.length > 0 ? (
                                <div className="flex items-center gap-8">
                                    <ResponsiveContainer width="50%" height={200}>
                                        <PieChart>
                                            <Pie
                                                data={trafficSourcesWithPercent}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={50}
                                                outerRadius={80}
                                                paddingAngle={2}
                                                dataKey="value"
                                            >
                                                {trafficSourcesWithPercent.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip content={<PieTooltip />} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="flex-1 space-y-2">
                                        {trafficSourcesWithPercent.slice(0, 5).map((source) => (
                                            <div key={source.name} className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-3 w-3 rounded-full" style={{ backgroundColor: source.color }} />
                                                    <span className="text-sm">{source.name}</span>
                                                </div>
                                                <span className="text-sm font-medium">{source.percent}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                                    No traffic source data available
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Demographics Bar Chart */}
                    <Card className="border-0 bg-card shadow-lg">
                        <CardHeader className="pb-4">
                            <div className="flex items-center gap-2">
                                <Users className="h-5 w-5 text-amber-500" />
                                <CardTitle className="text-lg">Demographics</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent>
                            {demographicsData.length > 0 ? (
                                <>
                                    <ResponsiveContainer width="100%" height={200}>
                                        <BarChart data={demographicsData} layout="vertical">
                                            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} horizontal={false} />
                                            <XAxis type="number" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} />
                                            <YAxis type="category" dataKey="age" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} width={50} />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Bar dataKey="male" name="Male" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                                            <Bar dataKey="female" name="Female" fill="#ec4899" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                    <div className="flex justify-center gap-6 mt-4">
                                        <div className="flex items-center gap-2">
                                            <div className="h-3 w-3 rounded-full bg-blue-500" />
                                            <span className="text-sm text-muted-foreground">Male</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="h-3 w-3 rounded-full bg-pink-500" />
                                            <span className="text-sm text-muted-foreground">Female</span>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                                    No demographics data available
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Top Videos Table */}
                <Card className="border-0 bg-card shadow-lg">
                    <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Play className="h-5 w-5 text-red-500" />
                                <CardTitle className="text-lg">Top Videos</CardTitle>
                            </div>
                            <Link href={`/dashboard/videos?account=${accountId}`}>
                                <Button variant="ghost" size="sm">
                                    View All
                                    <ExternalLink className="h-4 w-4 ml-2" />
                                </Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {topVideos.length > 0 ? (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Video</TableHead>
                                        <TableHead className="text-right">Views</TableHead>
                                        <TableHead className="text-right">Likes</TableHead>
                                        <TableHead className="text-right">Comments</TableHead>
                                        <TableHead className="text-right">Avg. Duration</TableHead>
                                        <TableHead className="text-right">Watch Time</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {topVideos.map((video) => (
                                        <TableRow key={video.video_id}>
                                            <TableCell className="font-medium max-w-[300px] truncate">
                                                {video.title}
                                            </TableCell>
                                            <TableCell className="text-right">{formatNumber(video.views)}</TableCell>
                                            <TableCell className="text-right">{formatNumber(video.likes)}</TableCell>
                                            <TableCell className="text-right">{formatNumber(video.comments)}</TableCell>
                                            <TableCell className="text-right">
                                                {Math.floor(video.average_view_duration / 60)}:{Math.floor(video.average_view_duration % 60).toString().padStart(2, "0")}
                                            </TableCell>
                                            <TableCell className="text-right">{formatWatchTime(video.watch_time_minutes)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        ) : (
                            <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                                No video data available. Click Sync to fetch data from YouTube.
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
