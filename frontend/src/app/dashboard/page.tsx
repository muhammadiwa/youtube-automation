"use client";

import { DashboardLayout } from "@/components/dashboard";
import { OverviewCard } from "@/components/dashboard/overview-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentActivity } from "@/components/dashboard/recent-activity";
import { PerformanceChart } from "@/components/dashboard/performance-chart";
import { Users, Eye, DollarSign, Radio } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
    const { user } = useAuth();

    // Mock data - will be replaced with real API data
    const stats = {
        subscribers: {
            value: "12,345",
            trend: { value: 12.5, isPositive: true },
        },
        views: {
            value: "1.2M",
            trend: { value: 8.3, isPositive: true },
        },
        revenue: {
            value: "$4,231",
            trend: { value: 15.2, isPositive: true },
        },
        activeStreams: {
            value: "3",
            trend: { value: 2.1, isPositive: false },
        },
    };

    return (
        <DashboardLayout breadcrumbs={[{ label: "Dashboard" }]}>
            <div className="space-y-6">
                {/* Welcome Message */}
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">
                        Welcome back, {user?.name || "User"}!
                    </h1>
                    <p className="text-muted-foreground">
                        Here's what's happening with your channels today.
                    </p>
                </div>

                {/* Overview Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <OverviewCard
                        title="Total Subscribers"
                        value={stats.subscribers.value}
                        icon={Users}
                        trend={stats.subscribers.trend}
                    />
                    <OverviewCard
                        title="Total Views"
                        value={stats.views.value}
                        icon={Eye}
                        trend={stats.views.trend}
                    />
                    <OverviewCard
                        title="Revenue"
                        value={stats.revenue.value}
                        icon={DollarSign}
                        trend={stats.revenue.trend}
                    />
                    <OverviewCard
                        title="Active Streams"
                        value={stats.activeStreams.value}
                        icon={Radio}
                        trend={stats.activeStreams.trend}
                    />
                </div>

                {/* Quick Actions */}
                <QuickActions />

                {/* Charts and Activity */}
                <div className="grid gap-4 md:grid-cols-2">
                    <PerformanceChart />
                    <RecentActivity />
                </div>
            </div>
        </DashboardLayout>
    );
}
