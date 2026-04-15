"use client"

import { LogOut, Settings, User, ChevronRight, Search, Shield, Clock } from "lucide-react"
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

function formatTimeRemaining(seconds: number | null): string {
    if (seconds === null || seconds <= 0) return "Expired"
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
}

export function AdminHeader({ breadcrumbs }: AdminHeaderProps) {
    const { user, logout: authLogout } = useAuth()
    const { admin } = useAdmin()
    const { timeRemaining, clearSession } = useAdminSession()
    const router = useRouter()

    const handleLogout = async () => {
        clearSession()
        await authLogout()
        router.push("/admin/login")
    }

    const handleAdminLogout = () => {
        clearSession()
        router.push("/admin/login")
    }

    const userInitials = user?.name
        ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase()
        : "A"

    const roleLabel = admin?.role === "super_admin" ? "Super Admin" : "Admin"

    return (
        <header className="sticky top-0 z-40 h-14 flex items-center border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
            <div className="flex w-full items-center px-4 gap-4">
                {/* Mobile Menu */}
                <MobileAdminSidebar />

                {/* Breadcrumbs */}
                {breadcrumbs && breadcrumbs.length > 0 && (
                    <nav className="hidden md:flex items-center text-sm">
                        {breadcrumbs.map((crumb, index) => (
                            <div key={index} className="flex items-center">
                                {index > 0 && (
                                    <ChevronRight className="mx-2 h-4 w-4 text-slate-400" />
                                )}
                                {crumb.href ? (
                                    <Link
                                        href={crumb.href}
                                        className="text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
                                    >
                                        {crumb.label}
                                    </Link>
                                ) : (
                                    <span className="font-medium text-slate-900 dark:text-white">
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
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <Input
                            type="search"
                            placeholder="Search..."
                            className="w-56 pl-9 h-9 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 rounded-lg text-sm"
                        />
                    </div>
                </div>

                {/* Right side actions */}
                <div className="flex items-center gap-2">
                    {/* Session Timer */}
                    {timeRemaining !== null && timeRemaining > 0 && (
                        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-100 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-400">
                            <Clock className="h-3.5 w-3.5" />
                            <span>{formatTimeRemaining(timeRemaining)}</span>
                        </div>
                    )}

                    {/* Theme Toggle */}
                    <ThemeToggle />

                    {/* User Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-9 gap-2 px-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                                <Avatar className="h-7 w-7">
                                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white text-xs font-medium">
                                        {userInitials}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="hidden md:flex flex-col items-start">
                                    <span className="text-sm font-medium text-slate-900 dark:text-white leading-none">
                                        {user?.name || "Admin"}
                                    </span>
                                    <Badge variant="secondary" className="text-[10px] px-1.5 py-0 mt-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-0">
                                        {roleLabel}
                                    </Badge>
                                </div>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56 rounded-lg">
                            <DropdownMenuLabel className="font-normal">
                                <div className="flex items-center gap-3 py-1">
                                    <Avatar className="h-10 w-10">
                                        <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-medium">
                                            {userInitials}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex flex-col">
                                        <p className="text-sm font-medium">{user?.name || "Admin"}</p>
                                        <p className="text-xs text-slate-500">{user?.email}</p>
                                    </div>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => router.push("/dashboard")} className="cursor-pointer">
                                <User className="mr-2 h-4 w-4" />
                                <span>User Dashboard</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => router.push("/dashboard/settings")} className="cursor-pointer">
                                <Settings className="mr-2 h-4 w-4" />
                                <span>Settings</span>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={handleAdminLogout} className="cursor-pointer text-amber-600 focus:text-amber-600">
                                <Shield className="mr-2 h-4 w-4" />
                                <span>Exit Admin Panel</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-500 focus:text-red-500">
                                <LogOut className="mr-2 h-4 w-4" />
                                <span>Log out</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
        </header>
    )
}
