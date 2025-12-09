"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { TrendingUp } from "lucide-react";

// Mock data - will be replaced with real API data
const mockData = [
    { date: "Jan", views: 4000, subscribers: 240 },
    { date: "Feb", views: 3000, subscribers: 198 },
    { date: "Mar", views: 2000, subscribers: 280 },
    { date: "Apr", views: 2780, subscribers: 308 },
    { date: "May", views: 1890, subscribers: 348 },
    { date: "Jun", views: 2390, subscribers: 380 },
    { date: "Jul", views: 3490, subscribers: 430 },
];

export function PerformanceChart() {
    const { theme } = useTheme();
    const isDark = theme === "dark";

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
                <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={mockData}>
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
            </CardContent>
        </Card>
    );
}
