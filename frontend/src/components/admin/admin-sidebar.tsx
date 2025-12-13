"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
    LayoutDashboard,
    Users,
    CreditCard,
    Shield,
    Server,
    FileText,
    Settings,
    HelpCircle,
    Menu,
    MessageSquare,
    Wallet,
    Zap,
    Database,
    Bell,
    Flag,
    ChevronDown,
    Gift,
    TrendingUp,
    HardDrive,
    ExternalLink,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useState, useEffect } from "react"

interface NavItem {
    name: string
    href: string
    icon: React.ComponentType<{ className?: string }>
}

interface NavSection {
    title: string
    key: string
    icon: React.ComponentType<{ className?: string }>
    items: NavItem[]
}

const adminNavigation: NavSection[] = [
    {
        title: "Overview",
        key: "overview",
        icon: LayoutDashboard,
        items: [
            { name: "Dashboard", href: "/admin", icon: LayoutDashboard },
            { name: "Revenue", href: "/admin/revenue", icon: TrendingUp },
            { name: "Funnel Analysis", href: "/admin/funnel", icon: TrendingUp },
        ],
    },
    {
        title: "User Management",
        key: "users",
        icon: Users,
        items: [
            { name: "Users", href: "/admin/users", icon: Users },
            { name: "Subscriptions", href: "/admin/subscriptions", icon: CreditCard },
        ],
    },
    {
        title: "Content",
        key: "content",
        icon: Shield,
        items: [
            { name: "Moderation", href: "/admin/moderation", icon: Shield },
            { name: "Support Tickets", href: "/admin/support", icon: MessageSquare },
        ],
    },
    {
        title: "System",
        key: "system",
        icon: Server,
        items: [
            { name: "System Health", href: "/admin/system", icon: Server },
            { name: "Quota Management", href: "/admin/quota", icon: Zap },
            { name: "Payment Gateways", href: "/admin/payment-gateways", icon: Wallet },
            { name: "AI Services", href: "/admin/ai", icon: Database },
            { name: "Backups", href: "/admin/backups", icon: HardDrive },
        ],
    },
    {
        title: "Compliance",
        key: "compliance",
        icon: FileText,
        items: [
            { name: "Audit Logs", href: "/admin/audit-logs", icon: FileText },
            { name: "Security", href: "/admin/security", icon: Shield },
            { name: "Data Requests", href: "/admin/compliance/requests", icon: Flag },
        ],
    },
    {
        title: "Configuration",
        key: "configuration",
        icon: Settings,
        items: [
            { name: "Global Config", href: "/admin/config", icon: Settings },
            { name: "Promotions", href: "/admin/promotions", icon: Gift },
            { name: "Announcements", href: "/admin/announcements", icon: Bell },
        ],
    },
]

interface AdminSidebarProps {
    className?: string
}

function AdminNavItem({
    item,
    isActive,
    onClick,
}: {
    item: NavItem
    isActive: boolean
    onClick?: () => void
}) {
    return (
        <Link href={item.href} onClick={onClick}>
            <div
                className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                    isActive
                        ? "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400"
                        : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white"
                )}
            >
                <item.icon
                    className={cn(
                        "h-4 w-4 flex-shrink-0",
                        isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300"
                    )}
                />
                <span className="truncate">{item.name}</span>
                {isActive && (
                    <div className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-500" />
                )}
            </div>
        </Link>
    )
}

function CollapsibleNavSection({
    section,
    isOpen,
    onToggle,
    isActiveRoute,
    onItemClick,
}: {
    section: NavSection
    isOpen: boolean
    onToggle: () => void
    isActiveRoute: (href: string) => boolean
    onItemClick?: () => void
}) {
    const hasActiveItem = section.items.some((item) => isActiveRoute(item.href))
    const SectionIcon = section.icon

    return (
        <Collapsible open={isOpen} onOpenChange={onToggle}>
            <CollapsibleTrigger asChild>
                <button
                    className={cn(
                        "flex w-full items-center gap-3 px-3 py-2 text-sm font-medium transition-colors rounded-lg",
                        hasActiveItem
                            ? "text-blue-600 dark:text-blue-400"
                            : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    )}
                >
                    <SectionIcon className={cn(
                        "h-4 w-4 flex-shrink-0",
                        hasActiveItem ? "text-blue-600 dark:text-blue-400" : "text-slate-400 dark:text-slate-500"
                    )} />
                    <span className="flex-1 text-left">{section.title}</span>
                    <ChevronDown className={cn(
                        "h-4 w-4 text-slate-400 transition-transform duration-200",
                        isOpen && "rotate-180"
                    )} />
                </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pl-4 mt-1 space-y-0.5">
                {section.items.map((item) => (
                    <AdminNavItem
                        key={item.name}
                        item={item}
                        isActive={isActiveRoute(item.href)}
                        onClick={onItemClick}
                    />
                ))}
            </CollapsibleContent>
        </Collapsible>
    )
}

export function AdminSidebar({ className }: AdminSidebarProps) {
    const pathname = usePathname()

    const getInitialOpenSections = () => {
        const openSections: Record<string, boolean> = {}
        adminNavigation.forEach((section) => {
            const hasActiveItem = section.items.some((item) => {
                if (item.href === "/admin") {
                    return pathname === "/admin"
                }
                return pathname.startsWith(item.href)
            })
            openSections[section.key] = hasActiveItem || section.key === "overview"
        })
        return openSections
    }

    const [openSections, setOpenSections] = useState<Record<string, boolean>>(getInitialOpenSections)

    useEffect(() => {
        setOpenSections((prev) => {
            const newState = { ...prev }
            adminNavigation.forEach((section) => {
                const hasActiveItem = section.items.some((item) => {
                    if (item.href === "/admin") {
                        return pathname === "/admin"
                    }
                    return pathname.startsWith(item.href)
                })
                if (hasActiveItem) {
                    newState[section.key] = true
                }
            })
            return newState
        })
    }, [pathname])

    const toggleSection = (key: string) => {
        setOpenSections((prev) => ({
            ...prev,
            [key]: !prev[key],
        }))
    }

    const isActiveRoute = (href: string) => {
        if (href === "/admin") {
            return pathname === "/admin"
        }
        return pathname.startsWith(href)
    }

    return (
        <div className={cn(
            "flex flex-col h-full bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800",
            className
        )}>
            {/* Logo Section */}
            <div className="h-16 flex items-center px-5 border-b border-slate-200 dark:border-slate-800">
                <Link href="/admin" className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md shadow-blue-500/20">
                        <Shield className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-sm font-bold text-slate-900 dark:text-white">Admin Panel</span>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400">System Management</span>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
                <div className="space-y-1">
                    {adminNavigation.map((section) => (
                        <CollapsibleNavSection
                            key={section.key}
                            section={section}
                            isOpen={openSections[section.key] ?? true}
                            onToggle={() => toggleSection(section.key)}
                            isActiveRoute={isActiveRoute}
                        />
                    ))}
                </div>
            </ScrollArea>

            {/* Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                {/* Back to User Dashboard */}
                <Link href="/dashboard">
                    <Button
                        variant="outline"
                        className="w-full justify-start gap-2 text-sm h-9 rounded-lg border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                        <ExternalLink className="h-4 w-4" />
                        Back to Dashboard
                    </Button>
                </Link>

                {/* Help Card */}
                <div className="mt-4 rounded-lg bg-slate-50 dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800">
                    <div className="flex items-center gap-2 mb-2">
                        <HelpCircle className="h-4 w-4 text-blue-500" />
                        <p className="text-sm font-medium text-slate-900 dark:text-white">Need Help?</p>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                        View admin documentation and guides.
                    </p>
                    <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs h-8 rounded-lg border-slate-200 dark:border-slate-700"
                    >
                        View Docs
                    </Button>
                </div>
            </div>
        </div>
    )
}

export function MobileAdminSidebar() {
    const [open, setOpen] = useState(false)
    const pathname = usePathname()

    const getInitialOpenSections = () => {
        const openSections: Record<string, boolean> = {}
        adminNavigation.forEach((section) => {
            const hasActiveItem = section.items.some((item) => {
                if (item.href === "/admin") {
                    return pathname === "/admin"
                }
                return pathname.startsWith(item.href)
            })
            openSections[section.key] = hasActiveItem || section.key === "overview"
        })
        return openSections
    }

    const [openSections, setOpenSections] = useState<Record<string, boolean>>(getInitialOpenSections)

    useEffect(() => {
        setOpenSections((prev) => {
            const newState = { ...prev }
            adminNavigation.forEach((section) => {
                const hasActiveItem = section.items.some((item) => {
                    if (item.href === "/admin") {
                        return pathname === "/admin"
                    }
                    return pathname.startsWith(item.href)
                })
                if (hasActiveItem) {
                    newState[section.key] = true
                }
            })
            return newState
        })
    }, [pathname])

    const toggleSection = (key: string) => {
        setOpenSections((prev) => ({
            ...prev,
            [key]: !prev[key],
        }))
    }

    const isActiveRoute = (href: string) => {
        if (href === "/admin") {
            return pathname === "/admin"
        }
        return pathname.startsWith(href)
    }

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle admin menu</span>
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
                <div className="flex flex-col h-full bg-white dark:bg-slate-950">
                    {/* Logo Section */}
                    <div className="h-16 flex items-center px-5 border-b border-slate-200 dark:border-slate-800">
                        <Link
                            href="/admin"
                            className="flex items-center gap-3"
                            onClick={() => setOpen(false)}
                        >
                            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 shadow-md shadow-blue-500/20">
                                <Shield className="h-5 w-5 text-white" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-bold text-slate-900 dark:text-white">Admin Panel</span>
                                <span className="text-[10px] text-slate-500 dark:text-slate-400">System Management</span>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <ScrollArea className="flex-1 px-3 py-4">
                        <div className="space-y-1">
                            {adminNavigation.map((section) => (
                                <CollapsibleNavSection
                                    key={section.key}
                                    section={section}
                                    isOpen={openSections[section.key] ?? true}
                                    onToggle={() => toggleSection(section.key)}
                                    isActiveRoute={isActiveRoute}
                                    onItemClick={() => setOpen(false)}
                                />
                            ))}
                        </div>
                    </ScrollArea>

                    {/* Footer */}
                    <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                        <Link href="/dashboard" onClick={() => setOpen(false)}>
                            <Button
                                variant="outline"
                                className="w-full justify-start gap-2 text-sm h-9 rounded-lg"
                            >
                                <ExternalLink className="h-4 w-4" />
                                Back to Dashboard
                            </Button>
                        </Link>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    )
}
