"use client"

import { YouTubeAccount } from "@/types"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Users, Video, AlertCircle, CheckCircle, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface AccountCardProps {
    account: YouTubeAccount
    view?: "grid" | "list"
}

const statusConfig = {
    active: {
        label: "Active",
        color: "bg-green-500",
        icon: CheckCircle,
        badgeVariant: "default" as const,
    },
    expired: {
        label: "Token Expired",
        color: "bg-yellow-500",
        icon: Clock,
        badgeVariant: "secondary" as const,
    },
    error: {
        label: "Error",
        color: "bg-red-500",
        icon: AlertCircle,
        badgeVariant: "destructive" as const,
    },
}

export function AccountCard({ account, view = "grid" }: AccountCardProps) {
    const status = statusConfig[account.status]
    const StatusIcon = status.icon

    if (view === "list") {
        return (
            <Link href={`/dashboard/accounts/${account.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <Avatar className="h-16 w-16">
                                    <AvatarImage src={account.thumbnailUrl} alt={account.channelTitle} />
                                    <AvatarFallback>{account.channelTitle.substring(0, 2).toUpperCase()}</AvatarFallback>
                                </Avatar>
                                <div
                                    className={cn(
                                        "absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-background",
                                        status.color
                                    )}
                                />
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-semibold text-lg truncate">{account.channelTitle}</h3>
                                    <Badge variant={status.badgeVariant} className="flex items-center gap-1">
                                        <StatusIcon className="h-3 w-3" />
                                        {status.label}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                    <div className="flex items-center gap-1">
                                        <Users className="h-4 w-4" />
                                        <span>{account.subscriberCount.toLocaleString()} subscribers</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Video className="h-4 w-4" />
                                        <span>{account.videoCount.toLocaleString()} videos</span>
                                    </div>
                                </div>
                            </div>

                            {account.strikeCount > 0 && (
                                <Badge variant="destructive" className="ml-auto">
                                    {account.strikeCount} Strike{account.strikeCount > 1 ? "s" : ""}
                                </Badge>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </Link>
        )
    }

    return (
        <Link href={`/dashboard/accounts/${account.id}`}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardContent className="p-6">
                    <div className="flex flex-col items-center text-center space-y-4">
                        <div className="relative">
                            <Avatar className="h-20 w-20">
                                <AvatarImage src={account.thumbnailUrl} alt={account.channelTitle} />
                                <AvatarFallback>{account.channelTitle.substring(0, 2).toUpperCase()}</AvatarFallback>
                            </Avatar>
                            <div
                                className={cn(
                                    "absolute -bottom-1 -right-1 h-5 w-5 rounded-full border-2 border-background",
                                    status.color
                                )}
                            />
                        </div>

                        <div className="space-y-2 w-full">
                            <h3 className="font-semibold text-lg line-clamp-2">{account.channelTitle}</h3>
                            <Badge variant={status.badgeVariant} className="flex items-center gap-1 w-fit mx-auto">
                                <StatusIcon className="h-3 w-3" />
                                {status.label}
                            </Badge>
                        </div>

                        <div className="flex flex-col gap-2 text-sm text-muted-foreground w-full">
                            <div className="flex items-center justify-center gap-1">
                                <Users className="h-4 w-4" />
                                <span>{account.subscriberCount.toLocaleString()}</span>
                            </div>
                            <div className="flex items-center justify-center gap-1">
                                <Video className="h-4 w-4" />
                                <span>{account.videoCount.toLocaleString()} videos</span>
                            </div>
                        </div>

                        {account.strikeCount > 0 && (
                            <Badge variant="destructive">
                                {account.strikeCount} Strike{account.strikeCount > 1 ? "s" : ""}
                            </Badge>
                        )}
                    </div>
                </CardContent>
            </Card>
        </Link>
    )
}
