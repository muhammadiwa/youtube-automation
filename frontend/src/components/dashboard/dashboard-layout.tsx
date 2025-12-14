"use client";

import { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { StrikeWarningBanner } from "./strike-alerts";
import { AnnouncementBanner } from "@/components/announcement-banner";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
    children: ReactNode;
    breadcrumbs?: { label: string; href?: string }[];
    className?: string;
}

export function DashboardLayout({
    children,
    breadcrumbs,
    className,
}: DashboardLayoutProps) {
    return (
        <div className="flex min-h-screen bg-muted/30">
            {/* Desktop Sidebar */}
            <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-50">
                <Sidebar />
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col md:pl-64">
                <Header breadcrumbs={breadcrumbs} />
                {/* Strike Warning Banner */}
                <StrikeWarningBanner className="mx-4 md:mx-6 lg:mx-8 mt-4" />
                <main className={cn("flex-1 p-4 md:p-6 lg:p-8", className)}>
                    {/* Announcements Banner */}
                    <AnnouncementBanner />
                    {children}
                </main>
            </div>
        </div>
    );
}
