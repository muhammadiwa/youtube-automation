"use client";

import { useState } from "react";
import { LogOut, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/theme-toggle";
import { MobileSidebar } from "./sidebar";
import { NotificationCenter } from "./notification-center";
import { NotificationPreferencesModal } from "./notification-preferences-modal";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";

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
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex h-16 items-center px-4 gap-4">
                    {/* Mobile Menu */}
                    <MobileSidebar />

                    {/* Breadcrumbs */}
                    {breadcrumbs && breadcrumbs.length > 0 && (
                        <nav className="hidden md:flex items-center space-x-2 text-sm">
                            {breadcrumbs.map((crumb, index) => (
                                <div key={index} className="flex items-center">
                                    {index > 0 && <span className="mx-2 text-muted-foreground">/</span>}
                                    {crumb.href ? (
                                        <a
                                            href={crumb.href}
                                            className="text-muted-foreground hover:text-foreground transition-colors"
                                        >
                                            {crumb.label}
                                        </a>
                                    ) : (
                                        <span className="font-medium">{crumb.label}</span>
                                    )}
                                </div>
                            ))}
                        </nav>
                    )}

                    {/* Spacer */}
                    <div className="flex-1" />

                    {/* Right side actions */}
                    <div className="flex items-center gap-2">
                        {/* Theme Toggle */}
                        <ThemeToggle />

                        {/* Notifications */}
                        <NotificationCenter
                            onOpenPreferences={() => setPreferencesOpen(true)}
                        />

                        {/* User Menu */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                                    <Avatar className="h-10 w-10">
                                        <AvatarFallback>{userInitials}</AvatarFallback>
                                    </Avatar>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuLabel>
                                    <div className="flex flex-col space-y-1">
                                        <p className="text-sm font-medium leading-none">
                                            {user?.name || "User"}
                                        </p>
                                        <p className="text-xs leading-none text-muted-foreground">
                                            {user?.email || "user@example.com"}
                                        </p>
                                    </div>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => router.push("/dashboard/settings")}>
                                    <Settings className="mr-2 h-4 w-4" />
                                    <span>Settings</span>
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={handleLogout}>
                                    <LogOut className="mr-2 h-4 w-4" />
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
