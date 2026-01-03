"use client";

import { useState, useEffect, useMemo } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import strikesApi, {
    Strike,
    StrikeSummary,
    StrikeTimeline,
    AllAccountsSummary,
    RiskLevel,
} from "@/lib/api/strikes";
import {
    AlertTriangle,
    Shield,
    ShieldAlert,
    ShieldCheck,
    ShieldX,
    Clock,
    RefreshCw,
    X,
    Send,
    ChevronRight,
    Calendar,
    Video,
    FileWarning,
    Search,
    LayoutGrid,
    List,
    SlidersHorizontal,
    ChevronLeft,
    ChevronsLeft,
    ChevronsRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ITEMS_PER_PAGE_OPTIONS = [12, 24, 48, 96];

// Helper functions
const getRiskLevelConfig = (level: RiskLevel) => {
    const config = {
        low: { color: "text-green-500", bg: "bg-green-500/10", icon: ShieldCheck, label: "Low Risk" },
        medium: { color: "text-yellow-500", bg: "bg-yellow-500/10", icon: Shield, label: "Medium Risk" },
        high: { color: "text-orange-500", bg: "bg-orange-500/10", icon: ShieldAlert, label: "High Risk" },
        critical: { color: "text-red-500", bg: "bg-red-500/10", icon: ShieldX, label: "Critical" },
    };
    return config[level] || config.low;
};

const getStrikeTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
        copyright: "Copyright",
        community_guidelines: "Community Guidelines",
        trademark: "Trademark",
        other: "Other",
    };
    return labels[type] || type;
};

const getStatusBadge = (status: string) => {
    const config: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
        active: { label: "Active", variant: "destructive" },
        appealed: { label: "Appealed", variant: "secondary" },
        resolved: { label: "Resolved", variant: "outline" },
        expired: { label: "Expired", variant: "outline" },
    };
    const { label, variant } = config[status] || { label: status, variant: "default" };
    return <Badge variant={variant}>{label}</Badge>;
};

export default function StrikesPage() {
    const [data, setData] = useState<AllAccountsSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);

    // View and filter state
    const [view, setView] = useState<"grid" | "list">("grid");
    const [searchQuery, setSearchQuery] = useState("");
    const [riskFilter, setRiskFilter] = useState<string>("all");
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(12);

    // Slide-over panel state
    const [selectedAccount, setSelectedAccount] = useState<StrikeSummary | null>(null);
    const [accountStrikes, setAccountStrikes] = useState<Strike[]>([]);
    const [loadingStrikes, setLoadingStrikes] = useState(false);

    // Strike detail state
    const [selectedStrike, setSelectedStrike] = useState<Strike | null>(null);
    const [strikeTimeline, setStrikeTimeline] = useState<StrikeTimeline | null>(null);
    const [loadingTimeline, setLoadingTimeline] = useState(false);

    // Appeal dialog state
    const [appealOpen, setAppealOpen] = useState(false);
    const [appealReason, setAppealReason] = useState("");
    const [submittingAppeal, setSubmittingAppeal] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, riskFilter, itemsPerPage]);

    useEffect(() => {
        if (selectedAccount) {
            loadAccountStrikes(selectedAccount.account_id);
        }
    }, [selectedAccount]);

    const loadData = async () => {
        try {
            setLoading(true);
            const result = await strikesApi.getAllSummaries();
            setData(result);
        } catch (error) {
            console.error("Failed to load strike data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadAccountStrikes = async (accountId: string) => {
        try {
            setLoadingStrikes(true);
            const result = await strikesApi.getStrikes({
                account_id: accountId,
                include_expired: true,
            });
            setAccountStrikes(result.strikes || []);
        } catch (error) {
            console.error("Failed to load account strikes:", error);
            setAccountStrikes([]);
        } finally {
            setLoadingStrikes(false);
        }
    };

    const handleSyncAll = async () => {
        try {
            setSyncing(true);
            await strikesApi.syncAllAccounts();
            await loadData();
            if (selectedAccount) {
                await loadAccountStrikes(selectedAccount.account_id);
            }
        } catch (error) {
            console.error("Failed to sync strikes:", error);
        } finally {
            setSyncing(false);
        }
    };

    const handleSelectAccount = (summary: StrikeSummary) => {
        setSelectedAccount(summary);
        setSelectedStrike(null);
        setStrikeTimeline(null);
    };

    const handleClosePanel = () => {
        setSelectedAccount(null);
        setAccountStrikes([]);
        setSelectedStrike(null);
        setStrikeTimeline(null);
    };

    const handleViewStrikeDetail = async (strike: Strike) => {
        setSelectedStrike(strike);
        setLoadingTimeline(true);
        try {
            const timeline = await strikesApi.getStrikeTimeline(strike.id);
            setStrikeTimeline(timeline);
        } catch (error) {
            console.error("Failed to load strike timeline:", error);
            setStrikeTimeline(null);
        } finally {
            setLoadingTimeline(false);
        }
    };

    const handleSubmitAppeal = async () => {
        if (!selectedStrike || !appealReason.trim()) return;
        try {
            setSubmittingAppeal(true);
            await strikesApi.submitAppeal(selectedStrike.id, { reason: appealReason });
            setAppealOpen(false);
            setAppealReason("");
            await loadData();
            if (selectedAccount) {
                await loadAccountStrikes(selectedAccount.account_id);
            }
        } catch (error) {
            console.error("Failed to submit appeal:", error);
        } finally {
            setSubmittingAppeal(false);
        }
    };

    const handlePageChange = (page: number) => {
        setCurrentPage(Math.max(1, Math.min(page, totalPages)));
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    // Filter and paginate
    const { filteredSummaries, paginatedSummaries, totalPages } = useMemo(() => {
        if (!data) return { filteredSummaries: [], paginatedSummaries: [], totalPages: 0 };

        let filtered = [...data.summaries];

        // Filter by risk level
        if (riskFilter !== "all") {
            filtered = filtered.filter((s) => s.risk_level === riskFilter);
        }

        // Filter by search query
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter((s) =>
                (s.channel_name || "").toLowerCase().includes(query)
            );
        }

        // Pagination
        const totalPages = Math.ceil(filtered.length / itemsPerPage);
        const startIndex = (currentPage - 1) * itemsPerPage;
        const paginatedSummaries = filtered.slice(startIndex, startIndex + itemsPerPage);

        return { filteredSummaries: filtered, paginatedSummaries, totalPages };
    }, [data, searchQuery, riskFilter, currentPage, itemsPerPage]);

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Strikes" },
            ]}
        >
            <div className="flex h-[calc(100vh-120px)]">
                {/* Main Content */}
                <div className={cn(
                    "flex-1 space-y-6 overflow-auto p-1 transition-all duration-300",
                    selectedAccount ? "pr-4" : ""
                )}>
                    {/* Header */}
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Strike Management</h1>
                            <p className="text-muted-foreground mt-1">
                                Monitor YouTube strikes across all your channels
                            </p>
                        </div>
                        <Button
                            variant="outline"
                            onClick={handleSyncAll}
                            disabled={syncing}
                        >
                            <RefreshCw className={cn("mr-2 h-4 w-4", syncing && "animate-spin")} />
                            {syncing ? "Syncing..." : "Sync All Channels"}
                        </Button>
                    </div>

                    {/* Stats Cards */}
                    {loading ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {[1, 2, 3, 4].map((i) => (
                                <Skeleton key={i} className="h-24" />
                            ))}
                        </div>
                    ) : data && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950 dark:to-red-900 border-red-200 dark:border-red-800">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-red-500/10">
                                            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
                                        </div>
                                        <div>
                                            <p className="text-2xl font-bold text-red-700 dark:text-red-300">{data.total_active_strikes}</p>
                                            <p className="text-xs text-red-600/70 dark:text-red-400/70">Active Strikes</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card className="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-950 dark:to-amber-900 border-amber-200 dark:border-amber-800">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-amber-500/10">
                                            <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                                        </div>
                                        <div>
                                            <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">{data.total_appealed_strikes}</p>
                                            <p className="text-xs text-amber-600/70 dark:text-amber-400/70">Under Appeal</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900 border-orange-200 dark:border-orange-800">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-orange-500/10">
                                            <ShieldAlert className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                                        </div>
                                        <div>
                                            <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">{data.accounts_with_strikes}</p>
                                            <p className="text-xs text-orange-600/70 dark:text-orange-400/70">Affected Channels</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                            <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950 dark:to-emerald-900 border-emerald-200 dark:border-emerald-800">
                                <CardContent className="p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-emerald-500/10">
                                            <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                                        </div>
                                        <div>
                                            <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{data.clean_accounts}</p>
                                            <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70">Clean Channels</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Filters */}
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex flex-col lg:flex-row gap-4">
                                <div className="relative flex-1">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        placeholder="Search by channel name..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-10"
                                    />
                                </div>
                                <div className="flex flex-wrap items-center gap-3">
                                    <Select value={riskFilter} onValueChange={setRiskFilter}>
                                        <SelectTrigger className="w-[160px]">
                                            <SlidersHorizontal className="h-4 w-4 mr-2" />
                                            <SelectValue placeholder="Risk Level" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Risk Levels</SelectItem>
                                            <SelectItem value="low">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-emerald-500" />
                                                    Low Risk
                                                </div>
                                            </SelectItem>
                                            <SelectItem value="medium">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-yellow-500" />
                                                    Medium Risk
                                                </div>
                                            </SelectItem>
                                            <SelectItem value="high">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-orange-500" />
                                                    High Risk
                                                </div>
                                            </SelectItem>
                                            <SelectItem value="critical">
                                                <div className="flex items-center gap-2">
                                                    <div className="h-2 w-2 rounded-full bg-red-500" />
                                                    Critical
                                                </div>
                                            </SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <Select value={itemsPerPage.toString()} onValueChange={(v) => setItemsPerPage(Number(v))}>
                                        <SelectTrigger className="w-[130px]">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {ITEMS_PER_PAGE_OPTIONS.map((option) => (
                                                <SelectItem key={option} value={option.toString()}>
                                                    {option} per page
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <ToggleGroup
                                        type="single"
                                        value={view}
                                        onValueChange={(v) => v && setView(v as "grid" | "list")}
                                        className="bg-muted rounded-lg p-1"
                                    >
                                        <ToggleGroupItem value="grid" aria-label="Grid view" className="px-3">
                                            <LayoutGrid className="h-4 w-4" />
                                        </ToggleGroupItem>
                                        <ToggleGroupItem value="list" aria-label="List view" className="px-3">
                                            <List className="h-4 w-4" />
                                        </ToggleGroupItem>
                                    </ToggleGroup>
                                </div>
                            </div>
                            {(searchQuery || riskFilter !== "all") && (
                                <div className="flex items-center gap-2 mt-3 pt-3 border-t">
                                    <span className="text-sm text-muted-foreground">Filters:</span>
                                    {searchQuery && (
                                        <Badge variant="secondary" className="gap-1">
                                            Search: {searchQuery}
                                            <button onClick={() => setSearchQuery("")} className="ml-1 hover:text-destructive">
                                                <X className="h-3 w-3" />
                                            </button>
                                        </Badge>
                                    )}
                                    {riskFilter !== "all" && (
                                        <Badge variant="secondary" className="gap-1">
                                            Risk: {riskFilter}
                                            <button onClick={() => setRiskFilter("all")} className="ml-1 hover:text-destructive">
                                                <X className="h-3 w-3" />
                                            </button>
                                        </Badge>
                                    )}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => { setSearchQuery(""); setRiskFilter("all"); }}
                                        className="text-xs"
                                    >
                                        Clear all
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Channels Grid/List */}
                    {loading ? (
                        <div className={view === "grid"
                            ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
                            : "space-y-3"
                        }>
                            {Array.from({ length: itemsPerPage > 12 ? 12 : itemsPerPage }).map((_, i) => (
                                <Skeleton key={i} className={view === "grid" ? "h-48 rounded-xl" : "h-20 rounded-xl"} />
                            ))}
                        </div>
                    ) : !data || paginatedSummaries.length === 0 ? (
                        <Card className="border-dashed">
                            <CardContent className="py-16">
                                <div className="text-center">
                                    <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                                        <Shield className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <h3 className="text-xl font-semibold mb-2">
                                        {data?.summaries.length === 0 ? "No channels connected" : "No channels found"}
                                    </h3>
                                    <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                                        {data?.summaries.length === 0
                                            ? "Connect YouTube accounts to monitor their strike status."
                                            : "Try adjusting your search or filters to find what you're looking for."}
                                    </p>
                                    {data?.summaries.length !== 0 && (
                                        <Button variant="outline" onClick={() => { setSearchQuery(""); setRiskFilter("all"); }}>
                                            Clear Filters
                                        </Button>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    ) : (
                        <>
                            {view === "grid" ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                    {paginatedSummaries.map((summary) => {
                                        const riskConfig = getRiskLevelConfig(summary.risk_level);
                                        const RiskIcon = riskConfig.icon;
                                        const isSelected = selectedAccount?.account_id === summary.account_id;

                                        return (
                                            <Card
                                                key={summary.account_id}
                                                className={cn(
                                                    "hover:shadow-lg transition-all cursor-pointer",
                                                    isSelected && "ring-2 ring-primary"
                                                )}
                                                onClick={() => handleSelectAccount(summary)}
                                            >
                                                <CardContent className="p-4">
                                                    <div className="flex items-center gap-3 mb-4">
                                                        <Avatar className="h-12 w-12">
                                                            <AvatarImage
                                                                src={summary.channel_thumbnail}
                                                                alt={summary.channel_name || "Channel"}
                                                            />
                                                            <AvatarFallback>
                                                                {(summary.channel_name || "CH").substring(0, 2).toUpperCase()}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <div className="flex-1 min-w-0">
                                                            <h3 className="font-semibold truncate">
                                                                {summary.channel_name || "Unknown Channel"}
                                                            </h3>
                                                            <div className={cn("flex items-center gap-1 text-sm", riskConfig.color)}>
                                                                <RiskIcon className="h-4 w-4" />
                                                                {riskConfig.label}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Strike Level Bar */}
                                                    <div className="mb-4">
                                                        <div className="flex justify-between text-xs mb-1">
                                                            <span className="text-muted-foreground">Strike Level</span>
                                                            <span className="font-medium">{summary.active_strikes}/3</span>
                                                        </div>
                                                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                            <div
                                                                className={cn(
                                                                    "h-full transition-all",
                                                                    summary.active_strikes === 0 && "bg-green-500",
                                                                    summary.active_strikes === 1 && "bg-yellow-500",
                                                                    summary.active_strikes === 2 && "bg-orange-500",
                                                                    summary.active_strikes >= 3 && "bg-red-500"
                                                                )}
                                                                style={{ width: `${Math.min((summary.active_strikes / 3) * 100, 100)}%` }}
                                                            />
                                                        </div>
                                                    </div>

                                                    {/* Stats */}
                                                    <div className="grid grid-cols-3 gap-2 text-center">
                                                        <div className="p-2 bg-muted/50 rounded-lg">
                                                            <p className={cn(
                                                                "text-lg font-bold",
                                                                summary.active_strikes > 0 ? "text-red-500" : "text-muted-foreground"
                                                            )}>
                                                                {summary.active_strikes}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground">Active</p>
                                                        </div>
                                                        <div className="p-2 bg-muted/50 rounded-lg">
                                                            <p className={cn(
                                                                "text-lg font-bold",
                                                                summary.appealed_strikes > 0 ? "text-yellow-500" : "text-muted-foreground"
                                                            )}>
                                                                {summary.appealed_strikes}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground">Appealed</p>
                                                        </div>
                                                        <div className="p-2 bg-muted/50 rounded-lg">
                                                            <p className="text-lg font-bold text-muted-foreground">
                                                                {summary.resolved_strikes}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground">Resolved</p>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {paginatedSummaries.map((summary) => {
                                        const riskConfig = getRiskLevelConfig(summary.risk_level);
                                        const RiskIcon = riskConfig.icon;
                                        const isSelected = selectedAccount?.account_id === summary.account_id;

                                        return (
                                            <Card
                                                key={summary.account_id}
                                                className={cn(
                                                    "hover:shadow-lg transition-all cursor-pointer",
                                                    isSelected && "ring-2 ring-primary"
                                                )}
                                                onClick={() => handleSelectAccount(summary)}
                                            >
                                                <CardContent className="p-4">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-4">
                                                            <Avatar className="h-12 w-12">
                                                                <AvatarImage
                                                                    src={summary.channel_thumbnail}
                                                                    alt={summary.channel_name || "Channel"}
                                                                />
                                                                <AvatarFallback>
                                                                    {(summary.channel_name || "CH").substring(0, 2).toUpperCase()}
                                                                </AvatarFallback>
                                                            </Avatar>
                                                            <div>
                                                                <h3 className="font-semibold">
                                                                    {summary.channel_name || "Unknown Channel"}
                                                                </h3>
                                                                <div className={cn("flex items-center gap-1 text-sm", riskConfig.color)}>
                                                                    <RiskIcon className="h-4 w-4" />
                                                                    {riskConfig.label}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        <div className="flex items-center gap-6">
                                                            <div className="flex items-center gap-4 text-sm">
                                                                <div className="text-center">
                                                                    <p className={cn(
                                                                        "text-lg font-bold",
                                                                        summary.active_strikes > 0 ? "text-red-500" : "text-muted-foreground"
                                                                    )}>
                                                                        {summary.active_strikes}
                                                                    </p>
                                                                    <p className="text-xs text-muted-foreground">Active</p>
                                                                </div>
                                                                <div className="text-center">
                                                                    <p className={cn(
                                                                        "text-lg font-bold",
                                                                        summary.appealed_strikes > 0 ? "text-yellow-500" : "text-muted-foreground"
                                                                    )}>
                                                                        {summary.appealed_strikes}
                                                                    </p>
                                                                    <p className="text-xs text-muted-foreground">Appealed</p>
                                                                </div>
                                                                <div className="text-center">
                                                                    <p className="text-lg font-bold text-muted-foreground">
                                                                        {summary.resolved_strikes}
                                                                    </p>
                                                                    <p className="text-xs text-muted-foreground">Resolved</p>
                                                                </div>
                                                            </div>

                                                            {/* Strike Level Bar */}
                                                            <div className="w-24">
                                                                <div className="flex justify-between text-xs mb-1">
                                                                    <span className="text-muted-foreground">Level</span>
                                                                    <span className="font-medium">{summary.active_strikes}/3</span>
                                                                </div>
                                                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                                    <div
                                                                        className={cn(
                                                                            "h-full transition-all",
                                                                            summary.active_strikes === 0 && "bg-green-500",
                                                                            summary.active_strikes === 1 && "bg-yellow-500",
                                                                            summary.active_strikes === 2 && "bg-orange-500",
                                                                            summary.active_strikes >= 3 && "bg-red-500"
                                                                        )}
                                                                        style={{ width: `${Math.min((summary.active_strikes / 3) * 100, 100)}%` }}
                                                                    />
                                                                </div>
                                                            </div>

                                                            <ChevronRight className="h-5 w-5 text-muted-foreground" />
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        );
                                    })}
                                </div>
                            )}

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <Card>
                                    <CardContent className="p-4">
                                        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                                            <p className="text-sm text-muted-foreground">
                                                Showing <span className="font-medium">{((currentPage - 1) * itemsPerPage) + 1}</span> to{" "}
                                                <span className="font-medium">{Math.min(currentPage * itemsPerPage, filteredSummaries.length)}</span> of{" "}
                                                <span className="font-medium">{filteredSummaries.length}</span> channels
                                            </p>
                                            <div className="flex items-center gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="icon"
                                                    onClick={() => handlePageChange(1)}
                                                    disabled={currentPage === 1}
                                                >
                                                    <ChevronsLeft className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="icon"
                                                    onClick={() => handlePageChange(currentPage - 1)}
                                                    disabled={currentPage === 1}
                                                >
                                                    <ChevronLeft className="h-4 w-4" />
                                                </Button>

                                                <div className="flex items-center gap-1">
                                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                                        let pageNum: number;
                                                        if (totalPages <= 5) {
                                                            pageNum = i + 1;
                                                        } else if (currentPage <= 3) {
                                                            pageNum = i + 1;
                                                        } else if (currentPage >= totalPages - 2) {
                                                            pageNum = totalPages - 4 + i;
                                                        } else {
                                                            pageNum = currentPage - 2 + i;
                                                        }
                                                        return (
                                                            <Button
                                                                key={pageNum}
                                                                variant={currentPage === pageNum ? "default" : "outline"}
                                                                size="icon"
                                                                onClick={() => handlePageChange(pageNum)}
                                                                className="w-10"
                                                            >
                                                                {pageNum}
                                                            </Button>
                                                        );
                                                    })}
                                                </div>

                                                <Button
                                                    variant="outline"
                                                    size="icon"
                                                    onClick={() => handlePageChange(currentPage + 1)}
                                                    disabled={currentPage === totalPages}
                                                >
                                                    <ChevronRight className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="icon"
                                                    onClick={() => handlePageChange(totalPages)}
                                                    disabled={currentPage === totalPages}
                                                >
                                                    <ChevronsRight className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </>
                    )}
                </div>

                {/* Slide-over Panel */}
                {selectedAccount && (
                    <div className="w-[450px] border-l bg-background flex flex-col animate-in slide-in-from-right duration-300">
                        {/* Panel Header */}
                        <div className="p-4 border-b flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Avatar className="h-10 w-10">
                                    <AvatarImage
                                        src={selectedAccount.channel_thumbnail}
                                        alt={selectedAccount.channel_name || "Channel"}
                                    />
                                    <AvatarFallback>
                                        {(selectedAccount.channel_name || "CH").substring(0, 2).toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <div>
                                    <h3 className="font-semibold">{selectedAccount.channel_name || "Unknown Channel"}</h3>
                                    <p className="text-sm text-muted-foreground">
                                        {selectedAccount.active_strikes} active • {selectedAccount.total_strikes} total
                                    </p>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" onClick={handleClosePanel}>
                                <X className="h-4 w-4" />
                            </Button>
                        </div>

                        {/* Panel Content */}
                        <ScrollArea className="flex-1">
                            <div className="p-4 space-y-4">
                                {loadingStrikes ? (
                                    <div className="space-y-3">
                                        {[1, 2].map((i) => (
                                            <Skeleton key={i} className="h-32" />
                                        ))}
                                    </div>
                                ) : accountStrikes.length === 0 ? (
                                    <div className="text-center py-8">
                                        <ShieldCheck className="mx-auto h-12 w-12 text-green-500 mb-4" />
                                        <h3 className="font-semibold mb-2">No strikes</h3>
                                        <p className="text-sm text-muted-foreground">
                                            This channel is in good standing
                                        </p>
                                    </div>
                                ) : (
                                    accountStrikes.map((strike) => (
                                        <Card
                                            key={strike.id}
                                            className={cn(
                                                "cursor-pointer hover:shadow-md transition-all",
                                                selectedStrike?.id === strike.id && "ring-2 ring-primary"
                                            )}
                                            onClick={() => handleViewStrikeDetail(strike)}
                                        >
                                            <CardContent className="p-4">
                                                <div className="flex items-start justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        <FileWarning className={cn(
                                                            "h-5 w-5",
                                                            strike.status === "active" && "text-red-500",
                                                            strike.status === "appealed" && "text-yellow-500",
                                                            strike.status === "resolved" && "text-green-500",
                                                            strike.status === "expired" && "text-gray-500"
                                                        )} />
                                                        <span className="font-medium">{getStrikeTypeLabel(strike.strike_type)}</span>
                                                    </div>
                                                    {getStatusBadge(strike.status)}
                                                </div>
                                                <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                                                    {strike.reason}
                                                </p>
                                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                    <div className="flex items-center gap-1">
                                                        <Calendar className="h-3 w-3" />
                                                        {new Date(strike.issued_at).toLocaleDateString()}
                                                    </div>
                                                    {strike.affected_video_title && (
                                                        <div className="flex items-center gap-1">
                                                            <Video className="h-3 w-3" />
                                                            <span className="truncate max-w-[150px]">{strike.affected_video_title}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))
                                )}
                            </div>
                        </ScrollArea>

                        {/* Strike Detail Section */}
                        {selectedStrike && (
                            <div className="border-t p-4 space-y-4 bg-muted/30">
                                <div className="flex items-center justify-between">
                                    <h4 className="font-semibold">Strike Details</h4>
                                    {selectedStrike.status === "active" && selectedStrike.appeal_status === "not_appealed" && (
                                        <Button size="sm" onClick={() => setAppealOpen(true)}>
                                            <Send className="mr-2 h-4 w-4" />
                                            Appeal
                                        </Button>
                                    )}
                                </div>

                                <div className="space-y-3 text-sm">
                                    <div>
                                        <p className="text-muted-foreground">Reason</p>
                                        <p className="font-medium">{selectedStrike.reason}</p>
                                    </div>
                                    {selectedStrike.reason_details && (
                                        <div>
                                            <p className="text-muted-foreground">Details</p>
                                            <p>{selectedStrike.reason_details}</p>
                                        </div>
                                    )}
                                    {selectedStrike.affected_video_title && (
                                        <div>
                                            <p className="text-muted-foreground">Affected Video</p>
                                            <p>{selectedStrike.affected_video_title}</p>
                                        </div>
                                    )}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-muted-foreground">Issued</p>
                                            <p>{new Date(selectedStrike.issued_at).toLocaleDateString()}</p>
                                        </div>
                                        {selectedStrike.expires_at && (
                                            <div>
                                                <p className="text-muted-foreground">Expires</p>
                                                <p>{new Date(selectedStrike.expires_at).toLocaleDateString()}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Timeline */}
                                {loadingTimeline ? (
                                    <Skeleton className="h-24" />
                                ) : strikeTimeline && strikeTimeline.events.length > 0 && (
                                    <div className="space-y-2">
                                        <p className="text-sm font-medium">Timeline</p>
                                        <div className="space-y-2">
                                            {strikeTimeline.events.map((event, index) => (
                                                <div key={index} className="flex items-start gap-2 text-sm">
                                                    <div className={cn(
                                                        "mt-1 h-2 w-2 rounded-full",
                                                        event.event_type === "issued" && "bg-red-500",
                                                        event.event_type === "appealed" && "bg-yellow-500",
                                                        event.event_type === "resolved" && "bg-green-500",
                                                        event.event_type === "expired" && "bg-gray-500"
                                                    )} />
                                                    <div className="flex-1">
                                                        <p className="text-muted-foreground">
                                                            {new Date(event.timestamp).toLocaleDateString()}
                                                        </p>
                                                        <p>{event.description}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Appeal Dialog */}
            <Dialog open={appealOpen} onOpenChange={setAppealOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Submit Appeal</DialogTitle>
                        <DialogDescription>
                            Explain why you believe this strike should be removed.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {selectedStrike && (
                            <div className="p-3 bg-muted/50 rounded-lg">
                                <p className="text-sm font-medium">{selectedStrike.reason}</p>
                                <p className="text-xs text-muted-foreground">
                                    {getStrikeTypeLabel(selectedStrike.strike_type)}
                                </p>
                            </div>
                        )}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Appeal Reason</label>
                            <Textarea
                                placeholder="Explain why you believe this strike should be removed..."
                                value={appealReason}
                                onChange={(e) => setAppealReason(e.target.value)}
                                rows={5}
                            />
                            <p className="text-xs text-muted-foreground">
                                Include specific details and any evidence that supports your appeal.
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setAppealOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSubmitAppeal}
                            disabled={!appealReason.trim() || submittingAppeal}
                        >
                            {submittingAppeal ? "Submitting..." : "Submit Appeal"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    );
}
