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
import type { DiscountCode, DiscountCodeListResponse } from "@/types/admin"
import { DiscountCodeForm } from "@/components/admin/promotions/discount-code-form"


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
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Filters
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [page, setPage] = useState(1)
    const pageSize = 10

    // Dialogs
    const [isFormOpen, setIsFormOpen] = useState(false)
    const [editingCode, setEditingCode] = useState<DiscountCode | null>(null)
    const [deleteCode, setDeleteCode] = useState<DiscountCode | null>(null)
    const [isDeleting, setIsDeleting] = useState(false)

    // Copy state
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

    useEffect(() => {
        fetchDiscountCodes()
    }, [fetchDiscountCodes])

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

    // Calculate stats
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
                    <StatsCard
                        title="Total Codes"
                        value={totalCodes}
                        icon={Gift}
                        gradient="from-violet-500 to-violet-600"
                        delay={0}
                    />
                    <StatsCard
                        title="Active Codes"
                        value={activeCodes}
                        icon={CheckCircle}
                        gradient="from-emerald-500 to-emerald-600"
                        delay={0.05}
                    />
                    <StatsCard
                        title="Total Usage"
                        value={totalUsage}
                        icon={Users}
                        gradient="from-blue-500 to-blue-600"
                        delay={0.1}
                    />
                </div>


                {/* Filters */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardContent className="p-4">
                            <div className="flex flex-col sm:flex-row gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by code..."
                                        value={search}
                                        onChange={(e) => handleSearch(e.target.value)}
                                        className="pl-9"
                                    />
                                </div>
                                <Select value={statusFilter} onValueChange={handleStatusFilter}>
                                    <SelectTrigger className="w-[150px]">
                                        <SelectValue placeholder="Status" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Status</SelectItem>
                                        <SelectItem value="active">Active</SelectItem>
                                        <SelectItem value="inactive">Inactive</SelectItem>
                                    </SelectContent>
                                </Select>
                                <Button variant="outline" size="icon" onClick={fetchDiscountCodes}>
                                    <RefreshCcw className="h-4 w-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Discount Codes Table */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="border border-slate-200/60 dark:border-slate-700/60 shadow-sm bg-white dark:bg-slate-900">
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Gift className="h-5 w-5" />
                                Discount Codes
                            </CardTitle>
                            <CardDescription>
                                Manage discount codes with percentage or fixed discounts
                            </CardDescription>
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
                                    <Button variant="outline" onClick={fetchDiscountCodes}>
                                        Try Again
                                    </Button>
                                </div>
                            ) : discountCodes?.items.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-center">
                                    <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                                        <Gift className="h-6 w-6 text-muted-foreground" />
                                    </div>
                                    <p className="text-muted-foreground mb-4">No discount codes found</p>
                                    <Button onClick={handleCreateNew} className="gap-2">
                                        <Plus className="h-4 w-4" />
                                        Create First Code
                                    </Button>
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
                                                                <code className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-sm font-mono">
                                                                    {code.code}
                                                                </code>
                                                                <Button
                                                                    variant="ghost"
                                                                    size="icon"
                                                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                                    onClick={() => handleCopyCode(code.code)}
                                                                >
                                                                    {copiedCode === code.code ? (
                                                                        <Check className="h-3 w-3 text-green-500" />
                                                                    ) : (
                                                                        <Copy className="h-3 w-3" />
                                                                    )}
                                                                </Button>
                                                            </div>

                                                        </TableCell>
                                                        <TableCell>
                                                            <div className="flex items-center gap-2">
                                                                {code.discount_type === "percentage" ? (
                                                                    <>
                                                                        <Percent className="h-4 w-4 text-violet-500" />
                                                                        <span className="font-medium">{code.discount_value}%</span>
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <DollarSign className="h-4 w-4 text-emerald-500" />
                                                                        <span className="font-medium">${code.discount_value}</span>
                                                                    </>
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
                                                                {code.usage_limit && (
                                                                    <span className="text-muted-foreground">/ {code.usage_limit}</span>
                                                                )}
                                                            </div>
                                                        </TableCell>
                                                        <TableCell>
                                                            {code.is_active && code.is_valid ? (
                                                                <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                                    Active
                                                                </Badge>
                                                            ) : !code.is_active ? (
                                                                <Badge variant="secondary" className="bg-slate-100 dark:bg-slate-800">
                                                                    <XCircle className="h-3 w-3 mr-1" />
                                                                    Disabled
                                                                </Badge>
                                                            ) : (
                                                                <Badge variant="secondary" className="bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20">
                                                                    <AlertCircle className="h-3 w-3 mr-1" />
                                                                    Expired
                                                                </Badge>
                                                            )}
                                                        </TableCell>
                                                        <TableCell>
                                                            <DropdownMenu>
                                                                <DropdownMenuTrigger asChild>
                                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                                        <MoreHorizontal className="h-4 w-4" />
                                                                    </Button>
                                                                </DropdownMenuTrigger>
                                                                <DropdownMenuContent align="end">
                                                                    <DropdownMenuItem onClick={() => handleEdit(code)}>
                                                                        <Pencil className="h-4 w-4 mr-2" />
                                                                        Edit
                                                                    </DropdownMenuItem>
                                                                    <DropdownMenuSeparator />
                                                                    <DropdownMenuItem
                                                                        onClick={() => setDeleteCode(code)}
                                                                        className="text-red-600 dark:text-red-400"
                                                                    >
                                                                        <Trash2 className="h-4 w-4 mr-2" />
                                                                        Delete
                                                                    </DropdownMenuItem>
                                                                </DropdownMenuContent>
                                                            </DropdownMenu>
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </div>

                                    {/* Pagination */}
                                    {discountCodes && discountCodes.total_pages > 1 && (
                                        <div className="flex items-center justify-between mt-4">
                                            <p className="text-sm text-muted-foreground">
                                                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, discountCodes.total)} of {discountCodes.total} codes
                                            </p>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                                    disabled={page === 1}
                                                >
                                                    Previous
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => setPage(p => Math.min(discountCodes.total_pages, p + 1))}
                                                    disabled={page === discountCodes.total_pages}
                                                >
                                                    Next
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* Create/Edit Dialog */}
            <DiscountCodeForm
                open={isFormOpen}
                onOpenChange={setIsFormOpen}
                editingCode={editingCode}
                onSuccess={handleFormSuccess}
            />

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteCode} onOpenChange={() => setDeleteCode(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Discount Code</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete the discount code &quot;{deleteCode?.code}&quot;? This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteCode(null)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
                            {isDeleting ? "Deleting..." : "Delete"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </AdminLayout>
    )
}
