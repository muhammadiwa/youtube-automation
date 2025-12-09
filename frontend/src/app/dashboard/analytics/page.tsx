"use client";

import { DashboardLayout } from "@/components/dashboard";

export default function AnalyticsPage() {
    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Analytics" }]}
        >
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
                    <p className="text-muted-foreground">
                        View performance metrics and insights
                    </p>
                </div>
                <div className="text-center py-12">
                    <p className="text-muted-foreground">Coming soon...</p>
                </div>
            </div>
        </DashboardLayout>
    );
}
