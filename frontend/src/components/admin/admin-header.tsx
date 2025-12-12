"use client"

import { LogOut, Settings, User, ChevronRight, Search, ArrowLeft, Shield, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import { MobileAdminSidebar } from "./admin-sidebar"
import { useAuth } from "@/hooks/use-auth"
import { useAdmin } from "@/hooks/use-admin"
import { useAdminSession } from "@/hooks/use-admin-session"
import { useRouter } from "next/navigation"
import Link from "next/link"

interface AdminHeaderProps {
    breadcrumbs?: { label: string; href?: string }[]
}

/**
 * Format time remaining in human readable format
 */
function formatTimeRemaining(seconds: number | null): string {
    if (seconds === null || seconds <= 0) return "Expired"

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
        return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
}

export function AdminHeader({ breadcrumbs }: AdminHeaderProps) {
    const { user, logout: authLogout } = useAuth()
    const { admin } = useAdmin()
    const { timeRemaining, clearSession } = useAdminSession()
    const router = useRouter()

    const handleLogout = async () => {
        // Clear admin session first
        clearSession()
        // Then logout from main auth
        await authLogout()
        router.push("/admin/login")
    }

    const handleAdminLogout = () => {
        // Only clear admin session, keep user logged in
        clearSession()
        router.push("/admin/login")
    }

    const userInitials = user?.name
        ? user.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
        : "A"

    const roleLabel = admin?.role === "super_admin" ? "Super Admin" : "Admin"
    const roleColor = admin?.role === "super_admin" ? "bg-purple-500" : "bg-blue-500"

    return (
        <header className="sticky top-0 z-40 h-16 flex items-center border-b bg-background/80 backdrop-blur-xl">
            <div className="flex w-full items-center px-4 md:px-6 gap-4">
                {/* Mobile Menu */}
                <MobileAdminSidebar />

                {/* Back to Dashboard */}
                <Link href="/dashboard" className="hidden md:flex">
                    <Button variant="ghost" size="sm" className="gap-2 text-muted-foreground hover:text-foreground">
                        <ArrowLeft className="h-4 w-4" />
                        <span className="text-sm">Back to Dashboard</span>
                    </Button>
                </Link>

                {/* Breadcrumbs */}
                {breadcrumbs && breadcrumbs.length > 0 && (
                    <nav className="hidden md:flex items-center text-sm">
                        <ChevronRight className="mx-2 h-4 w-4 text-muted-foreground/50" />
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
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors group-focus-within:text-blue-500" />
                        <Input
                            type="search"
                            placeholder="Search admin..."
                            className="w-64 pl-9 h-9 bg-muted/50 border-0 rounded-xl focus-visible:ring-2 focus-visible:ring-blue-500/30 focus-visible:bg-background transition-all duration-300"
                        />
                    </div>
                </div>

                {/* Right side actions */}
                <div className="flex items-center gap-1">
                    {/* Session Timer */}
                    {timeRemaining !== null && timeRemaining > 0 && (
                        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-muted/50 text-xs text-muted-foreground">
                            <Clock className="h-3.5 w-3.5" />
                            <span>Session: {formatTimeRemaining(timeRemaining)}</span>
                        </div>
                    )}

                    {/* Theme Toggle */}
                    <ThemeToggle />

                    {/* User Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button
                                variant="ghost"
                                className="relative h-9 gap-2 px-2 hover:bg-accent rounded-xl ml-1"
                            >
                                <Avatar className="h-8 w-8 ring-2 ring-blue-500/20 transition-all duration-300 hover:ring-blue-500/40">
                                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white text-xs font-semibold">
                                        {userInitials}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="hidden md:flex flex-col items-start">
                                    <span className="text-sm font-medium leading-none">
                                        {user?.name || "Admin"}
                                    </span>
                                    <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 mt-0.5 ${roleColor} text-white`}>
                                        {roleLabel}
                                    </Badge>
                                </div>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-64 p-2 rounded-xl">
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex items-center gap-3 p-2">
                                    <Avatar className="h-12 w-12 ring-2 ring-blue-500/20">
                                        <AvatarFallback className="bg-gradient-to-br from-blue-500 to-blue-600 text-white font-semibold">
                                            {userInitials}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex flex-col space-y-1">
                                        <p className="text-sm font-semibold leading-none">
                                            {user?.name || "Admin"}
                                        </p>
                                        <p className="text-xs leading-none text-muted-foreground">
                                            {user?.email || "admin@example.com"}
                                        </p>
                                        <Badge variant="secondary" className={`text-[10px] w-fit px-1.5 py-0 ${roleColor} text-white`}>
                                            <Shield className="h-3 w-3 mr-1" />
                                            {roleLabel}
                                        </Badge>
                                    </div>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator className="my-2" />
                            <DropdownMenuItem
                                onClick={() => router.push("/dashboard")}
                                className="cursor-pointer rounded-lg py-2.5 transition-colors"
                            >
                                <ArrowLeft className="mr-3 h-4 w-4" />
                                <span>Back to Dashboard</span>
                            </DropdownMenuItem>
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
                                onClick={handleAdminLogout}
                                className="cursor-pointer rounded-lg py-2.5 text-amber-600 focus:text-amber-600 focus:bg-amber-500/10 transition-colors"
                            >
                                <Shield className="mr-3 h-4 w-4" />
                                <span>Exit Admin Panel</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem
                                onClick={handleLogout}
                                className="cursor-pointer rounded-lg py-2.5 text-red-500 focus:text-red-500 focus:bg-red-500/10 transition-colors"
                            >
                                <LogOut className="mr-3 h-4 w-4" />
                                <span>Log out completely</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
        </header>
    )
}
