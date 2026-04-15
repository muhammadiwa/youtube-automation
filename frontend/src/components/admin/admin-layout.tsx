"use client"

import { ReactNode } from "react"
import { AdminSidebar } from "./admin-sidebar"
import { AdminHeader } from "./admin-header"
import { cn } from "@/lib/utils"

interface AdminLayoutProps {
    children: ReactNode
    breadcrumbs?: { label: string; href?: string }[]
    className?: string
}

export function AdminLayout({
    children,
    breadcrumbs,
    className,
}: AdminLayoutProps) {
    return (
        <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
            {/* Desktop Sidebar */}
            <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 z-50">
                <AdminSidebar />
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col lg:pl-64">
                <AdminHeader breadcrumbs={breadcrumbs} />
                <main className={cn(
                    "flex-1 p-4 md:p-6",
                    className
                )}>
                    {children}
                </main>
            </div>
        </div>
    )
}
