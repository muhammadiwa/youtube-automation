"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
} from "recharts";
import { useTheme } from "next-themes";
import { TrendingUp, BarChart3 } from "lucide-react";
import { analyticsApi } from "@/lib/api/analytics";

interface ChartData {
    date: string;
    views: number;
    subscribers: number;
}

export function PerformanceChart() {
    const { theme } = useTheme();
    const isDark = theme === "dark";
    const [chartData, setChartData] = useState<ChartData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadChartData = async () => {
            try {
                // Fetch views and subscribers time series data (last 30 days)
                const endDate = new Date().toISOString().split("T")[0];
                const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];

                const [viewsData, subscribersData] = await Promise.all([
                    analyticsApi.getViewsTimeSeries({ start_date: startDate, end_date: endDate }),
                    analyticsApi.getSubscribersTimeSeries({ start_date: startDate, end_date: endDate }),
                ]);

                // Combine the data
                const combinedData: ChartData[] = [];
                const viewsMap = new Map(viewsData.map(v => [v.date, v.value]));
                const subscribersMap = new Map(subscribersData.map(s => [s.date, s.value]));

                // Get all unique dates
                const allDates = new Set([
                    ...viewsData.map(v => v.date),
                    ...subscribersData.map(s => s.date)
                ]);

                // Sort dates and create combined data
                Array.from(allDates).sort().forEach(date => {
                    const dateObj = new Date(date);
                    const formattedDate = dateObj.toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric"
                    });
                    combinedData.push({
                        date: formattedDate,
                        views: viewsMap.get(date) || 0,
                        subscribers: subscribersMap.get(date) || 0,
                    });
                });

                setChartData(combinedData);
            } catch (error) {
                console.error("Failed to load chart data:", error);
            } finally {
                setLoading(false);
            }
        };
        loadChartData();
    }, []);

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
                            <span className="font-medium">{entry.value.toLocaleString()}</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <Card className="border-0 bg-card shadow-lg h-full">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-500" />
                        <CardTitle className="text-lg">Performance Overview</CardTitle>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full bg-gradient-to-r from-blue-500 to-blue-600" />
                            <span className="text-muted-foreground">Views</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="h-3 w-3 rounded-full bg-gradient-to-r from-green-500 to-green-600" />
                            <span className="text-muted-foreground">Subscribers</span>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="h-[350px] flex items-center justify-center">
                        <div className="text-center">
                            <Skeleton className="h-[300px] w-full" />
                        </div>
                    </div>
                ) : chartData.length === 0 ? (
                    <div className="h-[350px] flex flex-col items-center justify-center text-center">
                        <BarChart3 className="h-12 w-12 text-muted-foreground/50 mb-4" />
                        <p className="text-sm text-muted-foreground">No performance data available</p>
                        <p className="text-xs text-muted-foreground/70 mt-1">Connect a YouTube account to see analytics</p>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height={350}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
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
                                dy={10}
                            />
                            <YAxis
                                stroke={isDark ? "#6b7280" : "#9ca3af"}
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                dx={-10}
                                tickFormatter={(value) => value >= 1000 ? `${value / 1000}k` : value}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey="views"
                                stroke="#3b82f6"
                                strokeWidth={2.5}
                                fill="url(#viewsGradient)"
                                dot={{ fill: "#3b82f6", strokeWidth: 0, r: 4 }}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                            />
                            <Area
                                type="monotone"
                                dataKey="subscribers"
                                stroke="#10b981"
                                strokeWidth={2.5}
                                fill="url(#subscribersGradient)"
                                dot={{ fill: "#10b981", strokeWidth: 0, r: 4 }}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </CardContent>
        </Card>
    );
}
