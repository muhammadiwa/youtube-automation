"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    Home,
    Users,
    Video,
    Radio,
    BarChart3,
    Settings,
    Menu,
    Youtube,
    HelpCircle,
    Shield,
    MessageSquare,
    DollarSign,
    Target,
    AlertTriangle,
    ListTodo,
    Monitor,
    Wallet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useState } from "react";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: Home },
    { name: "Accounts", href: "/dashboard/accounts", icon: Users },
    { name: "Videos", href: "/dashboard/videos", icon: Video },
    { name: "Streams", href: "/dashboard/streams", icon: Radio },
    { name: "Comments", href: "/dashboard/comments", icon: MessageSquare },
    { name: "Moderation", href: "/dashboard/moderation/settings", icon: Shield },
    { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
    { name: "Revenue", href: "/dashboard/revenue", icon: DollarSign },
    { name: "Competitors", href: "/dashboard/competitors", icon: Target },
    { name: "Strikes", href: "/dashboard/strikes", icon: AlertTriangle },
    { name: "Monitoring", href: "/dashboard/monitoring", icon: Monitor },
    { name: "Jobs", href: "/dashboard/jobs", icon: ListTodo },
    { name: "Billing", href: "/dashboard/billing", icon: Wallet },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

interface SidebarProps {
    className?: string;
}

function NavItem({
    item,
    isActive,
    onClick
}: {
    item: typeof navigation[0];
    isActive: boolean;
    onClick?: () => void;
}) {
    return (
        <Link href={item.href} onClick={onClick}>
            <div
                className={cn(
                    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300 ease-out",
                    isActive
                        ? "bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg shadow-red-500/30"
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
                {isActive && (
                    <div className="h-1.5 w-1.5 rounded-full bg-white/80 animate-pulse" />
                )}
            </div>
        </Link>
    );
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();

    const isActiveRoute = (href: string) => {
        if (href === "/dashboard") {
            return pathname === "/dashboard";
        }
        // Handle moderation routes - check if pathname starts with /dashboard/moderation
        if (href.startsWith("/dashboard/moderation")) {
            return pathname.startsWith("/dashboard/moderation");
        }
        // Handle comments routes - check if pathname starts with /dashboard/comments
        if (href.startsWith("/dashboard/comments")) {
            return pathname.startsWith("/dashboard/comments");
        }
        // Handle revenue routes - check if pathname starts with /dashboard/revenue
        if (href.startsWith("/dashboard/revenue")) {
            return pathname.startsWith("/dashboard/revenue");
        }
        // Handle strikes routes - check if pathname starts with /dashboard/strikes
        if (href.startsWith("/dashboard/strikes")) {
            return pathname.startsWith("/dashboard/strikes");
        }
        // Handle jobs routes - check if pathname starts with /dashboard/jobs
        if (href.startsWith("/dashboard/jobs")) {
            return pathname.startsWith("/dashboard/jobs");
        }
        // Handle monitoring routes
        if (href.startsWith("/dashboard/monitoring")) {
            return pathname.startsWith("/dashboard/monitoring");
        }
        // Handle settings routes
        if (href.startsWith("/dashboard/settings")) {
            return pathname.startsWith("/dashboard/settings");
        }
        // Handle billing routes
        if (href.startsWith("/dashboard/billing")) {
            return pathname.startsWith("/dashboard/billing");
        }
        return pathname.startsWith(href);
    };

    return (
        <div className={cn("flex flex-col h-full bg-card border-r", className)}>
            {/* Logo Section - h-16 to match header */}
            <div className="h-16 flex items-center px-6 border-b">
                <Link href="/dashboard" className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/30">
                        <Youtube className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-base font-bold tracking-tight">YT Automation</span>
                        <span className="text-[10px] text-muted-foreground leading-none">Manage your channels</span>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <ScrollArea className="flex-1 px-3 py-4">
                <div className="space-y-1.5">
                    <p className="px-3 mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                        Menu
                    </p>
                    {navigation.map((item) => (
                        <NavItem
                            key={item.name}
                            item={item}
                            isActive={isActiveRoute(item.href)}
                        />
                    ))}
                </div>
            </ScrollArea>

            {/* Footer */}
            <div className="p-3 border-t">
                <div className="rounded-xl bg-gradient-to-br from-red-500/5 via-orange-500/5 to-yellow-500/5 p-4 border border-red-500/10">
                    <div className="flex items-center gap-2 mb-2">
                        <HelpCircle className="h-4 w-4 text-red-500" />
                        <p className="text-sm font-semibold">Need help?</p>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        Check our docs for guides and tutorials.
                    </p>
                    <Button
                        variant="outline"
                        size="sm"
                        className="mt-3 w-full text-xs h-8 rounded-lg border-red-500/20 hover:bg-red-500/10 hover:text-red-500 transition-colors"
                    >
                        View Documentation
                    </Button>
                </div>
            </div>
        </div>
    );
}

export function MobileSidebar() {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();

    const isActiveRoute = (href: string) => {
        if (href === "/dashboard") {
            return pathname === "/dashboard";
        }
        return pathname.startsWith(href);
    };

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle menu</span>
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
                <div className="flex flex-col h-full bg-card">
                    {/* Logo Section */}
                    <div className="h-16 flex items-center px-6 border-b">
                        <Link
                            href="/dashboard"
                            className="flex items-center gap-3"
                            onClick={() => setOpen(false)}
                        >
                            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/30">
                                <Youtube className="h-5 w-5 text-white" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-base font-bold tracking-tight">YT Automation</span>
                                <span className="text-[10px] text-muted-foreground leading-none">Manage your channels</span>
                            </div>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <ScrollArea className="flex-1 px-3 py-4">
                        <div className="space-y-1.5">
                            <p className="px-3 mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                                Menu
                            </p>
                            {navigation.map((item) => (
                                <NavItem
                                    key={item.name}
                                    item={item}
                                    isActive={isActiveRoute(item.href)}
                                    onClick={() => setOpen(false)}
                                />
                            ))}
                        </div>
                    </ScrollArea>

                    {/* Footer */}
                    <div className="p-3 border-t">
                        <div className="rounded-xl bg-gradient-to-br from-red-500/5 via-orange-500/5 to-yellow-500/5 p-4 border border-red-500/10">
                            <div className="flex items-center gap-2 mb-2">
                                <HelpCircle className="h-4 w-4 text-red-500" />
                                <p className="text-sm font-semibold">Need help?</p>
                            </div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                Check our docs for guides.
                            </p>
                            <Button
                                variant="outline"
                                size="sm"
                                className="mt-3 w-full text-xs h-8 rounded-lg border-red-500/20 hover:bg-red-500/10 hover:text-red-500 transition-colors"
                            >
                                View Docs
                            </Button>
                        </div>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
