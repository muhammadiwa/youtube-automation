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
            <div className="space-y-8">
                {/* Welcome Message */}
                <div className="space-y-1">
                    <h1 className="text-2xl md:text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
                        Welcome back, {user?.name || "User"}! 👋
                    </h1>
                    <p className="text-muted-foreground">
                        Here's what's happening with your channels today.
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
                        title="Active Streams"
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
