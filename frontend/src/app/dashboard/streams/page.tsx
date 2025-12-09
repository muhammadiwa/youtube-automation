"use client";

import { DashboardLayout } from "@/components/dashboard";

export default function StreamsPage() {
    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Streams" }]}
        >
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Live Streams</h1>
                    <p className="text-muted-foreground">
                        Manage your live streaming events
                    </p>
                </div>
                <div className="text-center py-12">
                    <p className="text-muted-foreground">Coming soon...</p>
                </div>
            </div>
        </DashboardLayout>
    );
}
