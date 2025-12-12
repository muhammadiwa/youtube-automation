"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
    Home,
    Users,
    CreditCard,
    Shield,
    Server,
    FileText,
    Settings,
    BarChart3,
    HelpCircle,
    Menu,
    MessageSquare,
    Wallet,
    Zap,
    Database,
    Bell,
    Flag,
    ChevronDown,
    ChevronRight,
    Gift,
    TrendingUp,
    Map,
    Clock,
    Layers,
    HardDrive,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { useState, useEffect } from "react"

interface NavItem {
    name: string
    href: string
    icon: React.ComponentType<{ className?: string }>
    badge?: string | number
}

interface NavSection {
    title: string
    key: string
    items: NavItem[]
}

const adminNavigation: NavSection[] = [
    {
        title: "Overview",
        key: "overview",
        items: [
            { name: "Dashboard", href: "/admin", icon: Home },
        ],
    },
    {
        title: "User Management",
        key: "users",
        items: [
            { name: "Users", href: "/admin/users", icon: Users },
            { name: "Subscriptions", href: "/admin/subscriptions", icon: CreditCard },
        ],
    },
    {
        title: "Content",
        key: "content",
        items: [
            { name: "Moderation", href: "/admin/moderation", icon: Shield },
            { name: "Support Tickets", href: "/admin/support", icon: MessageSquare },
        ],
    },
    {
        title: "System",
        key: "system",
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
        items: [
            { name: "Audit Logs", href: "/admin/audit-logs", icon: FileText },
            { name: "Security", href: "/admin/security", icon: Shield },
            { name: "Data Requests", href: "/admin/compliance", icon: Flag },
        ],
    },
    {
        title: "Configuration",
        key: "configuration",
        items: [
            { name: "Global Config", href: "/admin/config", icon: Settings },
            { name: "Promotions", href: "/admin/promotions", icon: Gift },
            { name: "Announcements", href: "/admin/announcements", icon: Bell },
        ],
    },
    {
        title: "Analytics",
        key: "analytics",
        items: [
            { name: "Platform Analytics", href: "/admin/analytics", icon: BarChart3 },
            { name: "Growth Metrics", href: "/admin/analytics/growth", icon: TrendingUp },
            { name: "Cohort Analysis", href: "/admin/analytics/cohort", icon: Layers },
            { name: "Geographic", href: "/admin/analytics/geographic", icon: Map },
            { name: "Usage Heatmap", href: "/admin/analytics/heatmap", icon: Clock },
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
                    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300 ease-out",
                    isActive
                        ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30"
                        : "text-muted-foreground hover:bg-accent/80 hover:text-foreground"
                )}
            >
                <item.icon
                    className={cn(
                        "h-5 w-5 transition-all duration-300",
                        isActive ? "text-white" : "group-hover:scale-110"
                    )}
                />
                <span className="flex-1">{item.name}</span>
                {item.badge && (
                    <Badge
                        variant={isActive ? "secondary" : "outline"}
                        className={cn(
                            "text-xs",
                            isActive && "bg-white/20 text-white border-white/30"
                        )}
                    >
                        {item.badge}
                    </Badge>
                )}
                {isActive && (
                    <div className="h-1.5 w-1.5 rounded-full bg-white/80 animate-pulse" />
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

    return (
        <Collapsible open={isOpen} onOpenChange={onToggle}>
            <CollapsibleTrigger asChild>
                <button
                    className={cn(
                        "flex w-full items-center justify-between px-3 py-2 text-[11px] font-semibold uppercase tracking-wider transition-colors rounded-lg",
                        hasActiveItem
                            ? "text-blue-500"
                            : "text-muted-foreground/70 hover:text-muted-foreground hover:bg-accent/50"
                    )}
                >
                    <span>{section.title}</span>
                    {isOpen ? (
                        <ChevronDown className="h-3.5 w-3.5 transition-transform duration-200" />
                    ) : (
                        <ChevronRight className="h-3.5 w-3.5 transition-transform duration-200" />
                    )}
                </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
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

    // Initialize open sections based on current route
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

    // Update open sections when pathname changes
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
        <div className={cn("flex flex-col h-full bg-card border-r", className)}>
            {/* Logo Section */}
            <div className="h-16 flex items-center px-6 border-b">
                <Link href="/admin" className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30">
                        <Shield className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-base font-bold tracking-tight">Admin Panel</span>
                        <span className="text-[10px] text-muted-foreground leading-none">System Management</span>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
                <div className="space-y-4">
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
            <div className="p-3 border-t">
                <div className="rounded-xl bg-gradient-to-br from-blue-500/5 via-indigo-500/5 to-purple-500/5 p-4 border border-blue-500/10">
                    <div className="flex items-center gap-2 mb-2">
                        <HelpCircle className="h-4 w-4 text-blue-500" />
                        <p className="text-sm font-semibold">Admin Help</p>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        View admin documentation and guides.
                    </p>
                    <Button
                        variant="outline"
                        size="sm"
                        className="mt-3 w-full text-xs h-8 rounded-lg border-blue-500/20 hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
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

    // Initialize open sections based on current route
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

    // Update open sections when pathname changes
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
                <Button variant="ghost" size="icon" className="md:hidden">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle admin menu</span>
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
                <div className="flex flex-col h-full bg-card">
                    {/* Logo Section */}
                    <div className="h-16 flex items-center px-6 border-b">
                        <Link
                            href="/admin"
                            className="flex items-center gap-3"
                            onClick={() => setOpen(false)}
                        >
                            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30">
                                <Shield className="h-5 w-5 text-white" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-base font-bold tracking-tight">Admin Panel</span>
                                <span className="text-[10px] text-muted-foreground leading-none">System Management</span>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <ScrollArea className="flex-1 px-3 py-4">
                        <div className="space-y-4">
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
                    <div className="p-3 border-t">
                        <div className="rounded-xl bg-gradient-to-br from-blue-500/5 via-indigo-500/5 to-purple-500/5 p-4 border border-blue-500/10">
                            <div className="flex items-center gap-2 mb-2">
                                <HelpCircle className="h-4 w-4 text-blue-500" />
                                <p className="text-sm font-semibold">Admin Help</p>
                            </div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                View admin docs.
                            </p>
                            <Button
                                variant="outline"
                                size="sm"
                                className="mt-3 w-full text-xs h-8 rounded-lg border-blue-500/20 hover:bg-blue-500/10 hover:text-blue-500 transition-colors"
                            >
                                View Docs
                            </Button>
                        </div>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    )
}
