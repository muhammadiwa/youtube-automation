"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import {
    Shield,
    Upload,
    Radio,
    Sparkles,
    MessageSquare,
    Bell,
    Cog,
    Settings,
    CreditCard,
    Mail,
    Flag,
    Palette,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { cn } from "@/lib/utils"

interface ConfigNavItem {
    name: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    description: string
}

const configNavItems: ConfigNavItem[] = [
    {
        name: "Authentication",
        href: "/admin/config/auth",
        icon: Shield,
        description: "JWT, password policy, login security",
    },
    {
        name: "Upload",
        href: "/admin/config/upload",
        icon: Upload,
        description: "File limits, upload behavior, video defaults",
    },
    {
        name: "Streaming",
        href: "/admin/config/streaming",
        icon: Radio,
        description: "Stream limits, health monitoring, simulcast",
    },
    {
        name: "AI Services",
        href: "/admin/config/ai",
        icon: Sparkles,
        description: "Model selection, generation settings, budget",
    },
    {
        name: "Moderation",
        href: "/admin/config/moderation",
        icon: MessageSquare,
        description: "Filter toggles, penalty settings, slow mode",
    },
    {
        name: "Notifications",
        href: "/admin/config/notifications",
        icon: Bell,
        description: "Channel toggles, batching, retention",
    },
    {
        name: "Job Queue",
        href: "/admin/config/jobs",
        icon: Cog,
        description: "Retry settings, timeouts, worker settings",
    },
    {
        name: "Plans",
        href: "/admin/config/plans",
        icon: CreditCard,
        description: "Subscription plans, pricing, limits",
    },
    {
        name: "Email Templates",
        href: "/admin/config/email-templates",
        icon: Mail,
        description: "Email templates, preview, variables",
    },
    {
        name: "Feature Flags",
        href: "/admin/config/feature-flags",
        icon: Flag,
        description: "Feature toggles, rollout, targeting",
    },
    {
        name: "Branding",
        href: "/admin/config/branding",
        icon: Palette,
        description: "Platform name, logo, colors, links",
    },
]

export default function ConfigLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()
    const [isCollapsed, setIsCollapsed] = useState(false)

    return (
        <AdminLayout>
            <div className="flex h-full">
                {/* Config Sidebar */}
                <div
                    className={cn(
                        "border-r border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 transition-all duration-300",
                        isCollapsed ? "w-16" : "w-64"
                    )}
                >
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <div className="flex items-center justify-between">
                            {!isCollapsed && (
                                <div className="flex items-center gap-2">
                                    <Settings className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                                    <h2 className="font-semibold text-slate-900 dark:text-white">
                                        Configuration
                                    </h2>
                                </div>
                            )}
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                            >
                                <svg
                                    className={cn(
                                        "h-4 w-4 text-slate-500 transition-transform",
                                        isCollapsed && "rotate-180"
                                    )}
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                                    />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <nav className="p-2 space-y-1">
                        {configNavItems.map((item) => {
                            const isActive = pathname === item.href
                            const Icon = item.icon

                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                                        isActive
                                            ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                                            : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                                    )}
                                    title={isCollapsed ? item.name : undefined}
                                >
                                    <Icon
                                        className={cn(
                                            "h-5 w-5 flex-shrink-0",
                                            isActive
                                                ? "text-blue-600 dark:text-blue-400"
                                                : "text-slate-500 dark:text-slate-400"
                                        )}
                                    />
                                    {!isCollapsed && (
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate">
                                                {item.name}
                                            </p>
                                            <p className="text-xs text-slate-500 dark:text-slate-500 truncate">
                                                {item.description}
                                            </p>
                                        </div>
                                    )}
                                    {isActive && !isCollapsed && (
                                        <motion.div
                                            layoutId="config-active-indicator"
                                            className="w-1 h-8 bg-blue-600 dark:bg-blue-400 rounded-full"
                                        />
                                    )}
                                </Link>
                            )
                        })}
                    </nav>
                </div>

                {/* Main Content */}
                <div className="flex-1 overflow-auto">
                    {children}
                </div>
            </div>
        </AdminLayout>
    )
}
