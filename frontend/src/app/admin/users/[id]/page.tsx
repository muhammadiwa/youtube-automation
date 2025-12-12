"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
    User,
    Mail,
    Calendar,
    Clock,
    Shield,
    AlertTriangle,
    Youtube,
    Video,
    Activity,
    HardDrive,
    Wifi,
    Sparkles,
    ArrowLeft,
    Loader2,
    AlertCircle,
    UserX,
    UserCheck,
    KeyRound,
    UserCog,
    CreditCard,
    History,
    Globe,
    Zap,
    TrendingUp,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Separator } from "@/components/ui/separator"
import { format, formatDistanceToNow } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { UserDetail, UserStatus } from "@/types/admin"
import { SuspendUserDialog } from "@/components/admin/users/suspend-user-dialog"
import { ActivateUserDialog } from "@/components/admin/users/activate-user-dialog"
import { ResetPasswordDialog } from "@/components/admin/users/reset-password-dialog"
import { ImpersonateUserDialog } from "@/components/admin/users/impersonate-user-dialog"

const statusConfig: Record<UserStatus, { color: string; bg: string; gradient: string }> = {
    active: {
        color: "text-emerald-600 dark:text-emerald-400",
        bg: "bg-emerald-500/10 border-emerald-500/20",
        gradient: "from-emerald-500 to-emerald-600",
    },
    suspended: {
        color: "text-red-600 dark:text-red-400",
        bg: "bg-red-500/10 border-red-500/20",
        gradient: "from-red-500 to-red-600",
    },
    pending: {
        color: "text-amber-600 dark:text-amber-400",
        bg: "bg-amber-500/10 border-amber-500/20",
        gradient: "from-amber-500 to-amber-600",
    },
}

const statusLabels: Record<UserStatus, string> = {
    active: "Active",
    suspended: "Suspended",
    pending: "Pending",
}

export default function AdminUserDetailPage() {
    const params = useParams()
    const router = useRouter()
    const userId = params.id as string

    const [user, setUser] = useState<UserDetail | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Dialog states
    const [showSuspendDialog, setShowSuspendDialog] = useState(false)
    const [showActivateDialog, setShowActivateDialog] = useState(false)
    const [showResetPasswordDialog, setShowResetPasswordDialog] = useState(false)
    const [showImpersonateDialog, setShowImpersonateDialog] = useState(false)

    const fetchUser = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await adminApi.getUserDetail(userId)
            setUser(data)
        } catch (err) {
            console.error("Failed to fetch user:", err)
            setError("Failed to load user details. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [userId])

    useEffect(() => {
        fetchUser()
    }, [fetchUser])

    const handleActionComplete = () => {
        fetchUser()
    }

    if (isLoading) {
        return (
            <AdminLayout breadcrumbs={[{ label: "Users", href: "/admin/users" }, { label: "Loading..." }]}>
                <div className="flex flex-col items-center justify-center py-32">
                    <div className="relative">
                        <div className="h-20 w-20 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
                        <User className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-8 w-8 text-blue-500" />
                    </div>
                    <p className="mt-6 text-muted-foreground">Loading user details...</p>
                </div>
            </AdminLayout>
        )
    }

    if (error || !user) {
        return (
            <AdminLayout breadcrumbs={[{ label: "Users", href: "/admin/users" }, { label: "Error" }]}>
                <div className="flex flex-col items-center justify-center py-32 text-center">
                    <div className="h-20 w-20 rounded-full bg-red-500/10 flex items-center justify-center mb-6">
                        <AlertCircle className="h-10 w-10 text-red-500" />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Failed to Load User</h2>
                    <p className="text-muted-foreground mb-6 max-w-md">{error || "User not found"}</p>
                    <div className="flex gap-3">
                        <Button variant="outline" onClick={() => router.push("/admin/users")} className="rounded-xl">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Users
                        </Button>
                        <Button onClick={fetchUser} className="rounded-xl bg-blue-500 hover:bg-blue-600">
                            Try Again
                        </Button>
                    </div>
                </div>
            </AdminLayout>
        )
    }

    return (
        <AdminLayout breadcrumbs={[{ label: "Users", href: "/admin/users" }, { label: user.name }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between"
                >
                    <div className="flex items-start gap-6">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push("/admin/users")}
                            className="h-10 w-10 rounded-xl shrink-0"
                        >
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div className="flex items-center gap-5">
                            <div className={cn(
                                "flex h-20 w-20 items-center justify-center rounded-2xl text-white text-3xl font-bold shadow-xl",
                                "bg-gradient-to-br",
                                statusConfig[user.status].gradient
                            )}>
                                {user.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center gap-3 flex-wrap">
                                    <h1 className="text-3xl font-bold tracking-tight">{user.name}</h1>
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "text-sm font-semibold px-3 py-1 rounded-lg",
                                            statusConfig[user.status].bg,
                                            statusConfig[user.status].color
                                        )}
                                    >
                                        {statusLabels[user.status]}
                                    </Badge>
                                    {user.is_2fa_enabled && (
                                        <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/20 rounded-lg">
                                            <Shield className="h-3.5 w-3.5 mr-1.5" />
                                            2FA Enabled
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-muted-foreground flex items-center gap-2 text-lg">
                                    <Mail className="h-5 w-5" />
                                    {user.email}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap gap-3 ml-16 lg:ml-0">
                        {user.status === "suspended" ? (
                            <Button
                                onClick={() => setShowActivateDialog(true)}
                                className="rounded-xl bg-emerald-500 hover:bg-emerald-600 shadow-lg shadow-emerald-500/20"
                            >
                                <UserCheck className="h-4 w-4 mr-2" />
                                Activate User
                            </Button>
                        ) : (
                            <Button
                                variant="outline"
                                onClick={() => setShowSuspendDialog(true)}
                                className="rounded-xl border-red-500/30 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                                <UserX className="h-4 w-4 mr-2" />
                                Suspend User
                            </Button>
                        )}
                        <Button variant="outline" onClick={() => setShowResetPasswordDialog(true)} className="rounded-xl">
                            <KeyRound className="h-4 w-4 mr-2" />
                            Reset Password
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => setShowImpersonateDialog(true)}
                            className="rounded-xl border-purple-500/30 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20"
                        >
                            <UserCog className="h-4 w-4 mr-2" />
                            Impersonate
                        </Button>
                    </div>
                </motion.div>

                {/* Warning Banner */}
                {user.warning_count > 0 && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <Card className="border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-orange-500/10">
                            <CardContent className="p-5 flex items-center gap-4">
                                <div className="h-12 w-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                                    <AlertTriangle className="h-6 w-6 text-amber-600" />
                                </div>
                                <div>
                                    <p className="font-semibold text-amber-700 dark:text-amber-400">
                                        User has {user.warning_count} warning{user.warning_count > 1 ? "s" : ""}
                                    </p>
                                    <p className="text-sm text-amber-600/80 dark:text-amber-500/80">
                                        Review the user&apos;s activity and consider appropriate action
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}

                {/* Main Content */}
                <div className="grid gap-8 lg:grid-cols-3">
                    {/* Left Column - User Info */}
                    <div className="space-y-6">
                        {/* Profile Info */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900 overflow-hidden">
                                <CardHeader className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200/60 dark:border-slate-700/60">
                                    <CardTitle className="text-lg flex items-center gap-3">
                                        <div className="h-9 w-9 rounded-xl bg-blue-500/10 flex items-center justify-center">
                                            <User className="h-5 w-5 text-blue-500" />
                                        </div>
                                        Profile Information
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-6 space-y-5">
                                    <InfoRow
                                        icon={Globe}
                                        label="User ID"
                                        value={<code className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{user.id.slice(0, 12)}...</code>}
                                    />
                                    <Separator />
                                    <InfoRow
                                        icon={Calendar}
                                        label="Registered"
                                        value={format(new Date(user.created_at), "PPP")}
                                    />
                                    <InfoRow
                                        icon={Clock}
                                        label="Last Login"
                                        value={user.last_login_at
                                            ? formatDistanceToNow(new Date(user.last_login_at), { addSuffix: true })
                                            : "Never"}
                                    />
                                    <InfoRow
                                        icon={AlertTriangle}
                                        label="Warnings"
                                        value={
                                            <Badge variant={user.warning_count > 0 ? "destructive" : "secondary"} className="rounded-lg">
                                                {user.warning_count}
                                            </Badge>
                                        }
                                    />
                                </CardContent>
                            </Card>
                        </motion.div>

                        {/* Subscription Info */}
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900 overflow-hidden">
                                <CardHeader className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200/60 dark:border-slate-700/60">
                                    <CardTitle className="text-lg flex items-center gap-3">
                                        <div className="h-9 w-9 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                                            <CreditCard className="h-5 w-5 text-emerald-500" />
                                        </div>
                                        Subscription
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-6">
                                    {user.subscription?.plan_name ? (
                                        <div className="space-y-5">
                                            <div className="flex items-center justify-between">
                                                <span className="text-muted-foreground">Plan</span>
                                                <Badge className="capitalize rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white border-0">
                                                    {user.subscription.plan_name}
                                                </Badge>
                                            </div>
                                            <Separator />
                                            <div className="flex items-center justify-between">
                                                <span className="text-muted-foreground">Status</span>
                                                <span className="capitalize font-medium">{user.subscription.status || "N/A"}</span>
                                            </div>
                                            {user.subscription.end_date && (
                                                <>
                                                    <Separator />
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-muted-foreground">Expires</span>
                                                        <span className="font-medium">{format(new Date(user.subscription.end_date), "PP")}</span>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="text-center py-8">
                                            <div className="h-14 w-14 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-3">
                                                <CreditCard className="h-7 w-7 text-muted-foreground" />
                                            </div>
                                            <p className="text-muted-foreground">No active subscription</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    </div>

                    {/* Right Column - Tabs */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="lg:col-span-2"
                    >
                        <Tabs defaultValue="usage" className="space-y-6">
                            <TabsList className="bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                                <TabsTrigger value="usage" className="rounded-md data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm">
                                    <Zap className="h-4 w-4 mr-2" />
                                    Usage Stats
                                </TabsTrigger>
                                <TabsTrigger value="accounts" className="rounded-md data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm">
                                    <Youtube className="h-4 w-4 mr-2" />
                                    YouTube Accounts
                                </TabsTrigger>
                                <TabsTrigger value="activity" className="rounded-md data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:shadow-sm">
                                    <History className="h-4 w-4 mr-2" />
                                    Activity
                                </TabsTrigger>
                            </TabsList>

                            {/* Usage Stats Tab */}
                            <TabsContent value="usage">
                                <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                    <CardHeader>
                                        <CardTitle className="text-xl">Resource Usage</CardTitle>
                                        <CardDescription>Current usage statistics for this user</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                            <UsageStatCard
                                                icon={Video}
                                                label="Total Videos"
                                                value={user.usage_stats.total_videos}
                                                gradient="from-pink-500 to-rose-500"
                                            />
                                            <UsageStatCard
                                                icon={Activity}
                                                label="Total Streams"
                                                value={user.usage_stats.total_streams}
                                                gradient="from-red-500 to-orange-500"
                                            />
                                            <UsageStatCard
                                                icon={HardDrive}
                                                label="Storage Used"
                                                value={`${user.usage_stats.storage_used_gb.toFixed(2)} GB`}
                                                gradient="from-blue-500 to-cyan-500"
                                            />
                                            <UsageStatCard
                                                icon={Wifi}
                                                label="Bandwidth Used"
                                                value={`${user.usage_stats.bandwidth_used_gb.toFixed(2)} GB`}
                                                gradient="from-cyan-500 to-teal-500"
                                            />
                                            <UsageStatCard
                                                icon={Sparkles}
                                                label="AI Generations"
                                                value={user.usage_stats.ai_generations_used}
                                                gradient="from-purple-500 to-violet-500"
                                            />
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            {/* YouTube Accounts Tab */}
                            <TabsContent value="accounts">
                                <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                    <CardHeader>
                                        <CardTitle className="text-xl flex items-center gap-3">
                                            <Youtube className="h-6 w-6 text-red-500" />
                                            Connected YouTube Accounts
                                        </CardTitle>
                                        <CardDescription>
                                            {user.connected_accounts.length} account{user.connected_accounts.length !== 1 ? "s" : ""} connected
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {user.connected_accounts.length === 0 ? (
                                            <div className="text-center py-12">
                                                <div className="h-16 w-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
                                                    <Youtube className="h-8 w-8 text-red-500" />
                                                </div>
                                                <p className="text-muted-foreground">No YouTube accounts connected</p>
                                            </div>
                                        ) : (
                                            <div className="space-y-4">
                                                {user.connected_accounts.map((account) => (
                                                    <div
                                                        key={account.id}
                                                        className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                                    >
                                                        <div className="flex items-center gap-4">
                                                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-500/10">
                                                                <Youtube className="h-6 w-6 text-red-500" />
                                                            </div>
                                                            <div>
                                                                <p className="font-semibold">{account.channel_name}</p>
                                                                <p className="text-sm text-muted-foreground font-mono">{account.channel_id}</p>
                                                            </div>
                                                        </div>
                                                        <div className="text-right">
                                                            <p className="font-semibold flex items-center gap-2 justify-end">
                                                                <TrendingUp className="h-4 w-4 text-emerald-500" />
                                                                {account.subscriber_count?.toLocaleString() || "N/A"} subs
                                                            </p>
                                                            <Badge variant={account.is_active ? "default" : "secondary"} className="mt-1 rounded-lg">
                                                                {account.is_active ? "Active" : "Inactive"}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            {/* Activity History Tab */}
                            <TabsContent value="activity">
                                <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                                    <CardHeader>
                                        <CardTitle className="text-xl flex items-center gap-3">
                                            <History className="h-6 w-6 text-orange-500" />
                                            Recent Activity
                                        </CardTitle>
                                        <CardDescription>Last 20 activities for this user</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {user.activity_history.length === 0 ? (
                                            <div className="text-center py-12">
                                                <div className="h-16 w-16 rounded-full bg-orange-500/10 flex items-center justify-center mx-auto mb-4">
                                                    <History className="h-8 w-8 text-orange-500" />
                                                </div>
                                                <p className="text-muted-foreground">No activity recorded</p>
                                            </div>
                                        ) : (
                                            <div className="overflow-x-auto">
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow className="hover:bg-transparent">
                                                            <TableHead className="font-semibold">Action</TableHead>
                                                            <TableHead className="font-semibold">IP Address</TableHead>
                                                            <TableHead className="font-semibold">Time</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {user.activity_history.map((activity) => (
                                                            <TableRow key={activity.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                                                                <TableCell className="font-medium">{activity.action}</TableCell>
                                                                <TableCell className="text-muted-foreground font-mono text-sm">
                                                                    {activity.ip_address || "N/A"}
                                                                </TableCell>
                                                                <TableCell className="text-muted-foreground">
                                                                    {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </motion.div>
                </div>
            </div>

            {/* Dialogs */}
            <SuspendUserDialog
                open={showSuspendDialog}
                onOpenChange={setShowSuspendDialog}
                user={user}
                onSuccess={handleActionComplete}
            />
            <ActivateUserDialog
                open={showActivateDialog}
                onOpenChange={setShowActivateDialog}
                user={user}
                onSuccess={handleActionComplete}
            />
            <ResetPasswordDialog
                open={showResetPasswordDialog}
                onOpenChange={setShowResetPasswordDialog}
                user={user}
                onSuccess={handleActionComplete}
            />
            <ImpersonateUserDialog
                open={showImpersonateDialog}
                onOpenChange={setShowImpersonateDialog}
                user={user}
            />
        </AdminLayout>
    )
}

function InfoRow({
    icon: Icon,
    label,
    value,
}: {
    icon: React.ComponentType<{ className?: string }>
    label: string
    value: React.ReactNode
}) {
    return (
        <div className="flex items-center justify-between">
            <span className="text-muted-foreground flex items-center gap-2">
                <Icon className="h-4 w-4" />
                {label}
            </span>
            <span className="font-medium">{value}</span>
        </div>
    )
}

function UsageStatCard({
    icon: Icon,
    label,
    value,
    gradient,
}: {
    icon: React.ComponentType<{ className?: string }>
    label: string
    value: string | number
    gradient: string
}) {
    return (
        <div className="flex items-center gap-4 p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors group">
            <div className={cn(
                "flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg group-hover:scale-110 transition-transform",
                gradient
            )}>
                <Icon className="h-7 w-7 text-white" />
            </div>
            <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="text-2xl font-bold">{value}</p>
            </div>
        </div>
    )
}
