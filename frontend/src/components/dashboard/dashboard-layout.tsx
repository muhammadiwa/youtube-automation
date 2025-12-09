"use client";

import { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
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
        <div className="flex min-h-screen">
            {/* Desktop Sidebar */}
            <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r bg-background">
                <Sidebar />
            </aside>

            {/* Main Content */}
            <div className="flex-1 md:pl-64">
                <Header breadcrumbs={breadcrumbs} />
                <main className={cn("flex-1 p-6", className)}>{children}</main>
            </div>
        </div>
    );
}
