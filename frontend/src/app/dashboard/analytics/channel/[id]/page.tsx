"use client";

import { useState, useEffect } from "react";
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
    Download,
    Play,
    Globe,
    Smartphone,
    Monitor,
    ExternalLink,
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
import analyticsApi, { ChannelMetrics, TimeSeriesData, VideoMetrics } from "@/lib/api/analytics";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";

type Period = "7d" | "30d" | "90d" | "1y";

// Mock traffic sources data
const trafficSourcesData = [
    { name: "YouTube Search", value: 35, color: "#3b82f6" },
    { name: "Suggested Videos", value: 28, color: "#10b981" },
    { name: "External", value: 15, color: "#f59e0b" },
    { name: "Browse Features", value: 12, color: "#8b5cf6" },
    { name: "Direct", value: 10, color: "#ef4444" },
];

// Mock demographics data
const demographicsData = [
    { age: "13-17", male: 8, female: 5 },
    { age: "18-24", male: 25, female: 18 },
    { age: "25-34", male: 30, female: 22 },
    { age: "35-44", male: 15, female: 12 },
    { age: "45-54", male: 8, female: 6 },
    { age: "55+", male: 5, female: 4 },
];

// Mock device data
const deviceData = [
    { name: "Mobile", value: 55, icon: Smartphone, color: "#3b82f6" },
    { name: "Desktop", value: 35, icon: Monitor, color: "#10b981" },
    { name: "TV", value: 10, icon: Monitor, color: "#8b5cf6" },
];

export default function ChannelAnalyticsPage() {
    const params = useParams();
    const accountId = params.id as string;
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [period, setPeriod] = useState<Period>("30d");
    const [account, setAccount] = useState<YouTubeAccount | null>(null);
    const [metrics, setMetrics] = useState<ChannelMetrics | null>(null);
    const [viewsData, setViewsData] = useState<TimeSeriesData[]>([]);
    const [subscribersData, setSubscribersData] = useState<TimeSeriesData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [accountId, period]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [accountData, channelMetrics, views, subscribers] = await Promise.all([
                accountsApi.getAccount(accountId),
                analyticsApi.getChannelMetrics(accountId),
                analyticsApi.getViewsTimeSeries({
                    account_id: accountId,
                    granularity: period === "7d" ? "day" : period === "30d" ? "day" : "week",
                }),
                analyticsApi.getSubscribersTimeSeries({
                    account_id: accountId,
                    granularity: period === "7d" ? "day" : period === "30d" ? "day" : "week",
                }),
            ]);

            setAccount(accountData);
            setMetrics(channelMetrics);
            setViewsData(views);
            setSubscribersData(subscribers);
        } catch (error) {
            console.error("Failed to load channel analytics:", error);
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

    const handleExport = async (format: "pdf" | "csv") => {
        try {
            await analyticsApi.generateReport({
                name: `${account?.channelTitle || "Channel"} Analytics Report`,
                type: "custom",
                metrics: ["views", "subscribers", "watch_time", "revenue"],
                format,
                account_ids: [accountId],
            });
            // In a real app, this would trigger a download
            alert(`Report generation started. You'll be notified when it's ready.`);
        } catch (error) {
            console.error("Failed to generate report:", error);
        }
    };

    // Combine data for charts
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
                        <span>{payload[0].value}%</span>
                    </div>
                </div>
            );
        }
        return null;
    };

    // Mock top videos if not available from API
    const topVideos: VideoMetrics[] = metrics?.top_videos || [
        { video_id: "1", title: "How to Get Started with YouTube", views: 125000, likes: 8500, comments: 450, watch_time: 45000, average_view_duration: 360, click_through_rate: 8.5 },
        { video_id: "2", title: "10 Tips for Better Thumbnails", views: 98000, likes: 6200, comments: 320, watch_time: 35000, average_view_duration: 280, click_through_rate: 7.2 },
        { video_id: "3", title: "YouTube Algorithm Explained", views: 87000, likes: 5800, comments: 280, watch_time: 32000, average_view_duration: 420, click_through_rate: 9.1 },
        { video_id: "4", title: "Best Camera Settings for YouTube", views: 76000, likes: 4900, comments: 210, watch_time: 28000, average_view_duration: 310, click_through_rate: 6.8 },
        { video_id: "5", title: "How I Edit My Videos", views: 65000, likes: 4200, comments: 180, watch_time: 24000, average_view_duration: 290, click_through_rate: 7.5 },
    ];

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

                        {/* Export Buttons */}
                        <Button variant="outline" onClick={() => handleExport("csv")}>
                            <Download className="h-4 w-4 mr-2" />
                            CSV
                        </Button>
                        <Button variant="outline" onClick={() => handleExport("pdf")}>
                            <Download className="h-4 w-4 mr-2" />
                            PDF
                        </Button>
                    </div>
                </div>

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
                            <div className="flex items-center gap-2">
                                <Eye className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-lg">Views</CardTitle>
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
                                    <XAxis dataKey="date" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} />
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
                            <div className="flex items-center gap-2">
                                <Users className="h-5 w-5 text-green-500" />
                                <CardTitle className="text-lg">Subscribers</CardTitle>
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
                                    <XAxis dataKey="date" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} />
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
                            <div className="flex items-center gap-8">
                                <ResponsiveContainer width="50%" height={200}>
                                    <PieChart>
                                        <Pie
                                            data={trafficSourcesData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={50}
                                            outerRadius={80}
                                            paddingAngle={2}
                                            dataKey="value"
                                        >
                                            {trafficSourcesData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip content={<PieTooltip />} />
                                    </PieChart>
                                </ResponsiveContainer>
                                <div className="flex-1 space-y-2">
                                    {trafficSourcesData.map((source) => (
                                        <div key={source.name} className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className="h-3 w-3 rounded-full" style={{ backgroundColor: source.color }} />
                                                <span className="text-sm">{source.name}</span>
                                            </div>
                                            <span className="text-sm font-medium">{source.value}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
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
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Video</TableHead>
                                    <TableHead className="text-right">Views</TableHead>
                                    <TableHead className="text-right">Likes</TableHead>
                                    <TableHead className="text-right">Comments</TableHead>
                                    <TableHead className="text-right">Avg. Duration</TableHead>
                                    <TableHead className="text-right">CTR</TableHead>
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
                                            {Math.floor(video.average_view_duration / 60)}:{(video.average_view_duration % 60).toString().padStart(2, "0")}
                                        </TableCell>
                                        <TableCell className="text-right">{video.click_through_rate.toFixed(1)}%</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
