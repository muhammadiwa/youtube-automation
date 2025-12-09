"use client"

import { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { AccountCard } from "@/components/dashboard/account-card"
import { ConnectAccountModal } from "@/components/dashboard/connect-account-modal"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Skeleton } from "@/components/ui/skeleton"
import { accountsApi } from "@/lib/api"
import { YouTubeAccount } from "@/types"
import { Plus, Search, Grid3x3, List, Youtube } from "lucide-react"

export default function AccountsPage() {
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [filteredAccounts, setFilteredAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [view, setView] = useState<"grid" | "list">("grid")
    const [searchQuery, setSearchQuery] = useState("")
    const [statusFilter, setStatusFilter] = useState<string>("all")
    const [connectModalOpen, setConnectModalOpen] = useState(false)

    useEffect(() => {
        loadAccounts()
    }, [])

    useEffect(() => {
        filterAccounts()
    }, [accounts, searchQuery, statusFilter])

    const loadAccounts = async () => {
        try {
            setLoading(true)
            const data = await accountsApi.getAccounts()
            // Ensure data is always an array
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
            setAccounts([])
        } finally {
            setLoading(false)
        }
    }

    const filterAccounts = () => {
        // Ensure accounts is an array before filtering
        if (!Array.isArray(accounts)) {
            setFilteredAccounts([])
            return
        }

        let filtered = [...accounts]

        // Filter by status
        if (statusFilter !== "all") {
            filtered = filtered.filter((account) => account.status === statusFilter)
        }

        // Filter by search query
        if (searchQuery) {
            filtered = filtered.filter((account) =>
                account.channelTitle.toLowerCase().includes(searchQuery.toLowerCase())
            )
        }

        setFilteredAccounts(filtered)
    }

    const handleConnectAccount = () => {
        setConnectModalOpen(true)
    }

    // Ensure filteredAccounts is always an array for rendering
    const safeFilteredAccounts = Array.isArray(filteredAccounts) ? filteredAccounts : []
    const safeAccounts = Array.isArray(accounts) ? accounts : []

    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Accounts" }]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">YouTube Accounts</h1>
                        <p className="text-muted-foreground">
                            Manage your connected YouTube accounts
                        </p>
                    </div>
                    <Button
                        onClick={handleConnectAccount}
                        size="lg"
                        className="w-full sm:w-auto"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        Connect Account
                    </Button>
                </div>

                {/* Filters and View Toggle */}
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search accounts..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-full sm:w-[180px]">
                            <SelectValue placeholder="Filter by status" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Status</SelectItem>
                            <SelectItem value="active">Active</SelectItem>
                            <SelectItem value="expired">Token Expired</SelectItem>
                            <SelectItem value="error">Error</SelectItem>
                        </SelectContent>
                    </Select>
                    <ToggleGroup type="single" value={view} onValueChange={(v) => v && setView(v as "grid" | "list")}>
                        <ToggleGroupItem value="grid" aria-label="Grid view">
                            <Grid3x3 className="h-4 w-4" />
                        </ToggleGroupItem>
                        <ToggleGroupItem value="list" aria-label="List view">
                            <List className="h-4 w-4" />
                        </ToggleGroupItem>
                    </ToggleGroup>
                </div>

                {/* Accounts List */}
                {loading ? (
                    <div className={view === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
                        {[1, 2, 3].map((i) => (
                            <Skeleton key={i} className={view === "grid" ? "h-64" : "h-24"} />
                        ))}
                    </div>
                ) : safeFilteredAccounts.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed rounded-lg">
                        <Youtube className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">
                            {safeAccounts.length === 0 ? "No accounts connected" : "No accounts found"}
                        </h3>
                        <p className="text-muted-foreground mb-4">
                            {safeAccounts.length === 0
                                ? "Connect your first YouTube account to get started"
                                : "Try adjusting your search or filters"}
                        </p>
                        {safeAccounts.length === 0 && (
                            <Button onClick={handleConnectAccount}>
                                <Plus className="mr-2 h-4 w-4" />
                                Connect Account
                            </Button>
                        )}
                    </div>
                ) : (
                    <div className={view === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
                        {safeFilteredAccounts.map((account) => (
                            <AccountCard key={account.id} account={account} view={view} />
                        ))}
                    </div>
                )}

                {/* Results count */}
                {!loading && safeFilteredAccounts.length > 0 && (
                    <div className="text-sm text-muted-foreground text-center">
                        Showing {safeFilteredAccounts.length} of {safeAccounts.length} account{safeAccounts.length !== 1 ? "s" : ""}
                    </div>
                )}

                {/* Connect Account Modal */}
                <ConnectAccountModal open={connectModalOpen} onOpenChange={setConnectModalOpen} />
            </div>
        </DashboardLayout>
    )
}
