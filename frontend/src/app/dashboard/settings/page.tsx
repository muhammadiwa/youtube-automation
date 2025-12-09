"use client";

import { DashboardLayout } from "@/components/dashboard";

export default function SettingsPage() {
    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings" }]}
        >
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
                    <p className="text-muted-foreground">
                        Manage your account and preferences
                    </p>
                </div>
                <div className="text-center py-12">
                    <p className="text-muted-foreground">Coming soon...</p>
                </div>
            </div>
        </DashboardLayout>
    );
}
