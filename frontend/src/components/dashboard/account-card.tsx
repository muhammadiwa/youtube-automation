"use client"

import { YouTubeAccount } from "@/types"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
    Users,
    Video,
    AlertCircle,
    CheckCircle,
    Clock,
    ExternalLink,
    MoreHorizontal,
    RefreshCw,
    Trash2,
    Eye,
    Zap
} from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

interface AccountCardProps {
    account: YouTubeAccount
    view?: "grid" | "list"
    onSync?: (id: string) => void
    onDisconnect?: (id: string) => void
}

const statusConfig = {
    active: {
        label: "Active",
        color: "bg-emerald-500",
        textColor: "text-emerald-600 dark:text-emerald-400",
        bgColor: "bg-emerald-500/10",
        borderColor: "border-emerald-500/20",
        icon: CheckCircle,
    },
    expired: {
        label: "Expired",
        color: "bg-amber-500",
        textColor: "text-amber-600 dark:text-amber-400",
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/20",
        icon: Clock,
    },
    error: {
        label: "Error",
        color: "bg-red-500",
        textColor: "text-red-600 dark:text-red-400",
        bgColor: "bg-red-500/10",
        borderColor: "border-red-500/20",
        icon: AlertCircle,
    },
}

function formatNumber(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + "M"
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + "K"
    }
    return num.toString()
}

export function AccountCard({ account, view = "grid", onSync, onDisconnect }: AccountCardProps) {
    const status = statusConfig[account.status] || statusConfig.error
    const StatusIcon = status.icon

    // Safe access to account properties with fallbacks
    const channelTitle = account.channelTitle || "Unknown Channel"
    const thumbnailUrl = account.thumbnailUrl || ""
    const subscriberCount = account.subscriberCount ?? 0
    const videoCount = account.videoCount ?? 0
    const strikeCount = account.strikeCount ?? 0
    const isMonetized = account.isMonetized ?? false

    if (view === "list") {
        return (
            <Card className="group hover:shadow-lg hover:border-primary/20 transition-all duration-300 overflow-hidden">
                <CardContent className="p-0">
                    <div className="flex items-center">
                        {/* Thumbnail Section */}
                        <Link href={`/dashboard/accounts/${account.id}`} className="flex-shrink-0">
                            <div className="relative w-24 h-24 sm:w-32 sm:h-full bg-gradient-to-br from-red-500/10 to-orange-500/10 flex items-center justify-center">
                                <Avatar className="h-16 w-16 sm:h-20 sm:w-20 ring-4 ring-background shadow-xl">
                                    <AvatarImage src={thumbnailUrl} alt={channelTitle} className="object-cover" />
                                    <AvatarFallback className="bg-gradient-to-br from-red-500 to-orange-500 text-white text-xl font-bold">
                                        {channelTitle.substring(0, 2).toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className={cn(
                                    "absolute bottom-2 right-2 h-4 w-4 rounded-full ring-2 ring-background",
                                    status.color
                                )} />
                            </div>
                        </Link>

                        {/* Content Section */}
                        <div className="flex-1 p-4 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                                <Link href={`/dashboard/accounts/${account.id}`} className="min-w-0 flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="font-semibold text-lg truncate group-hover:text-primary transition-colors">
                                            {channelTitle}
                                        </h3>
                                        {isMonetized && (
                                            <TooltipProvider>
                                                <Tooltip>
                                                    <TooltipTrigger>
                                                        <Zap className="h-4 w-4 text-amber-500 fill-amber-500" />
                                                    </TooltipTrigger>
                                                    <TooltipContent>Monetized</TooltipContent>
                                                </Tooltip>
                                            </TooltipProvider>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                        <div className="flex items-center gap-1.5">
                                            <Users className="h-4 w-4" />
                                            <span className="font-medium">{formatNumber(subscriberCount)}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <Video className="h-4 w-4" />
                                            <span>{formatNumber(videoCount)} videos</span>
                                        </div>
                                    </div>
                                </Link>

                                <div className="flex items-center gap-2 flex-shrink-0">
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "flex items-center gap-1.5 px-2.5 py-1",
                                            status.bgColor,
                                            status.borderColor,
                                            status.textColor
                                        )}
                                    >
                                        <StatusIcon className="h-3.5 w-3.5" />
                                        {status.label}
                                    </Badge>

                                    {strikeCount > 0 && (
                                        <Badge variant="destructive" className="px-2.5 py-1">
                                            {strikeCount} Strike{strikeCount > 1 ? "s" : ""}
                                        </Badge>
                                    )}

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon" className="h-8 w-8">
                                                <MoreHorizontal className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem asChild>
                                                <Link href={`/dashboard/accounts/${account.id}`}>
                                                    <Eye className="mr-2 h-4 w-4" />
                                                    View Details
                                                </Link>
                                            </DropdownMenuItem>
                                            <DropdownMenuItem onClick={() => onSync?.(account.id)}>
                                                <RefreshCw className="mr-2 h-4 w-4" />
                                                Sync Account
                                            </DropdownMenuItem>
                                            <DropdownMenuSeparator />
                                            <DropdownMenuItem
                                                className="text-destructive focus:text-destructive"
                                                onClick={() => onDisconnect?.(account.id)}
                                            >
                                                <Trash2 className="mr-2 h-4 w-4" />
                                                Disconnect
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    // Grid View
    return (
        <Card className="group hover:shadow-xl hover:border-primary/20 hover:-translate-y-1 transition-all duration-300 overflow-hidden h-full">
            <CardContent className="p-0 h-full flex flex-col">
                {/* Header with gradient background */}
                <div className="relative h-24 bg-gradient-to-br from-red-500/20 via-orange-500/10 to-amber-500/20">
                    <div className="absolute inset-0 bg-[url('/grid-pattern.svg')] opacity-30" />

                    {/* Status indicator */}
                    <div className="absolute top-3 right-3">
                        <Badge
                            variant="outline"
                            className={cn(
                                "flex items-center gap-1.5 px-2 py-0.5 text-xs backdrop-blur-sm bg-background/80",
                                status.borderColor,
                                status.textColor
                            )}
                        >
                            <StatusIcon className="h-3 w-3" />
                            {status.label}
                        </Badge>
                    </div>

                    {/* Actions menu */}
                    <div className="absolute top-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="secondary" size="icon" className="h-7 w-7 backdrop-blur-sm bg-background/80">
                                    <MoreHorizontal className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start">
                                <DropdownMenuItem asChild>
                                    <Link href={`/dashboard/accounts/${account.id}`}>
                                        <Eye className="mr-2 h-4 w-4" />
                                        View Details
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => onSync?.(account.id)}>
                                    <RefreshCw className="mr-2 h-4 w-4" />
                                    Sync Account
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                    className="text-destructive focus:text-destructive"
                                    onClick={() => onDisconnect?.(account.id)}
                                >
                                    <Trash2 className="mr-2 h-4 w-4" />
                                    Disconnect
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>

                    {/* Avatar */}
                    <div className="absolute -bottom-10 left-1/2 -translate-x-1/2">
                        <Avatar className="h-20 w-20 ring-4 ring-background shadow-xl">
                            <AvatarImage src={thumbnailUrl} alt={channelTitle} className="object-cover" />
                            <AvatarFallback className="bg-gradient-to-br from-red-500 to-orange-500 text-white text-xl font-bold">
                                {channelTitle.substring(0, 2).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                    </div>
                </div>

                {/* Content */}
                <Link href={`/dashboard/accounts/${account.id}`} className="flex-1 flex flex-col">
                    <div className="pt-12 pb-4 px-4 flex-1 flex flex-col">
                        {/* Channel name */}
                        <div className="text-center mb-3">
                            <div className="flex items-center justify-center gap-1.5 mb-1">
                                <h3 className="font-semibold text-lg line-clamp-1 group-hover:text-primary transition-colors">
                                    {channelTitle}
                                </h3>
                                {isMonetized && (
                                    <TooltipProvider>
                                        <Tooltip>
                                            <TooltipTrigger>
                                                <Zap className="h-4 w-4 text-amber-500 fill-amber-500" />
                                            </TooltipTrigger>
                                            <TooltipContent>Monetized Channel</TooltipContent>
                                        </Tooltip>
                                    </TooltipProvider>
                                )}
                            </div>
                            {strikeCount > 0 && (
                                <Badge variant="destructive" className="text-xs">
                                    {strikeCount} Strike{strikeCount > 1 ? "s" : ""}
                                </Badge>
                            )}
                        </div>

                        {/* Stats */}
                        <div className="grid grid-cols-2 gap-3 mt-auto">
                            <div className="bg-muted/50 rounded-lg p-3 text-center">
                                <div className="flex items-center justify-center gap-1.5 text-muted-foreground mb-1">
                                    <Users className="h-4 w-4" />
                                    <span className="text-xs">Subscribers</span>
                                </div>
                                <p className="font-bold text-lg">{formatNumber(subscriberCount)}</p>
                            </div>
                            <div className="bg-muted/50 rounded-lg p-3 text-center">
                                <div className="flex items-center justify-center gap-1.5 text-muted-foreground mb-1">
                                    <Video className="h-4 w-4" />
                                    <span className="text-xs">Videos</span>
                                </div>
                                <p className="font-bold text-lg">{formatNumber(videoCount)}</p>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="border-t px-4 py-3 bg-muted/30">
                        <div className="flex items-center justify-center gap-2 text-sm text-primary font-medium group-hover:gap-3 transition-all">
                            <span>View Details</span>
                            <ExternalLink className="h-4 w-4" />
                        </div>
                    </div>
                </Link>
            </CardContent>
        </Card>
    )
}
