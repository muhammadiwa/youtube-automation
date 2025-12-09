"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";
import { useTheme } from "next-themes";

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

    return (
        <Card>
            <CardHeader>
                <CardTitle>Performance Overview</CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={mockData}>
                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke={isDark ? "#374151" : "#e5e7eb"}
                        />
                        <XAxis
                            dataKey="date"
                            stroke={isDark ? "#9ca3af" : "#6b7280"}
                            fontSize={12}
                        />
                        <YAxis stroke={isDark ? "#9ca3af" : "#6b7280"} fontSize={12} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: isDark ? "#1f2937" : "#ffffff",
                                border: `1px solid ${isDark ? "#374151" : "#e5e7eb"}`,
                                borderRadius: "6px",
                            }}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="views"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={{ fill: "#3b82f6" }}
                        />
                        <Line
                            type="monotone"
                            dataKey="subscribers"
                            stroke="#10b981"
                            strokeWidth={2}
                            dot={{ fill: "#10b981" }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
