"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Gift,
    Plus,
    Search,
    Percent,
    DollarSign,
    Calendar,
    Users,
    MoreHorizontal,
    Pencil,
    Trash2,
    CheckCircle,
    XCircle,
    AlertCircle,
    RefreshCcw,
    Copy,
    Check,
    TrendingUp,
    Trophy,
    UserPlus,
    Target,
    Ticket,
    ArrowUpRight,
    ArrowDownRight,
    Minus,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { DiscountCode, DiscountCodeListResponse, PromotionAnalyticsResponse } from "@/types/admin"
import { DiscountCodeForm } from "@/components/admin/promotions/discount-code-form"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"

function StatsCard({
    title,
    value,
    icon: Icon,
    gradient,
    delay = 0,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    gradient: string
    delay?: number
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay }}
        >
            <Card className="relative overflow-hidden border border-slate-200/60 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-all duration-300 group bg-white dark:bg-slate-900">
                <div className={cn("absolute inset-0 opacity-[0.03] group-hover:opacity-[0.06] transition-opacity bg-gradient-to-br", gradient)} />
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
                            <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
                        </div>
                        <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br shadow-sm",
                            gradient
                        )}>
                            <Icon className="h-5 w-5 text-white" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}


export default function AdminPromotionsPage() {
    const [discountCodes, setDiscountCodes] = useState<DiscountCodeListResponse | null>(null)
    const [analytics, setAnalytics] = useState<PromotionAnalyticsResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [page, setPage] = useState(1)
    const pageSize = 10
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [editingCode, setEditingCode] = useState<DiscountCode | null>(null)
    const [deleteCode, setDeleteCode] = useState<DiscountCode | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)
    const [copiedCode, setCopiedCode] = useState<string | null>(null)

    const fetchDiscountCodes = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await adminApi.getDiscountCodes({
                page,
                page_size: pageSize,
                is_active: statusFilter === "all" ? undefined : statusFilter === "active",
                search: search || undefined,
            })
            setDiscountCodes(data)
        } catch (err) {
            console.error("Failed to fetch discount codes:", err)
            setError("Failed to load discount codes. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }, [page, statusFilter, search])

    const fetchAnalytics = useCallback(async () => {
        setIsLoadingAnalytics(true)
        try {
            const data = await adminApi.getPromotionAnalytics()
            setAnalytics(data)
        } catch (err) {
            console.error("Failed to fetch analytics:", err)
        } finally {
            setIsLoadingAnalytics(false)
        }
    }, [])

    useEffect(() => {
        fetchDiscountCodes()
        fetchAnalytics()
    }, [fetchDiscountCodes, fetchAnalytics])

    const handleSearch = (value: string) => {
        setSearch(value)
        setPage(1)
    }

    const handleStatusFilter = (value: string) => {
        setStatusFilter(value)
        setPage(1)
    }

    const handleCreateNew = () => {
        setEditingCode(null)
        setIsFormOpen(true)
    }

    const handleEdit = (code: DiscountCode) => {
        setEditingCode(code)
        setIsFormOpen(true)
    }

    const handleDelete = async () => {
        if (!deleteCode) return
        setIsDeleting(true)
        try {
            await adminApi.deleteDiscountCode(deleteCode.id)
            setDeleteCode(null)
            fetchDiscountCodes()
        } catch (err) {
            console.error("Failed to delete discount code:", err)
        } finally {
            setIsDeleting(false)
        }
    }

    const handleFormSuccess = () => {
        setIsFormOpen(false)
        setEditingCode(null)
        fetchDiscountCodes()
    }

    const handleCopyCode = async (code: string) => {
        try {
            await navigator.clipboard.writeText(code)
            setCopiedCode(code)
            setTimeout(() => setCopiedCode(null), 2000)
        } catch (err) {
            console.error("Failed to copy code:", err)
        }
    }

    const totalCodes = discountCodes?.total || 0
    const activeCodes = discountCodes?.items.filter(c => c.is_active && c.is_valid).length || 0
    const totalUsage = discountCodes?.items.reduce((sum, c) => sum + c.usage_count, 0) || 0


    return (
        <AdminLayout breadcrumbs={[{ label: "Promotions" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
                            Promotional Tools
                        </h1>
                        <p className="text-muted-foreground">
                            Manage discount codes and promotional campaigns
                        </p>
                    </div>
                    <Button onClick={handleCreateNew} className="rounded-xl gap-2">
                        <Plus className="h-4 w-4" />
                        Create Discount Code
                    </Button>
                </motion.div>

                {/* Stats Cards */}
                <div className="grid gap-4 sm:grid-cols-3">
                    <StatsCard title="Total Codes" value={totalCodes} icon={Gift} gradient="from-violet-500 to-violet-600" delay={0} />
                    <StatsCard title="Active Codes" value={activeCodes} icon={CheckCircle} gradient="from-emerald-500 to-emerald-600" delay={0.05} />
                    <StatsCard title="Total Usage" value={totalUsage} icon={Users} gradient="from-blue-500 to-blue-600" delay={0.1} />
                </div>

                {/* Filters */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardContent className="p-4">
                            <div className="flex flex-col sm:flex-row gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input placeholder="Search by code..." value={search} onChange={(e) => handleSearch(e.target.value)} className="pl-9" />
                                </div>
                                <Select value={statusFilter} onValueChange={handleStatusFilter}>
                                    <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="inactive">Inactive</SelectItem>
                                    </SelectContent>
                                </Select>
                                <Button variant="outline" size="icon" onClick={fetchDiscountCodes}><RefreshCcw className="h-4 w-4" /></Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Discount Codes Table */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2"><Gift className="h-5 w-5" />Discount Codes</CardTitle>
                            <CardDescription>Manage discount codes with percentage or fixed discounts</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex flex-col items-center justify-center py-12">
                                    <div className="relative">
                                        <div className="h-12 w-12 rounded-full border-4 border-violet-500/20 border-t-violet-500 animate-spin" />
                                        <Gift className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-5 w-5 text-violet-500" />
                                    </div>
                                    <p className="mt-4 text-muted-foreground">Loading discount codes...</p>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center mb-3">
                                        <AlertCircle className="h-6 w-6 text-red-500" />
                                    </div>
                                    <p className="text-red-500 mb-2">{error}</p>
                                    <Button variant="outline" onClick={fetchDiscountCodes}>Try Again</Button>
                                </div>
                            ) : discountCodes?.items.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                                        <Gift className="h-6 w-6 text-muted-foreground" />
                                    </div>
                                    <p className="text-muted-foreground mb-4">No discount codes found</p>
                                    <Button onClick={handleCreateNew} className="gap-2"><Plus className="h-4 w-4" />Create First Code</Button>
                                </div>
                            ) : (
                                <>
                                    <div className="rounded-lg border overflow-hidden">
                                        <Table>
                                            <TableHeader>
                                                <TableRow className="bg-slate-50 dark:bg-slate-800/50">
                                                    <TableHead>Code</TableHead>
                                                    <TableHead>Discount</TableHead>
                                                    <TableHead>Validity</TableHead>
                                                    <TableHead>Usage</TableHead>
                                                    <TableHead>Status</TableHead>
                                                    <TableHead className="w-[50px]"></TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {discountCodes?.items.map((code) => (
                                                    <TableRow key={code.id} className="group">
                                                        <TableCell>
                                                            <div className="flex items-center gap-2">
                                                                <code className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-sm font-mono">{code.code}</code>
                                                                <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => handleCopyCode(code.code)}>
                                                                    {copiedCode === code.code ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                                                                </Button>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <div className="flex items-center gap-2">
                                                                {code.discount_type === "percentage" ? (
                                                                    <><Percent className="h-4 w-4 text-violet-500" /><span className="font-medium">{code.discount_value}%</span></>
                                                                ) : (
                                                                    <><DollarSign className="h-4 w-4 text-emerald-500" /><span className="font-medium">${code.discount_value}</span></>
                                                                )}
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <div className="flex items-center gap-1 text-sm">
                                                                <Calendar className="h-3 w-3 text-muted-foreground" />
                                                                <span>{format(new Date(code.valid_from), "MMM d")} - {format(new Date(code.valid_until), "MMM d, yyyy")}</span>
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            <div className="flex items-center gap-1">
                                                                <Users className="h-3 w-3 text-muted-foreground" />
                                                                <span>{code.usage_count}</span>
                                                                {code.usage_limit && <span className="text-muted-foreground">/ {code.usage_limit}</span>}
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            {code.is_active && code.is_valid ? (
                                                                <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"><CheckCircle className="h-3 w-3 mr-1" />Active</Badge>
                                                            ) : !code.is_active ? (
                                                                <Badge variant="secondary" className="bg-slate-100 dark:bg-slate-800"><XCircle className="h-3 w-3 mr-1" />Disabled</Badge>
                                                            ) : (
                                                                <Badge variant="secondary" className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"><AlertCircle className="h-3 w-3 mr-1" />Expired</Badge>
                                                            )}
                                                        </TableCell>
                                                        <TableCell>
                                                            <DropdownMenu>
                                                                <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                                                                <DropdownMenuContent align="end">
                                                                    <DropdownMenuItem onClick={() => handleEdit(code)}><Pencil className="h-4 w-4 mr-2" />Edit</DropdownMenuItem>
                                                                    <DropdownMenuSeparator />
                                                                    <DropdownMenuItem onClick={() => setDeleteCode(code)} className="text-red-600 dark:text-red-400"><Trash2 className="h-4 w-4 mr-2" />Delete</DropdownMenuItem>
                                                                </DropdownMenuContent>
                                                            </DropdownMenu>
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </div>
                                    {discountCodes && discountCodes.total_pages > 1 && (
                                        <div className="flex items-center justify-between mt-4">
                                            <p className="text-sm text-muted-foreground">Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, discountCodes.total)} of {discountCodes.total} codes</p>
                                            <div className="flex gap-2">
                                                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>Previous</Button>
                                                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(discountCodes.total_pages, p + 1))} disabled={page === discountCodes.total_pages}>Next</Button>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>


                {/* Analytics Section */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="h-5 w-5" />Promotion Analytics</CardTitle>
                                <CardDescription>Performance metrics and insights for your promotional campaigns</CardDescription>
                            </div>
                            <Button variant="outline" size="sm" onClick={fetchAnalytics} disabled={isLoadingAnalytics}>
                                <RefreshCcw className={cn("h-4 w-4 mr-2", isLoadingAnalytics && "animate-spin")} />
                                Refresh
                            </Button>
                        </CardHeader>
                        <CardContent>
                            {isLoadingAnalytics ? (
                                <div className="flex items-center justify-center py-12">
                                    <div className="h-8 w-8 rounded-full border-4 border-violet-500/20 border-t-violet-500 animate-spin" />
                                </div>
                            ) : analytics ? (
                                <div className="space-y-6">
                                    {/* Overview Stats - Row 1 */}
                                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-violet-50 to-violet-100 dark:from-violet-900/20 dark:to-violet-800/20 border border-violet-200 dark:border-violet-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-violet-600 dark:text-violet-400">Discount Codes</span>
                                                <Gift className="h-4 w-4 text-violet-600 dark:text-violet-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-violet-900 dark:text-violet-100">{analytics.total_discount_codes}</p>
                                            <div className="flex items-center gap-1 mt-1">
                                                <Badge className="bg-violet-500/20 text-violet-700 dark:text-violet-300 text-[10px] px-1.5">{analytics.active_discount_codes} active</Badge>
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-50 to-cyan-100 dark:from-cyan-900/20 dark:to-cyan-800/20 border border-cyan-200 dark:border-cyan-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-cyan-600 dark:text-cyan-400">Trial Codes</span>
                                                <Ticket className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-cyan-900 dark:text-cyan-100">{analytics.total_trial_codes}</p>
                                            <div className="flex items-center gap-1 mt-1">
                                                <Badge className="bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 text-[10px] px-1.5">{analytics.active_trial_codes} active</Badge>
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border border-emerald-200 dark:border-emerald-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Total Usage</span>
                                                <Users className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">{analytics.total_discount_usage}</p>
                                            <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70 mt-1">Times codes were used</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-rose-50 to-rose-100 dark:from-rose-900/20 dark:to-rose-800/20 border border-rose-200 dark:border-rose-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-rose-600 dark:text-rose-400">Total Discount</span>
                                                <DollarSign className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-rose-900 dark:text-rose-100">${analytics.total_discount_amount.toFixed(2)}</p>
                                            <p className="text-xs text-rose-600/70 dark:text-rose-400/70 mt-1">Amount given in discounts</p>
                                        </div>
                                    </div>

                                    {/* Conversion & Revenue Stats - Row 2 */}
                                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-blue-600 dark:text-blue-400">Overall Conversion</span>
                                                <Target className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">{(analytics.overall_conversion_rate * 100).toFixed(1)}%</p>
                                            <div className="flex items-center gap-1 mt-1 text-xs text-blue-600/70 dark:text-blue-400/70">
                                                {analytics.overall_conversion_rate > 0.1 ? (
                                                    <><ArrowUpRight className="h-3 w-3 text-emerald-500" /><span className="text-emerald-600">Good</span></>
                                                ) : analytics.overall_conversion_rate > 0 ? (
                                                    <><Minus className="h-3 w-3 text-amber-500" /><span className="text-amber-600">Average</span></>
                                                ) : (
                                                    <><ArrowDownRight className="h-3 w-3 text-red-500" /><span className="text-red-600">Low</span></>
                                                )}
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-800/20 border border-indigo-200 dark:border-indigo-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Discount Conversion</span>
                                                <Percent className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">{(analytics.discount_conversion_rate * 100).toFixed(1)}%</p>
                                            <p className="text-xs text-indigo-600/70 dark:text-indigo-400/70 mt-1">Users who used discounts</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 border border-amber-200 dark:border-amber-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-amber-600 dark:text-amber-400">Revenue Impact</span>
                                                <Trophy className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">${analytics.discount_revenue_impact.toFixed(2)}</p>
                                            <p className="text-xs text-amber-600/70 dark:text-amber-400/70 mt-1">Revenue from promo users</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-900/20 dark:to-pink-800/20 border border-pink-200 dark:border-pink-800">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-sm font-medium text-pink-600 dark:text-pink-400">Referral Conversion</span>
                                                <UserPlus className="h-4 w-4 text-pink-600 dark:text-pink-400" />
                                            </div>
                                            <p className="text-2xl font-bold text-pink-900 dark:text-pink-100">{(analytics.referral_conversion_rate * 100).toFixed(1)}%</p>
                                            <p className="text-xs text-pink-600/70 dark:text-pink-400/70 mt-1">Referral success rate</p>
                                        </div>
                                    </div>

                                    {/* Referral Analytics Section */}
                                    {analytics.referral_analytics && (
                                        <div className="p-5 rounded-xl border bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-800/30">
                                            <h4 className="font-semibold mb-4 flex items-center gap-2">
                                                <UserPlus className="h-4 w-4 text-pink-500" />
                                                Referral Program Performance
                                            </h4>
                                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                                                <div className="text-center p-3 rounded-lg bg-white dark:bg-slate-900 border">
                                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{analytics.referral_analytics.total_referrals}</p>
                                                    <p className="text-xs text-muted-foreground">Total Referrals</p>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-white dark:bg-slate-900 border">
                                                    <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{analytics.referral_analytics.successful_referrals}</p>
                                                    <p className="text-xs text-muted-foreground">Successful</p>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-white dark:bg-slate-900 border">
                                                    <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{analytics.referral_analytics.pending_referrals}</p>
                                                    <p className="text-xs text-muted-foreground">Pending</p>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-white dark:bg-slate-900 border">
                                                    <p className="text-2xl font-bold text-violet-600 dark:text-violet-400">${analytics.referral_analytics.total_rewards_given.toFixed(2)}</p>
                                                    <p className="text-xs text-muted-foreground">Rewards Given</p>
                                                </div>
                                                <div className="text-center p-3 rounded-lg bg-white dark:bg-slate-900 border">
                                                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{(analytics.referral_analytics.conversion_rate * 100).toFixed(1)}%</p>
                                                    <p className="text-xs text-muted-foreground">Conversion Rate</p>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Charts Grid */}
                                    <div className="grid gap-6 lg:grid-cols-2">
                                        {/* Top Discount Codes Chart */}
                                        <div className="p-5 rounded-xl border bg-slate-50/50 dark:bg-slate-800/30">
                                            <h4 className="font-semibold mb-4 flex items-center gap-2">
                                                <Gift className="h-4 w-4 text-violet-500" />
                                                Top Discount Codes by Usage
                                            </h4>
                                            {analytics.top_discount_codes && analytics.top_discount_codes.length > 0 ? (
                                                <ResponsiveContainer width="100%" height={280}>
                                                    <BarChart data={analytics.top_discount_codes.slice(0, 5)} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                                        <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                                                        <XAxis dataKey="code" className="text-xs" tick={{ fontSize: 11 }} />
                                                        <YAxis className="text-xs" tick={{ fontSize: 11 }} />
                                                        <Tooltip
                                                            contentStyle={{ backgroundColor: "hsl(var(--background))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "12px" }}
                                                            formatter={(value: number) => [value, "Usage"]}
                                                        />
                                                        <Bar dataKey="usage_count" fill="#8b5cf6" radius={[6, 6, 0, 0]} name="Usage" />
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            ) : (
                                                <div className="flex items-center justify-center h-[280px] text-muted-foreground">No usage data yet</div>
                                            )}
                                        </div>

                                        {/* Revenue by Code Chart */}
                                        <div className="p-5 rounded-xl border bg-slate-50/50 dark:bg-slate-800/30">
                                            <h4 className="font-semibold mb-4 flex items-center gap-2">
                                                <DollarSign className="h-4 w-4 text-emerald-500" />
                                                Revenue Generated by Code
                                            </h4>
                                            {analytics.top_discount_codes && analytics.top_discount_codes.length > 0 ? (
                                                <ResponsiveContainer width="100%" height={280}>
                                                    <BarChart data={analytics.top_discount_codes.slice(0, 5)} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                                                        <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                                                        <XAxis dataKey="code" className="text-xs" tick={{ fontSize: 11 }} />
                                                        <YAxis className="text-xs" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                                                        <Tooltip
                                                            contentStyle={{ backgroundColor: "hsl(var(--background))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: "12px" }}
                                                            formatter={(value: number) => [`$${value.toFixed(2)}`, "Revenue"]}
                                                        />
                                                        <Bar dataKey="revenue_generated" fill="#10b981" radius={[6, 6, 0, 0]} name="Revenue" />
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            ) : (
                                                <div className="flex items-center justify-center h-[280px] text-muted-foreground">No revenue data yet</div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Tables Grid */}
                                    <div className="grid gap-6 lg:grid-cols-2">
                                        {/* Top Codes Table */}
                                        {analytics.top_discount_codes && analytics.top_discount_codes.length > 0 && (
                                            <div className="rounded-xl border overflow-hidden">
                                                <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border-b">
                                                    <h4 className="font-semibold flex items-center gap-2">
                                                        <Trophy className="h-4 w-4 text-amber-500" />
                                                        Top Performing Codes
                                                    </h4>
                                                </div>
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>Code</TableHead>
                                                            <TableHead className="text-center">Usage</TableHead>
                                                            <TableHead className="text-center">Conv.</TableHead>
                                                            <TableHead className="text-right">Revenue</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {analytics.top_discount_codes.slice(0, 5).map((code, idx) => (
                                                            <TableRow key={code.code}>
                                                                <TableCell>
                                                                    <div className="flex items-center gap-2">
                                                                        {idx < 3 && (
                                                                            <Badge className={cn(
                                                                                "w-5 h-5 rounded-full flex items-center justify-center p-0 text-[10px]",
                                                                                idx === 0 && "bg-amber-500",
                                                                                idx === 1 && "bg-slate-400",
                                                                                idx === 2 && "bg-amber-700"
                                                                            )}>{idx + 1}</Badge>
                                                                        )}
                                                                        <code className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono">{code.code}</code>
                                                                    </div>
                                                                </TableCell>
                                                                <TableCell className="text-center">
                                                                    <Badge variant="secondary">{code.usage_count}</Badge>
                                                                </TableCell>
                                                                <TableCell className="text-center">
                                                                    <Badge className="bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20">
                                                                        {(code.conversion_rate * 100).toFixed(1)}%
                                                                    </Badge>
                                                                </TableCell>
                                                                <TableCell className="text-right font-medium text-emerald-600 dark:text-emerald-400">
                                                                    ${code.revenue_generated.toFixed(2)}
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        )}

                                        {/* Top Referrers Table */}
                                        {analytics.top_referrers && analytics.top_referrers.length > 0 && (
                                            <div className="rounded-xl border overflow-hidden">
                                                <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border-b">
                                                    <h4 className="font-semibold flex items-center gap-2">
                                                        <UserPlus className="h-4 w-4 text-pink-500" />
                                                        Top Referrers
                                                    </h4>
                                                </div>
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>User</TableHead>
                                                            <TableHead className="text-center">Referrals</TableHead>
                                                            <TableHead className="text-center">Success</TableHead>
                                                            <TableHead className="text-right">Rewards</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {analytics.top_referrers.slice(0, 5).map((referrer, idx) => (
                                                            <TableRow key={referrer.user_id}>
                                                                <TableCell>
                                                                    <div className="flex items-center gap-2">
                                                                        {idx < 3 && (
                                                                            <Badge className={cn(
                                                                                "w-5 h-5 rounded-full flex items-center justify-center p-0 text-[10px]",
                                                                                idx === 0 && "bg-amber-500",
                                                                                idx === 1 && "bg-slate-400",
                                                                                idx === 2 && "bg-amber-700"
                                                                            )}>{idx + 1}</Badge>
                                                                        )}
                                                                        <div className="min-w-0">
                                                                            <p className="text-sm font-medium truncate">{referrer.user_name || "Unknown"}</p>
                                                                            <p className="text-xs text-muted-foreground truncate">{referrer.user_email}</p>
                                                                        </div>
                                                                    </div>
                                                                </TableCell>
                                                                <TableCell className="text-center">
                                                                    <Badge variant="secondary">{referrer.referral_count}</Badge>
                                                                </TableCell>
                                                                <TableCell className="text-center">
                                                                    <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                                                                        {referrer.successful_referrals}
                                                                    </Badge>
                                                                </TableCell>
                                                                <TableCell className="text-right font-medium text-violet-600 dark:text-violet-400">
                                                                    ${referrer.total_rewards_earned.toFixed(2)}
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        )}
                                    </div>

                                    {/* Period Info */}
                                    <div className="text-xs text-muted-foreground text-center pt-2 border-t pt-4">
                                        Analytics period: {format(new Date(analytics.period_start), "MMM d, yyyy")} - {format(new Date(analytics.period_end), "MMM d, yyyy")}
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
                                    <p className="text-muted-foreground">Unable to load analytics data</p>
                                    <Button variant="outline" className="mt-4" onClick={fetchAnalytics}>Try Again</Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Create/Edit Dialog */}
            <DiscountCodeForm open={isFormOpen} onOpenChange={setIsFormOpen} editingCode={editingCode} onSuccess={handleFormSuccess} />

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteCode} onOpenChange={() => setDeleteCode(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Discount Code</DialogTitle>
                        <DialogDescription>Are you sure you want to delete the discount code &quot;{deleteCode?.code}&quot;? This action cannot be undone.</DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteCode(null)}>Cancel</Button>
                        <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>{isDeleting ? "Deleting..." : "Delete"}</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
