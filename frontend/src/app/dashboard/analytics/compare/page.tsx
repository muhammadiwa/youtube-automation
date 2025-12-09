"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
    TrendingDown,
    Calendar,
    BarChart3,
    Minus,
    X,
} from "lucide-react";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    Legend,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
} from "recharts";
import { useTheme } from "next-themes";
import analyticsApi, { ChannelMetrics } from "@/lib/api/analytics";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";
import { cn } from "@/lib/utils";

type Period = "7d" | "30d" | "90d" | "1y";

const CHART_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

export default function ChannelComparisonPage() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    const [period, setPeriod] = useState<Period>("30d");
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([]);
    const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([]);
    const [channelMetrics, setChannelMetrics] = useState<ChannelMetrics[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadAccounts();
    }, []);

    useEffect(() => {
        if (selectedAccountIds.length > 0) {
            loadComparison();
        } else {
            setChannelMetrics([]);
        }
    }, [selectedAccountIds, period]);

    const loadAccounts = async () => {
        const data = await accountsApi.getAccounts();
        setAccounts(data);
    };

    const loadComparison = async () => {
        if (selectedAccountIds.length === 0) return;

        setLoading(true);
        try {
            const metrics = await analyticsApi.compareChannels(selectedAccountIds);
            setChannelMetrics(metrics);
        } catch (error) {
            console.error("Failed to load comparison:", error);
            // Generate mock data for demo
            const mockMetrics: ChannelMetrics[] = selectedAccountIds.map((id, index) => {
                const account = accounts.find(a => a.id === id);
                return {
                    account_id: id,
                    channel_name: account?.channelTitle || `Channel ${index + 1}`,
                    views: Math.floor(Math.random() * 500000) + 50000,
                    subscribers: Math.floor(Math.random() * 100000) + 10000,
                    watch_time: Math.floor(Math.random() * 50000) + 5000,
                    revenue: Math.floor(Math.random() * 5000) + 500,
                    engagement_rate: Math.random() * 10 + 2,
                    top_videos: [],
                };
            });
            setChannelMetrics(mockMetrics);
        } finally {
            setLoading(false);
        }
    };

    const toggleChannel = (accountId: string) => {
        setSelectedAccountIds(prev => {
            if (prev.includes(accountId)) {
                return prev.filter(id => id !== accountId);
            }
            if (prev.length >= 5) {
                return prev; // Max 5 channels
            }
            return [...prev, accountId];
        });
    };

    const removeChannel = (accountId: string) => {
        setSelectedAccountIds(prev => prev.filter(id => id !== accountId));
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

    // Calculate variance from average
    const calculateVariance = (value: number, metric: keyof ChannelMetrics): { value: number; isPositive: boolean } => {
        if (channelMetrics.length < 2) return { value: 0, isPositive: true };

        const values = channelMetrics.map(m => m[metric] as number);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = ((value - avg) / avg) * 100;

        return {
            value: Math.abs(variance),
            isPositive: variance >= 0,
        };
    };

    // Prepare bar chart data
    const barChartData = [
        {
            metric: "Views",
            ...channelMetrics.reduce((acc, m, i) => ({
                ...acc,
                [m.channel_name]: m.views,
            }), {}),
        },
        {
            metric: "Subscribers",
            ...channelMetrics.reduce((acc, m, i) => ({
                ...acc,
                [m.channel_name]: m.subscribers,
            }), {}),
        },
        {
            metric: "Watch Time (h)",
            ...channelMetrics.reduce((acc, m, i) => ({
                ...acc,
                [m.channel_name]: Math.floor(m.watch_time / 60),
            }), {}),
        },
    ];

    // Prepare radar chart data (normalized to 100)
    const getRadarData = () => {
        if (channelMetrics.length === 0) return [];

        const maxViews = Math.max(...channelMetrics.map(m => m.views));
        const maxSubs = Math.max(...channelMetrics.map(m => m.subscribers));
        const maxWatchTime = Math.max(...channelMetrics.map(m => m.watch_time));
        const maxEngagement = Math.max(...channelMetrics.map(m => m.engagement_rate));
        const maxRevenue = Math.max(...channelMetrics.map(m => m.revenue));

        return [
            {
                metric: "Views",
                ...channelMetrics.reduce((acc, m) => ({
                    ...acc,
                    [m.channel_name]: maxViews > 0 ? (m.views / maxViews) * 100 : 0,
                }), {}),
            },
            {
                metric: "Subscribers",
                ...channelMetrics.reduce((acc, m) => ({
                    ...acc,
                    [m.channel_name]: maxSubs > 0 ? (m.subscribers / maxSubs) * 100 : 0,
                }), {}),
            },
            {
                metric: "Watch Time",
                ...channelMetrics.reduce((acc, m) => ({
                    ...acc,
                    [m.channel_name]: maxWatchTime > 0 ? (m.watch_time / maxWatchTime) * 100 : 0,
                }), {}),
            },
            {
                metric: "Engagement",
                ...channelMetrics.reduce((acc, m) => ({
                    ...acc,
                    [m.channel_name]: maxEngagement > 0 ? (m.engagement_rate / maxEngagement) * 100 : 0,
                }), {}),
            },
            {
                metric: "Revenue",
                ...channelMetrics.reduce((acc, m) => ({
                    ...acc,
                    [m.channel_name]: maxRevenue > 0 ? (m.revenue / maxRevenue) * 100 : 0,
                }), {}),
            },
        ];
    };

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
                            <span className="text-muted-foreground">{entry.name}:</span>
                            <span className="font-medium">{formatNumber(entry.value)}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    const selectedAccounts = accounts.filter(a => selectedAccountIds.includes(a.id));

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Analytics", href: "/dashboard/analytics" },
                { label: "Compare Channels" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Compare Channels</h1>
                        <p className="text-muted-foreground">
                            Select up to 5 channels to compare side-by-side
                        </p>
                    </div>
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

                {/* Channel Selection */}
                <Card className="border-0 bg-card shadow-lg">
                    <CardHeader className="pb-4">
                        <CardTitle className="text-lg">Select Channels</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            {accounts.map((account) => (
                                <div
                                    key={account.id}
                                    className={cn(
                                        "flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all",
                                        selectedAccountIds.includes(account.id)
                                            ? "border-primary bg-primary/5"
                                            : "hover:bg-muted/50",
                                        selectedAccountIds.length >= 5 && !selectedAccountIds.includes(account.id)
                                            ? "opacity-50 cursor-not-allowed"
                                            : ""
                                    )}
                                    onClick={() => toggleChannel(account.id)}
                                >
                                    <Checkbox
                                        checked={selectedAccountIds.includes(account.id)}
                                        disabled={selectedAccountIds.length >= 5 && !selectedAccountIds.includes(account.id)}
                                    />
                                    {account.thumbnailUrl && (
                                        <img
                                            src={account.thumbnailUrl}
                                            alt={account.channelTitle}
                                            className="h-8 w-8 rounded-full"
                                        />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium truncate">{account.channelTitle}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {formatNumber(account.subscriberCount)} subscribers
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {selectedAccountIds.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
                                <span className="text-sm text-muted-foreground">Selected:</span>
                                {selectedAccounts.map((account, index) => (
                                    <div
                                        key={account.id}
                                        className="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                                        style={{ backgroundColor: `${CHART_COLORS[index]}20`, color: CHART_COLORS[index] }}
                                    >
                                        {account.channelTitle}
                                        <button onClick={() => removeChannel(account.id)} className="ml-1 hover:opacity-70">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {selectedAccountIds.length > 0 && (
                    <>
                        {/* Metrics Comparison Table */}
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader className="pb-4">
                                <div className="flex items-center gap-2">
                                    <BarChart3 className="h-5 w-5 text-purple-500" />
                                    <CardTitle className="text-lg">Metrics Comparison</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="overflow-x-auto">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>Channel</TableHead>
                                                <TableHead className="text-right">Views</TableHead>
                                                <TableHead className="text-right">Subscribers</TableHead>
                                                <TableHead className="text-right">Watch Time</TableHead>
                                                <TableHead className="text-right">Engagement</TableHead>
                                                <TableHead className="text-right">Revenue</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {channelMetrics.map((metrics, index) => {
                                                const viewsVariance = calculateVariance(metrics.views, "views");
                                                const subsVariance = calculateVariance(metrics.subscribers, "subscribers");
                                                const watchTimeVariance = calculateVariance(metrics.watch_time, "watch_time");
                                                const engagementVariance = calculateVariance(metrics.engagement_rate, "engagement_rate");
                                                const revenueVariance = calculateVariance(metrics.revenue, "revenue");

                                                return (
                                                    <TableRow key={metrics.account_id}>
                                                        <TableCell>
                                                            <div className="flex items-center gap-2">
                                                                <div
                                                                    className="h-3 w-3 rounded-full"
                                                                    style={{ backgroundColor: CHART_COLORS[index] }}
                                                                />
                                                                <span className="font-medium">{metrics.channel_name}</span>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span>{formatNumber(metrics.views)}</span>
                                                                <VarianceIndicator variance={viewsVariance} />
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span>{formatNumber(metrics.subscribers)}</span>
                                                                <VarianceIndicator variance={subsVariance} />
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span>{formatWatchTime(metrics.watch_time)}</span>
                                                                <VarianceIndicator variance={watchTimeVariance} />
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span>{metrics.engagement_rate.toFixed(1)}%</span>
                                                                <VarianceIndicator variance={engagementVariance} />
                                                            </div>
                                                        </TableCell>
                                                        <TableCell className="text-right">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span>${formatNumber(metrics.revenue)}</span>
                                                                <VarianceIndicator variance={revenueVariance} />
                                                            </div>
                                                        </TableCell>
                                                    </TableRow>
                                                );
                                            })}
                                        </TableBody>
                                    </Table>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Charts */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Bar Chart */}
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader className="pb-4">
                                    <CardTitle className="text-lg">Metrics Comparison</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart data={barChartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "#374151" : "#e5e7eb"} vertical={false} />
                                            <XAxis dataKey="metric" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} />
                                            <YAxis stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => formatNumber(v)} />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Legend />
                                            {channelMetrics.map((m, i) => (
                                                <Bar key={m.account_id} dataKey={m.channel_name} fill={CHART_COLORS[i]} radius={[4, 4, 0, 0]} />
                                            ))}
                                        </BarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>

                            {/* Radar Chart */}
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader className="pb-4">
                                    <CardTitle className="text-lg">Performance Radar</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <RadarChart data={getRadarData()}>
                                            <PolarGrid stroke={isDark ? "#374151" : "#e5e7eb"} />
                                            <PolarAngleAxis dataKey="metric" stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={12} />
                                            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke={isDark ? "#6b7280" : "#9ca3af"} fontSize={10} />
                                            {channelMetrics.map((m, i) => (
                                                <Radar
                                                    key={m.account_id}
                                                    name={m.channel_name}
                                                    dataKey={m.channel_name}
                                                    stroke={CHART_COLORS[i]}
                                                    fill={CHART_COLORS[i]}
                                                    fillOpacity={0.2}
                                                />
                                            ))}
                                            <Legend />
                                            <Tooltip />
                                        </RadarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        </div>
                    </>
                )}

                {selectedAccountIds.length === 0 && (
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="py-12 text-center">
                            <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No Channels Selected</h3>
                            <p className="text-muted-foreground">
                                Select at least one channel above to start comparing metrics
                            </p>
                        </CardContent>
                    </Card>
                )}
            </div>
        </DashboardLayout>
    );
}

// Variance Indicator Component
function VarianceIndicator({ variance }: { variance: { value: number; isPositive: boolean } }) {
    if (variance.value < 1) {
        return <Minus className="h-3 w-3 text-muted-foreground" />;
    }

    return (
        <div className={cn(
            "flex items-center gap-0.5 text-xs",
            variance.isPositive ? "text-green-500" : "text-red-500"
        )}>
            {variance.isPositive ? (
                <TrendingUp className="h-3 w-3" />
            ) : (
                <TrendingDown className="h-3 w-3" />
            )}
            <span>{variance.value.toFixed(0)}%</span>
        </div>
    );
}
