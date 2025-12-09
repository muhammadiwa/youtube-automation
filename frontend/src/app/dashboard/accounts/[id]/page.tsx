"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { accountsApi } from "@/lib/api"
import { YouTubeAccount } from "@/types"
import { AccountHealth, QuotaUsage } from "@/lib/api/accounts"
import {
    RefreshCw,
    Unlink,
    Users,
    Video,
    Eye,
    Clock,
    AlertCircle,
    CheckCircle,
    AlertTriangle,
    TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function AccountDetailPage() {
    const params = useParams()
    const router = useRouter()
    const accountId = params.id as string

    const [account, setAccount] = useState<YouTubeAccount | null>(null)
    const [health, setHealth] = useState<AccountHealth | null>(null)
    const [quota, setQuota] = useState<QuotaUsage | null>(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)
    const [disconnectDialogOpen, setDisconnectDialogOpen] = useState(false)
    const [disconnecting, setDisconnecting] = useState(false)

    useEffect(() => {
        loadAccountData()
    }, [accountId])

    const loadAccountData = async () => {
        try {
            setLoading(true)
            const [accountData, healthData, quotaData] = await Promise.all([
                accountsApi.getAccount(accountId),
                accountsApi.getAccountHealth(accountId),
                accountsApi.getQuotaUsage(accountId),
            ])
            setAccount(accountData)
            setHealth(healthData)
            setQuota(quotaData)
        } catch (error) {
            console.error("Failed to load account data:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleRefreshToken = async () => {
        try {
            setRefreshing(true)
            await accountsApi.refreshToken(accountId)
            await loadAccountData()
        } catch (error) {
            console.error("Failed to refresh token:", error)
        } finally {
            setRefreshing(false)
        }
    }

    const handleDisconnect = async () => {
        try {
            setDisconnecting(true)
            await accountsApi.disconnectAccount(accountId)
            router.push("/dashboard/accounts")
        } catch (error) {
            console.error("Failed to disconnect account:", error)
            setDisconnecting(false)
        }
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

    const getQuotaColor = (percentage: number) => {
        if (percentage >= 90) return "bg-red-500"
        if (percentage >= 75) return "bg-yellow-500"
        return "bg-green-500"
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Accounts", href: "/dashboard/accounts" },
                    { label: "Loading..." },
                ]}
            >
                <div className="space-y-6">
                    <Skeleton className="h-32" />
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {[1, 2, 3, 4].map((i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                </div>
            </DashboardLayout>
        )
    }

    if (!account) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Accounts", href: "/dashboard/accounts" },
                    { label: "Not Found" },
                ]}
            >
                <div className="text-center py-12">
                    <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Account not found</h3>
                    <p className="text-muted-foreground mb-4">
                        The account you're looking for doesn't exist or has been removed.
                    </p>
                    <Button onClick={() => router.push("/dashboard/accounts")}>Back to Accounts</Button>
                </div>
            </DashboardLayout>
        )
    }

    const status = statusConfig[account.status]
    const StatusIcon = status.icon

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Accounts", href: "/dashboard/accounts" },
                { label: account.channelTitle },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <Card>
                    <CardContent className="p-6">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                            <Avatar className="h-20 w-20">
                                <AvatarImage src={account.thumbnailUrl} alt={account.channelTitle} />
                                <AvatarFallback>{account.channelTitle.substring(0, 2).toUpperCase()}</AvatarFallback>
                            </Avatar>

                            <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                    <h1 className="text-2xl font-bold">{account.channelTitle}</h1>
                                    <Badge variant={status.badgeVariant} className="flex items-center gap-1">
                                        <StatusIcon className="h-3 w-3" />
                                        {status.label}
                                    </Badge>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Channel ID: {account.channelId}
                                </p>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Clock className="h-4 w-4" />
                                    <span>
                                        Last synced: {new Date(account.lastSyncAt).toLocaleString()}
                                    </span>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    onClick={handleRefreshToken}
                                    disabled={refreshing}
                                >
                                    <RefreshCw className={cn("mr-2 h-4 w-4", refreshing && "animate-spin")} />
                                    Refresh Token
                                </Button>
                                <Button
                                    variant="destructive"
                                    onClick={() => setDisconnectDialogOpen(true)}
                                >
                                    <Unlink className="mr-2 h-4 w-4" />
                                    Disconnect
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Subscribers</CardTitle>
                            <Users className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {account.subscriberCount.toLocaleString()}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Videos</CardTitle>
                            <Video className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {account.videoCount.toLocaleString()}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Monetization</CardTitle>
                            <TrendingUp className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {account.isMonetized ? (
                                    <Badge variant="default">Enabled</Badge>
                                ) : (
                                    <Badge variant="secondary">Disabled</Badge>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Live Streaming</CardTitle>
                            <Eye className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">
                                {account.hasLiveStreamingEnabled ? (
                                    <Badge variant="default">Enabled</Badge>
                                ) : (
                                    <Badge variant="secondary">Disabled</Badge>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Token Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Token Status</CardTitle>
                        <CardDescription>OAuth token information and expiration</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Status</span>
                            <Badge variant={status.badgeVariant} className="flex items-center gap-1">
                                <StatusIcon className="h-3 w-3" />
                                {status.label}
                            </Badge>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Expires At</span>
                            <span className="text-sm text-muted-foreground">
                                {new Date(account.tokenExpiresAt).toLocaleString()}
                            </span>
                        </div>
                        {account.status === "expired" && (
                            <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                <p className="text-sm text-yellow-600 dark:text-yellow-400">
                                    Token has expired. Please refresh to continue using this account.
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Quota Usage */}
                {quota && (
                    <Card>
                        <CardHeader>
                            <CardTitle>API Quota Usage</CardTitle>
                            <CardDescription>Daily YouTube API quota consumption</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="font-medium">Usage</span>
                                    <span className="text-muted-foreground">
                                        {quota.used.toLocaleString()} / {quota.limit.toLocaleString()} ({quota.percentage}%)
                                    </span>
                                </div>
                                <Progress value={quota.percentage} className="h-2" />
                            </div>
                            {quota.percentage >= 80 && (
                                <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
                                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                    <p className="text-sm text-yellow-600 dark:text-yellow-400">
                                        Quota usage is high. Consider optimizing API calls or upgrading your plan.
                                    </p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Strike Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Strike Status</CardTitle>
                        <CardDescription>YouTube community guidelines strikes</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {account.strikeCount === 0 ? (
                            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-md">
                                <CheckCircle className="h-4 w-4 text-green-500" />
                                <p className="text-sm text-green-600 dark:text-green-400">
                                    No strikes. Your account is in good standing.
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-md">
                                    <AlertCircle className="h-4 w-4 text-red-500" />
                                    <p className="text-sm text-red-600 dark:text-red-400">
                                        {account.strikeCount} active strike{account.strikeCount > 1 ? "s" : ""} on this account.
                                    </p>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    View detailed strike information and appeal options in the Strikes dashboard.
                                </p>
                                <Button variant="outline" onClick={() => router.push("/dashboard/strikes")}>
                                    View Strike Details
                                </Button>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Disconnect Confirmation Dialog */}
            <Dialog open={disconnectDialogOpen} onOpenChange={setDisconnectDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Disconnect Account</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to disconnect {account.channelTitle}? This will remove all
                            associated data and you'll need to reconnect to use this account again.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDisconnectDialogOpen(false)}
                            disabled={disconnecting}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDisconnect}
                            disabled={disconnecting}
                        >
                            {disconnecting ? "Disconnecting..." : "Disconnect"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
