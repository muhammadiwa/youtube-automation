"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { OverviewCard } from "@/components/dashboard/overview-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { Users, Eye, DollarSign, Radio } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { analyticsApi, type AnalyticsOverview } from "@/lib/api/analytics";

// Helper function to format numbers
function formatNumber(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
}

// Helper function to format currency
function formatCurrency(num: number): string {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(num);
}

export default function DashboardPage() {
    const { user } = useAuth();
    const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadOverview = async () => {
            try {
                const data = await analyticsApi.getOverview({ period: "30d" });
                setOverview(data);
            } catch (error) {
                console.error("Failed to load analytics overview:", error);
            } finally {
                setLoading(false);
            }
        };
        loadOverview();
    }, []);

    // Calculate stats from real API data
    const stats = {
        subscribers: {
            value: loading ? "..." : formatNumber(overview?.total_subscribers || 0),
            trend: {
                value: overview?.subscribers_change || 0,
                isPositive: (overview?.subscribers_change || 0) >= 0
            },
        },
        views: {
            value: loading ? "..." : formatNumber(overview?.total_views || 0),
            trend: {
                value: overview?.views_change || 0,
                isPositive: (overview?.views_change || 0) >= 0
            },
        },
        revenue: {
            value: loading ? "..." : formatCurrency(overview?.total_revenue || 0),
            trend: {
                value: overview?.revenue_change || 0,
                isPositive: (overview?.revenue_change || 0) >= 0
            },
        },
        activeStreams: {
            value: loading ? "..." : formatNumber(overview?.total_watch_time || 0),
            trend: {
                value: overview?.watch_time_change || 0,
                isPositive: (overview?.watch_time_change || 0) >= 0
            },
        },
    };

    return (
        <DashboardLayout breadcrumbs={[{ label: "Dashboard" }]}>
            <div className="space-y-8">
                {/* Welcome Message */}
                <div className="space-y-1">
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                        Welcome back, {user?.name || "User"}! 👋
                    </h1>
                    <p className="text-muted-foreground">
                        Here&apos;s what&apos;s happening with your channels today.
                    </p>
                </div>

                {/* Overview Cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <OverviewCard
                        title="Total Subscribers"
                        value={stats.subscribers.value}
                        icon={Users}
                        trend={stats.subscribers.trend}
                        gradient="from-blue-500 to-blue-600"
                    />
                    <OverviewCard
                        title="Total Views"
                        value={stats.views.value}
                        icon={Eye}
                        trend={stats.views.trend}
                        gradient="from-purple-500 to-purple-600"
                    />
                    <OverviewCard
                        title="Revenue"
                        value={stats.revenue.value}
                        icon={DollarSign}
                        trend={stats.revenue.trend}
                        gradient="from-green-500 to-green-600"
                    />
                    <OverviewCard
                        title="Watch Time (hrs)"
                        value={stats.activeStreams.value}
                        icon={Radio}
                        trend={stats.activeStreams.trend}
                        gradient="from-red-500 to-red-600"
                    />
                </div>

                {/* Quick Actions */}
                <QuickActions />

                {/* Charts and Activity */}
                <div className="grid gap-6 lg:grid-cols-5">
                    <div className="lg:col-span-3">
                        <PerformanceChart />
                    </div>
                    <div className="lg:col-span-2">
                        <RecentActivity />
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
