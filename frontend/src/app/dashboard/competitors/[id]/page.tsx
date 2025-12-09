"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import competitorsApi, {
    Competitor,
    CompetitorMetrics,
    CompetitorVideo,
    CompetitorComparison,
    CompetitorRecommendation,
} from "@/lib/api/competitors";
import {
    ArrowLeft,
    Users,
    Video,
    Eye,
    TrendingUp,
    TrendingDown,
    Download,
    ExternalLink,
    RefreshCw,
    Lightbulb,
    Calendar,
    ThumbsUp,
    MessageSquare,
    Clock,
    Sparkles,
    X,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    BarChart,
    Bar,
    Legend,
} from "recharts";

type Period = "7d" | "30d" | "90d";

export default function CompetitorDetailPage() {
    const params = useParams();
    const router = useRouter();
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const competitorId = params.id as string;

    const [competitor, setCompetitor] = useState<Competitor | null>(null);
    const [metrics, setMetrics] = useState<CompetitorMetrics[]>([]);
    const [comparison, setComparison] = useState<CompetitorComparison | null>(null);
    const [videos, setVideos] = useState<CompetitorVideo[]>([]);
    const [recommendations, setRecommendations] = useState<CompetitorRecommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState<Period>("30d");
    const [syncing, setSyncing] = useState(false);
    const [exporting, setExporting] = useState(false);


    useEffect(() => {
        loadCompetitorData();
    }, [competitorId]);

    useEffect(() => {
        loadMetrics();
    }, [competitorId, period]);

    const loadCompetitorData = async () => {
        try {
            setLoading(true);
            const [competitorData, comparisonData, videosData, recommendationsData] = await Promise.all([
                competitorsApi.getCompetitor(competitorId),
                competitorsApi.getComparison([competitorId]),
                competitorsApi.getCompetitorVideos(competitorId, { page_size: 10, sort_by: "published_at" }),
                competitorsApi.getRecommendations(competitorId),
            ]);
            setCompetitor(competitorData);
            setComparison(comparisonData);
            setVideos(videosData.items || []);
            setRecommendations(recommendationsData || []);
        } catch (error) {
            console.error("Failed to load competitor data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadMetrics = async () => {
        try {
            const endDate = new Date();
            const startDate = new Date();
            if (period === "7d") startDate.setDate(startDate.getDate() - 7);
            else if (period === "30d") startDate.setDate(startDate.getDate() - 30);
            else startDate.setDate(startDate.getDate() - 90);

            const metricsData = await competitorsApi.getMetrics(competitorId, {
                start_date: startDate.toISOString().split("T")[0],
                end_date: endDate.toISOString().split("T")[0],
            });
            setMetrics(metricsData || []);
        } catch (error) {
            console.error("Failed to load metrics:", error);
        }
    };

    const handleSync = async () => {
        try {
            setSyncing(true);
            await competitorsApi.syncCompetitor(competitorId);
            await loadCompetitorData();
        } catch (error) {
            console.error("Failed to sync competitor:", error);
        } finally {
            setSyncing(false);
        }
    };

    const handleExport = async () => {
        try {
            setExporting(true);
            const result = await competitorsApi.exportAnalysis([competitorId], "pdf");
            if (result.download_url) {
                window.open(result.download_url, "_blank");
            }
        } catch (error) {
            console.error("Failed to export analysis:", error);
        } finally {
            setExporting(false);
        }
    };

    const handleDismissRecommendation = async (recommendationId: string) => {
        try {
            await competitorsApi.dismissRecommendation(recommendationId);
            setRecommendations((prev) => prev.filter((r) => r.id !== recommendationId));
        } catch (error) {
            console.error("Failed to dismiss recommendation:", error);
        }
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    const formatDuration = (duration: string): string => {
        return duration || "0:00";
    };

    const getVarianceColor = (variance: number): string => {
        if (variance > 0) return "text-green-500";
        if (variance < 0) return "text-red-500";
        return "text-muted-foreground";
    };

    const getPriorityColor = (priority: string): string => {
        switch (priority) {
            case "high":
                return "bg-red-500/10 text-red-500 border-red-500/20";
            case "medium":
                return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
            default:
                return "bg-blue-500/10 text-blue-500 border-blue-500/20";
        }
    };

    const getRecommendationIcon = (type: string) => {
        switch (type) {
            case "content":
                return Video;
            case "timing":
                return Clock;
            case "tags":
                return Sparkles;
            case "thumbnail":
                return Eye;
            case "engagement":
                return MessageSquare;
            default:
                return Lightbulb;
        }
    };


    // Chart data
    const chartData = metrics.map((m) => ({
        date: new Date(m.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        subscribers: m.subscribers,
        views: m.views,
        engagement: m.engagement_rate,
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
                            <span className="font-medium">
                                {entry.name === "engagement"
                                    ? `${entry.value.toFixed(2)}%`
                                    : formatNumber(entry.value)}
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Competitors", href: "/dashboard/competitors" },
                    { label: "Loading..." },
                ]}
            >
                <div className="space-y-6">
                    <Skeleton className="h-32" />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[1, 2, 3].map((i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                    <Skeleton className="h-96" />
                </div>
            </DashboardLayout>
        );
    }

    if (!competitor) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Competitors", href: "/dashboard/competitors" },
                    { label: "Not Found" },
                ]}
            >
                <div className="text-center py-12">
                    <h3 className="text-lg font-semibold mb-2">Competitor not found</h3>
                    <p className="text-muted-foreground mb-4">
                        The competitor you're looking for doesn't exist or has been removed.
                    </p>
                    <Button onClick={() => router.push("/dashboard/competitors")}>
                        Back to Competitors
                    </Button>
                </div>
            </DashboardLayout>
        );
    }

    const competitorStats = comparison?.competitors.find((c) => c.competitor_id === competitorId);

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Competitors", href: "/dashboard/competitors" },
                { label: competitor.channel_name },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push("/dashboard/competitors")}
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <Avatar className="h-16 w-16">
                            <AvatarImage src={competitor.thumbnail_url} alt={competitor.channel_name} />
                            <AvatarFallback>
                                {competitor.channel_name.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">
                                {competitor.channel_name}
                            </h1>
                            <p className="text-muted-foreground">
                                Tracking since {new Date(competitor.created_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={handleSync} disabled={syncing}>
                            <RefreshCw className={cn("mr-2 h-4 w-4", syncing && "animate-spin")} />
                            Sync
                        </Button>
                        <Button variant="outline" onClick={handleExport} disabled={exporting}>
                            <Download className="mr-2 h-4 w-4" />
                            {exporting ? "Exporting..." : "Export"}
                        </Button>
                        <Button variant="outline" asChild>
                            <a href={competitor.channel_url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="mr-2 h-4 w-4" />
                                View Channel
                            </a>
                        </Button>
                    </div>
                </div>


                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Subscribers</p>
                                    <p className="text-2xl font-bold">
                                        {formatNumber(competitor.subscriber_count)}
                                    </p>
                                    {competitorStats?.variance && (
                                        <div className={cn("flex items-center gap-1 text-sm", getVarianceColor(competitorStats.variance.subscribers))}>
                                            {competitorStats.variance.subscribers > 0 ? (
                                                <TrendingUp className="h-4 w-4" />
                                            ) : (
                                                <TrendingDown className="h-4 w-4" />
                                            )}
                                            <span>
                                                {Math.abs(competitorStats.variance.subscribers).toFixed(1)}% vs you
                                            </span>
                                        </div>
                                    )}
                                </div>
                                <div className="h-12 w-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                                    <Users className="h-6 w-6 text-blue-500" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Videos</p>
                                    <p className="text-2xl font-bold">
                                        {formatNumber(competitor.video_count)}
                                    </p>
                                </div>
                                <div className="h-12 w-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                                    <Video className="h-6 w-6 text-green-500" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Views</p>
                                    <p className="text-2xl font-bold">
                                        {formatNumber(competitor.view_count)}
                                    </p>
                                    {competitorStats?.variance && (
                                        <div className={cn("flex items-center gap-1 text-sm", getVarianceColor(competitorStats.variance.views))}>
                                            {competitorStats.variance.views > 0 ? (
                                                <TrendingUp className="h-4 w-4" />
                                            ) : (
                                                <TrendingDown className="h-4 w-4" />
                                            )}
                                            <span>
                                                {Math.abs(competitorStats.variance.views).toFixed(1)}% vs you
                                            </span>
                                        </div>
                                    )}
                                </div>
                                <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                                    <Eye className="h-6 w-6 text-purple-500" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Tabs */}
                <Tabs defaultValue="metrics" className="space-y-6">
                    <div className="flex items-center justify-between">
                        <TabsList>
                            <TabsTrigger value="metrics">Metrics</TabsTrigger>
                            <TabsTrigger value="videos">Recent Videos</TabsTrigger>
                            <TabsTrigger value="recommendations">AI Recommendations</TabsTrigger>
                        </TabsList>
                        <Select value={period} onValueChange={(v) => setPeriod(v as Period)}>
                            <SelectTrigger className="w-[150px]">
                                <Calendar className="h-4 w-4 mr-2" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="7d">Last 7 days</SelectItem>
                                <SelectItem value="30d">Last 30 days</SelectItem>
                                <SelectItem value="90d">Last 90 days</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>


                    {/* Metrics Tab */}
                    <TabsContent value="metrics" className="space-y-6">
                        {/* Comparison Chart */}
                        {comparison && (
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader>
                                    <CardTitle>Channel Comparison</CardTitle>
                                    <CardDescription>
                                        Compare your channel metrics with {competitor.channel_name}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart
                                            data={[
                                                {
                                                    metric: "Subscribers",
                                                    you: comparison.your_channel.subscribers,
                                                    competitor: competitorStats?.subscribers || 0,
                                                },
                                                {
                                                    metric: "Videos",
                                                    you: comparison.your_channel.videos,
                                                    competitor: competitorStats?.videos || 0,
                                                },
                                                {
                                                    metric: "Engagement %",
                                                    you: comparison.your_channel.engagement_rate,
                                                    competitor: competitorStats?.engagement_rate || 0,
                                                },
                                            ]}
                                            layout="vertical"
                                        >
                                            <CartesianGrid
                                                strokeDasharray="3 3"
                                                stroke={isDark ? "#374151" : "#e5e7eb"}
                                                horizontal={false}
                                            />
                                            <XAxis
                                                type="number"
                                                stroke={isDark ? "#6b7280" : "#9ca3af"}
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                            />
                                            <YAxis
                                                type="category"
                                                dataKey="metric"
                                                stroke={isDark ? "#6b7280" : "#9ca3af"}
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                                width={100}
                                            />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Legend />
                                            <Bar dataKey="you" name="Your Channel" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                                            <Bar dataKey="competitor" name={competitor.channel_name} fill="#ef4444" radius={[0, 4, 4, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        )}

                        {/* Growth Chart */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Users className="h-5 w-5 text-blue-500" />
                                        <CardTitle className="text-lg">Subscriber Growth</CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {chartData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={250}>
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="subscribersGradient" x1="0" y1="0" x2="0" y2="1">
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
                                                    dataKey="subscribers"
                                                    stroke="#3b82f6"
                                                    strokeWidth={2.5}
                                                    fill="url(#subscribersGradient)"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                                            No data available for this period
                                        </div>
                                    )}
                                </CardContent>
                            </Card>

                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Eye className="h-5 w-5 text-purple-500" />
                                        <CardTitle className="text-lg">Views Over Time</CardTitle>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    {chartData.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={250}>
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                                                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
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
                                                    stroke="#a855f7"
                                                    strokeWidth={2.5}
                                                    fill="url(#viewsGradient)"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                                            No data available for this period
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>


                    {/* Videos Tab */}
                    <TabsContent value="videos" className="space-y-6">
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <CardTitle>Recent Videos</CardTitle>
                                <CardDescription>
                                    Latest content from {competitor.channel_name}
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {videos.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        No videos found
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {videos.map((video) => (
                                            <div
                                                key={video.id}
                                                className="flex gap-4 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                                            >
                                                <div className="relative w-40 h-24 rounded-lg overflow-hidden flex-shrink-0">
                                                    {video.thumbnail_url ? (
                                                        <img
                                                            src={video.thumbnail_url}
                                                            alt={video.title}
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <div className="w-full h-full bg-muted flex items-center justify-center">
                                                            <Video className="h-8 w-8 text-muted-foreground" />
                                                        </div>
                                                    )}
                                                    <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
                                                        {formatDuration(video.duration)}
                                                    </div>
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <h4 className="font-medium line-clamp-2 mb-2">
                                                        {video.title}
                                                    </h4>
                                                    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                                                        <div className="flex items-center gap-1">
                                                            <Eye className="h-4 w-4" />
                                                            {formatNumber(video.view_count)}
                                                        </div>
                                                        <div className="flex items-center gap-1">
                                                            <ThumbsUp className="h-4 w-4" />
                                                            {formatNumber(video.like_count)}
                                                        </div>
                                                        <div className="flex items-center gap-1">
                                                            <MessageSquare className="h-4 w-4" />
                                                            {formatNumber(video.comment_count)}
                                                        </div>
                                                        <div className="flex items-center gap-1">
                                                            <Calendar className="h-4 w-4" />
                                                            {new Date(video.published_at).toLocaleDateString()}
                                                        </div>
                                                    </div>
                                                </div>
                                                <Button variant="ghost" size="icon" asChild>
                                                    <a
                                                        href={`https://youtube.com/watch?v=${video.video_id}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                    >
                                                        <ExternalLink className="h-4 w-4" />
                                                    </a>
                                                </Button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Recommendations Tab */}
                    <TabsContent value="recommendations" className="space-y-6">
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <Sparkles className="h-5 w-5 text-amber-500" />
                                    <CardTitle>AI Recommendations</CardTitle>
                                </div>
                                <CardDescription>
                                    Actionable insights based on competitor analysis
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {recommendations.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <Lightbulb className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>No recommendations available yet</p>
                                        <p className="text-sm">
                                            Check back after more data has been collected
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {recommendations.map((rec) => {
                                            const Icon = getRecommendationIcon(rec.type);
                                            return (
                                                <div
                                                    key={rec.id}
                                                    className="flex gap-4 p-4 rounded-lg border bg-card"
                                                >
                                                    <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                                                        <Icon className="h-5 w-5 text-amber-500" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <h4 className="font-medium">{rec.title}</h4>
                                                            <Badge
                                                                variant="outline"
                                                                className={getPriorityColor(rec.priority)}
                                                            >
                                                                {rec.priority}
                                                            </Badge>
                                                        </div>
                                                        <p className="text-sm text-muted-foreground">
                                                            {rec.description}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground mt-2">
                                                            {new Date(rec.created_at).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="flex-shrink-0"
                                                        onClick={() => handleDismissRecommendation(rec.id)}
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
