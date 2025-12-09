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
    X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useState } from "react";

const navigation = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Accounts", href: "/dashboard/accounts", icon: Users },
    { name: "Videos", href: "/dashboard/videos", icon: Video },
    { name: "Streams", href: "/dashboard/streams", icon: Radio },
    { name: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();

    return (
        <div className={cn("pb-12 min-h-screen", className)}>
            <div className="space-y-4 py-4">
                <div className="px-3 py-2">
                    <div className="mb-4 px-4">
                        <h2 className="text-2xl font-bold tracking-tight">
                            YouTube Automation
                        </h2>
                    </div>
                    <div className="space-y-1">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Link key={item.name} href={item.href}>
                                    <Button
                                        variant={isActive ? "secondary" : "ghost"}
                                        className={cn(
                                            "w-full justify-start",
                                            isActive && "bg-secondary"
                                        )}
                                    >
                                        <item.icon className="mr-2 h-4 w-4" />
                                        {item.name}
                                    </Button>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

export function MobileSidebar() {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                    <Menu className="h-5 w-5" />
                    <span className="sr-only">Toggle menu</span>
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0">
                <ScrollArea className="h-full">
                    <div className="space-y-4 py-4">
                        <div className="px-3 py-2">
                            <div className="mb-4 px-4 flex items-center justify-between">
                                <h2 className="text-xl font-bold tracking-tight">
                                    YouTube Automation
                                </h2>
                            </div>
                            <div className="space-y-1">
                                {navigation.map((item) => {
                                    const isActive = pathname === item.href;
                                    return (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            onClick={() => setOpen(false)}
                                        >
                                            <Button
                                                variant={isActive ? "secondary" : "ghost"}
                                                className={cn(
                                                    "w-full justify-start",
                                                    isActive && "bg-secondary"
                                                )}
                                            >
                                                <item.icon className="mr-2 h-4 w-4" />
                                                {item.name}
                                            </Button>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}
