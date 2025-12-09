"use client";

import { useState } from "react";
import { LogOut, Settings, User, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";
import { MobileSidebar } from "./sidebar";
import { NotificationCenter } from "./notification-center";
import { NotificationPreferencesModal } from "./notification-preferences-modal";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface HeaderProps {
    breadcrumbs?: { label: string; href?: string }[];
}

export function Header({ breadcrumbs }: HeaderProps) {
    const { user, logout } = useAuth();
    const router = useRouter();
    const [preferencesOpen, setPreferencesOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        router.push("/login");
    };

    const userInitials = user?.name
        ? user.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
        : "U";

    return (
        <>
            <header className="sticky top-0 z-40 h-16 flex items-center border-b bg-background/80 backdrop-blur-xl">
                <div className="flex w-full items-center px-4 md:px-6 gap-4">
                    {/* Mobile Menu */}
                    <MobileSidebar />

                    {/* Breadcrumbs */}
                    {breadcrumbs && breadcrumbs.length > 0 && (
                        <nav className="hidden md:flex items-center text-sm">
                            {breadcrumbs.map((crumb, index) => (
                                <div key={index} className="flex items-center">
                                    {index > 0 && (
                                        <ChevronRight className="mx-2 h-4 w-4 text-muted-foreground/50" />
                                    )}
                                    {crumb.href ? (
                                        <Link
                                            href={crumb.href}
                                            className="text-muted-foreground hover:text-foreground transition-colors duration-200"
                                        >
                                            {crumb.label}
                                        </Link>
                                    ) : (
                                        <span className="font-medium text-foreground">
                                            {crumb.label}
                                        </span>
                                    )}
                                </div>
                            ))}
                        </nav>
                    )}

                    {/* Spacer */}
                    <div className="flex-1" />

                    {/* Search Bar */}
                    <div className="hidden lg:flex items-center">
                        <div className="relative group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-red-500" />
                            <Input
                                type="search"
                                placeholder="Search..."
                                className="w-64 pl-9 h-9 bg-muted/50 border-0 rounded-xl focus-visible:ring-2 focus-visible:ring-red-500/30 focus-visible:bg-background transition-all duration-300"
                            />
                        </div>
                    </div>

                    {/* Right side actions */}
                    <div className="flex items-center gap-1">
                        {/* Theme Toggle */}
                        <ThemeToggle />

                        {/* Notifications */}
                        <NotificationCenter
                            onOpenPreferences={() => setPreferencesOpen(true)}
                        />

                        {/* User Menu */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    variant="ghost"
                                    className="relative h-9 gap-2 px-2 hover:bg-accent rounded-xl ml-1"
                                >
                                    <Avatar className="h-8 w-8 ring-2 ring-red-500/20 transition-all duration-300 hover:ring-red-500/40">
                                        <AvatarFallback className="bg-gradient-to-br from-red-500 to-red-600 text-white text-xs font-semibold">
                                            {userInitials}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="hidden md:flex flex-col items-start">
                                        <span className="text-sm font-medium leading-none">
                                            {user?.name || "User"}
                                        </span>
                                    </div>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-64 p-2 rounded-xl">
                                <DropdownMenuLabel className="font-normal">
                                    <div className="flex items-center gap-3 p-2">
                                        <Avatar className="h-12 w-12 ring-2 ring-red-500/20">
                                            <AvatarFallback className="bg-gradient-to-br from-red-500 to-red-600 text-white font-semibold">
                                                {userInitials}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="flex flex-col space-y-1">
                                            <p className="text-sm font-semibold leading-none">
                                                {user?.name || "User"}
                                            </p>
                                            <p className="text-xs leading-none text-muted-foreground">
                                                {user?.email || "user@example.com"}
                                            </p>
                                        </div>
                                    </div>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator className="my-2" />
                                <DropdownMenuItem
                                    onClick={() => router.push("/dashboard/settings")}
                                    className="cursor-pointer rounded-lg py-2.5 transition-colors"
                                >
                                    <User className="mr-3 h-4 w-4" />
                                    <span>Profile</span>
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                    onClick={() => router.push("/dashboard/settings")}
                                    className="cursor-pointer rounded-lg py-2.5 transition-colors"
                                >
                                    <Settings className="mr-3 h-4 w-4" />
                                    <span>Settings</span>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator className="my-2" />
                                <DropdownMenuItem
                                    onClick={handleLogout}
                                    className="cursor-pointer rounded-lg py-2.5 text-red-500 focus:text-red-500 focus:bg-red-500/10 transition-colors"
                                >
                                    <LogOut className="mr-3 h-4 w-4" />
                                    <span>Log out</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>
            </header>

            {/* Notification Preferences Modal */}
            <NotificationPreferencesModal
                open={preferencesOpen}
                onOpenChange={setPreferencesOpen}
            />
        </>
    );
}
