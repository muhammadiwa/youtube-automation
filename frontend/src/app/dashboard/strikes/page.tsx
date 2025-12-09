"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import strikesApi, {
    Strike,
    StrikeSummary,
    StrikeHistory,
    StrikeStatus,
    StrikeType,
} from "@/lib/api/strikes";
import {
    AlertTriangle,
    Shield,
    ShieldAlert,
    ShieldCheck,
    ShieldX,
    Clock,
    FileText,
    RefreshCw,
    ChevronRight,
    AlertCircle,
    CheckCircle2,
    XCircle,
    History,
    Send,
} from "lucide-react";
import { cn } from "@/lib/utils";


// Helper functions
const getStrikeTypeLabel = (type: StrikeType): string => {
    const labels: Record<StrikeType, string> = {
        copyright: "Copyright",
        community_guidelines: "Community Guidelines",
        trademark: "Trademark",
        other: "Other",
    };
    return labels[type] || type;
};

const getStrikeStatusBadge = (status: StrikeStatus) => {
    const config: Record<StrikeStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
        active: { label: "Active", variant: "destructive" },
        appealed: { label: "Appealed", variant: "secondary" },
        resolved: { label: "Resolved", variant: "outline" },
        expired: { label: "Expired", variant: "outline" },
    };
    const { label, variant } = config[status] || { label: status, variant: "default" };
    return <Badge variant={variant}>{label}</Badge>;
};

const getRiskLevelConfig = (level: StrikeSummary["risk_level"]) => {
    const config = {
        low: { color: "text-green-500", bg: "bg-green-500/10", icon: ShieldCheck, label: "Low Risk" },
        medium: { color: "text-yellow-500", bg: "bg-yellow-500/10", icon: Shield, label: "Medium Risk" },
        high: { color: "text-orange-500", bg: "bg-orange-500/10", icon: ShieldAlert, label: "High Risk" },
        critical: { color: "text-red-500", bg: "bg-red-500/10", icon: ShieldX, label: "Critical" },
    };
    return config[level] || config.low;
};

export default function StrikesPage() {
    const [summaries, setSummaries] = useState<StrikeSummary[]>([]);
    const [strikes, setStrikes] = useState<Strike[]>([]);
    const [selectedStrike, setSelectedStrike] = useState<Strike | null>(null);
    const [strikeHistory, setStrikeHistory] = useState<StrikeHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [typeFilter, setTypeFilter] = useState<string>("all");
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [appealOpen, setAppealOpen] = useState(false);
    const [appealReason, setAppealReason] = useState("");
    const [submittingAppeal, setSubmittingAppeal] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        loadStrikes();
    }, [statusFilter, typeFilter]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [summariesData, strikesData] = await Promise.all([
                strikesApi.getStrikeSummaries(),
                strikesApi.getStrikes(),
            ]);
            setSummaries(summariesData.items || []);
            setStrikes(strikesData.items || []);
        } catch (error) {
            console.error("Failed to load strike data:", error);
        } finally {
            setLoading(false);
        }
    };

    const loadStrikes = async () => {
        try {
            const params: { status?: StrikeStatus; type?: StrikeType } = {};
            if (statusFilter !== "all") params.status = statusFilter as StrikeStatus;
            if (typeFilter !== "all") params.type = typeFilter as StrikeType;
            const data = await strikesApi.getStrikes(params);
            setStrikes(data.items || []);
        } catch (error) {
            console.error("Failed to load strikes:", error);
        }
    };

    const handleSync = async () => {
        try {
            setSyncing(true);
            await strikesApi.syncStrikes();
            await loadData();
        } catch (error) {
            console.error("Failed to sync strikes:", error);
        } finally {
            setSyncing(false);
        }
    };

    const handleViewDetails = async (strike: Strike) => {
        setSelectedStrike(strike);
        setDetailsOpen(true);
        setLoadingHistory(true);
        try {
            const history = await strikesApi.getStrikeHistory(strike.id);
            setStrikeHistory(history);
        } catch (error) {
            console.error("Failed to load strike history:", error);
            setStrikeHistory([]);
        } finally {
            setLoadingHistory(false);
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
        } catch (error) {
            console.error("Failed to submit appeal:", error);
        } finally {
            setSubmittingAppeal(false);
        }
    };

    const totalActiveStrikes = summaries.reduce((sum, s) => sum + s.active_strikes, 0);
    const totalAppealedStrikes = summaries.reduce((sum, s) => sum + s.appealed_strikes, 0);
    const accountsWithStrikes = summaries.filter((s) => s.total_strikes > 0).length;

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Strikes" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Strike Management</h1>
                        <p className="text-muted-foreground">
                            Monitor and manage YouTube strikes across your accounts
                        </p>
                    </div>
                    <Button
                        variant="outline"
                        onClick={handleSync}
                        disabled={syncing}
                    >
                        <RefreshCw className={cn("mr-2 h-4 w-4", syncing && "animate-spin")} />
                        {syncing ? "Syncing..." : "Sync Strikes"}
                    </Button>
                </div>


                {/* Overview Cards */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map((i) => (
                            <Skeleton key={i} className="h-24" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card className="border-0 bg-card shadow-lg">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-red-500/10">
                                        <AlertTriangle className="h-5 w-5 text-red-500" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{totalActiveStrikes}</p>
                                        <p className="text-sm text-muted-foreground">Active Strikes</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-0 bg-card shadow-lg">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-yellow-500/10">
                                        <Clock className="h-5 w-5 text-yellow-500" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{totalAppealedStrikes}</p>
                                        <p className="text-sm text-muted-foreground">Under Appeal</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-0 bg-card shadow-lg">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-blue-500/10">
                                        <Shield className="h-5 w-5 text-blue-500" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">{accountsWithStrikes}</p>
                                        <p className="text-sm text-muted-foreground">Affected Accounts</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-0 bg-card shadow-lg">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-green-500/10">
                                        <ShieldCheck className="h-5 w-5 text-green-500" />
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold">
                                            {summaries.length - accountsWithStrikes}
                                        </p>
                                        <p className="text-sm text-muted-foreground">Clean Accounts</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Main Content */}
                <Tabs defaultValue="overview" className="space-y-4">
                    <TabsList>
                        <TabsTrigger value="overview">Account Overview</TabsTrigger>
                        <TabsTrigger value="strikes">All Strikes</TabsTrigger>
                        <TabsTrigger value="timeline">Timeline</TabsTrigger>
                    </TabsList>

                    {/* Account Overview Tab */}
                    <TabsContent value="overview" className="space-y-4">
                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {[1, 2, 3].map((i) => (
                                    <Skeleton key={i} className="h-48" />
                                ))}
                            </div>
                        ) : summaries.length === 0 ? (
                            <div className="text-center py-12 border-2 border-dashed rounded-lg">
                                <Shield className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No accounts found</h3>
                                <p className="text-muted-foreground">
                                    Connect YouTube accounts to monitor their strike status
                                </p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {summaries.map((summary) => {
                                    const riskConfig = getRiskLevelConfig(summary.risk_level);
                                    const RiskIcon = riskConfig.icon;
                                    return (
                                        <Card
                                            key={summary.account_id}
                                            className="border-0 bg-card shadow-lg hover:shadow-xl transition-all"
                                        >
                                            <CardContent className="p-6">
                                                <div className="flex items-start justify-between mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <Avatar className="h-10 w-10">
                                                            <AvatarImage
                                                                src={summary.channel_thumbnail}
                                                                alt={summary.channel_name}
                                                            />
                                                            <AvatarFallback>
                                                                {summary.channel_name.substring(0, 2).toUpperCase()}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <div>
                                                            <h3 className="font-semibold line-clamp-1">
                                                                {summary.channel_name}
                                                            </h3>
                                                            <div className={cn("flex items-center gap-1 text-xs", riskConfig.color)}>
                                                                <RiskIcon className="h-3 w-3" />
                                                                {riskConfig.label}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    {summary.has_paused_streams && (
                                                        <Badge variant="destructive" className="text-xs">
                                                            Streams Paused
                                                        </Badge>
                                                    )}
                                                </div>

                                                {/* Strike Counts */}
                                                <div className="grid grid-cols-3 gap-2 mb-4">
                                                    <div className="text-center p-2 bg-muted/50 rounded-lg">
                                                        <p className="text-lg font-bold text-red-500">
                                                            {summary.active_strikes}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">Active</p>
                                                    </div>
                                                    <div className="text-center p-2 bg-muted/50 rounded-lg">
                                                        <p className="text-lg font-bold text-yellow-500">
                                                            {summary.appealed_strikes}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">Appealed</p>
                                                    </div>
                                                    <div className="text-center p-2 bg-muted/50 rounded-lg">
                                                        <p className="text-lg font-bold text-green-500">
                                                            {summary.resolved_strikes}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">Resolved</p>
                                                    </div>
                                                </div>

                                                {/* Strike Progress Bar */}
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-xs">
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
                                                    {summary.active_strikes >= 3 && (
                                                        <p className="text-xs text-red-500 font-medium">
                                                            ⚠️ Channel at risk of termination
                                                        </p>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    );
                                })}
                            </div>
                        )}
                    </TabsContent>


                    {/* All Strikes Tab */}
                    <TabsContent value="strikes" className="space-y-4">
                        {/* Filters */}
                        <div className="flex flex-wrap gap-4">
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Filter by status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Statuses</SelectItem>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="appealed">Appealed</SelectItem>
                                    <SelectItem value="resolved">Resolved</SelectItem>
                                    <SelectItem value="expired">Expired</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={typeFilter} onValueChange={setTypeFilter}>
                                <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Filter by type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Types</SelectItem>
                                    <SelectItem value="copyright">Copyright</SelectItem>
                                    <SelectItem value="community_guidelines">Community Guidelines</SelectItem>
                                    <SelectItem value="trademark">Trademark</SelectItem>
                                    <SelectItem value="other">Other</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Strikes List */}
                        {loading ? (
                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <Skeleton key={i} className="h-32" />
                                ))}
                            </div>
                        ) : strikes.length === 0 ? (
                            <div className="text-center py-12 border-2 border-dashed rounded-lg">
                                <ShieldCheck className="mx-auto h-12 w-12 text-green-500 mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No strikes found</h3>
                                <p className="text-muted-foreground">
                                    {statusFilter !== "all" || typeFilter !== "all"
                                        ? "Try adjusting your filters"
                                        : "Your accounts are in good standing"}
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {strikes.map((strike) => (
                                    <Card
                                        key={strike.id}
                                        className="border-0 bg-card shadow-lg hover:shadow-xl transition-all cursor-pointer"
                                        onClick={() => handleViewDetails(strike)}
                                    >
                                        <CardContent className="p-6">
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-4">
                                                    <div className={cn(
                                                        "p-3 rounded-lg",
                                                        strike.status === "active" && "bg-red-500/10",
                                                        strike.status === "appealed" && "bg-yellow-500/10",
                                                        strike.status === "resolved" && "bg-green-500/10",
                                                        strike.status === "expired" && "bg-gray-500/10"
                                                    )}>
                                                        <AlertTriangle className={cn(
                                                            "h-6 w-6",
                                                            strike.status === "active" && "text-red-500",
                                                            strike.status === "appealed" && "text-yellow-500",
                                                            strike.status === "resolved" && "text-green-500",
                                                            strike.status === "expired" && "text-gray-500"
                                                        )} />
                                                    </div>
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            <h3 className="font-semibold">{strike.reason}</h3>
                                                            {getStrikeStatusBadge(strike.status)}
                                                        </div>
                                                        <p className="text-sm text-muted-foreground">
                                                            {strike.channel_name} • {getStrikeTypeLabel(strike.type)}
                                                        </p>
                                                        {strike.video_title && (
                                                            <p className="text-sm text-muted-foreground">
                                                                Video: {strike.video_title}
                                                            </p>
                                                        )}
                                                        <p className="text-xs text-muted-foreground">
                                                            Issued: {new Date(strike.issued_at).toLocaleDateString()}
                                                            {strike.expires_at && (
                                                                <> • Expires: {new Date(strike.expires_at).toLocaleDateString()}</>
                                                            )}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {strike.status === "active" && strike.appeal_status === "not_appealed" && (
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setSelectedStrike(strike);
                                                                setAppealOpen(true);
                                                            }}
                                                        >
                                                            <FileText className="mr-2 h-4 w-4" />
                                                            Appeal
                                                        </Button>
                                                    )}
                                                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </TabsContent>

                    {/* Timeline Tab */}
                    <TabsContent value="timeline" className="space-y-4">
                        {loading ? (
                            <Skeleton className="h-96" />
                        ) : strikes.length === 0 ? (
                            <div className="text-center py-12 border-2 border-dashed rounded-lg">
                                <History className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No strike history</h3>
                                <p className="text-muted-foreground">
                                    Strike events will appear here as they occur
                                </p>
                            </div>
                        ) : (
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader>
                                    <CardTitle>Strike Timeline</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="relative">
                                        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
                                        <div className="space-y-6">
                                            {strikes
                                                .sort((a, b) => new Date(b.issued_at).getTime() - new Date(a.issued_at).getTime())
                                                .map((strike) => (
                                                    <div key={strike.id} className="relative pl-10">
                                                        <div className={cn(
                                                            "absolute left-2 w-5 h-5 rounded-full border-2 bg-background flex items-center justify-center",
                                                            strike.status === "active" && "border-red-500",
                                                            strike.status === "appealed" && "border-yellow-500",
                                                            strike.status === "resolved" && "border-green-500",
                                                            strike.status === "expired" && "border-gray-500"
                                                        )}>
                                                            {strike.status === "active" && <AlertCircle className="h-3 w-3 text-red-500" />}
                                                            {strike.status === "appealed" && <Clock className="h-3 w-3 text-yellow-500" />}
                                                            {strike.status === "resolved" && <CheckCircle2 className="h-3 w-3 text-green-500" />}
                                                            {strike.status === "expired" && <XCircle className="h-3 w-3 text-gray-500" />}
                                                        </div>
                                                        <div className="bg-muted/50 rounded-lg p-4">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-medium">{strike.reason}</span>
                                                                    {getStrikeStatusBadge(strike.status)}
                                                                </div>
                                                                <span className="text-xs text-muted-foreground">
                                                                    {new Date(strike.issued_at).toLocaleDateString()}
                                                                </span>
                                                            </div>
                                                            <p className="text-sm text-muted-foreground">
                                                                {strike.channel_name} • {getStrikeTypeLabel(strike.type)}
                                                            </p>
                                                            {strike.description && (
                                                                <p className="text-sm mt-2">{strike.description}</p>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </TabsContent>
                </Tabs>
            </div>


            {/* Strike Details Dialog */}
            <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>Strike Details</DialogTitle>
                        <DialogDescription>
                            View detailed information about this strike
                        </DialogDescription>
                    </DialogHeader>
                    {selectedStrike && (
                        <div className="space-y-6">
                            {/* Strike Info */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline">{getStrikeTypeLabel(selectedStrike.type)}</Badge>
                                        {getStrikeStatusBadge(selectedStrike.status)}
                                    </div>
                                    {selectedStrike.appeal_status !== "not_appealed" && (
                                        <Badge variant="secondary">
                                            Appeal: {selectedStrike.appeal_status.replace("_", " ")}
                                        </Badge>
                                    )}
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Channel</p>
                                        <p className="font-medium">{selectedStrike.channel_name}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Issued Date</p>
                                        <p className="font-medium">
                                            {new Date(selectedStrike.issued_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    {selectedStrike.video_title && (
                                        <div className="col-span-2">
                                            <p className="text-sm text-muted-foreground">Affected Video</p>
                                            <p className="font-medium">{selectedStrike.video_title}</p>
                                        </div>
                                    )}
                                    {selectedStrike.expires_at && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">Expires</p>
                                            <p className="font-medium">
                                                {new Date(selectedStrike.expires_at).toLocaleDateString()}
                                            </p>
                                        </div>
                                    )}
                                    {selectedStrike.appeal_deadline && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">Appeal Deadline</p>
                                            <p className="font-medium text-orange-500">
                                                {new Date(selectedStrike.appeal_deadline).toLocaleDateString()}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div>
                                    <p className="text-sm text-muted-foreground mb-1">Reason</p>
                                    <p className="font-medium">{selectedStrike.reason}</p>
                                </div>

                                {selectedStrike.description && (
                                    <div>
                                        <p className="text-sm text-muted-foreground mb-1">Description</p>
                                        <p className="text-sm">{selectedStrike.description}</p>
                                    </div>
                                )}
                            </div>

                            {/* Strike History */}
                            <div>
                                <h4 className="font-semibold mb-3 flex items-center gap-2">
                                    <History className="h-4 w-4" />
                                    History
                                </h4>
                                {loadingHistory ? (
                                    <div className="space-y-2">
                                        {[1, 2].map((i) => (
                                            <Skeleton key={i} className="h-12" />
                                        ))}
                                    </div>
                                ) : strikeHistory.length === 0 ? (
                                    <p className="text-sm text-muted-foreground">No history available</p>
                                ) : (
                                    <div className="space-y-2">
                                        {strikeHistory.map((event) => (
                                            <div
                                                key={event.id}
                                                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                                            >
                                                <div className="flex items-center gap-3">
                                                    {event.action === "issued" && <AlertCircle className="h-4 w-4 text-red-500" />}
                                                    {event.action === "appealed" && <FileText className="h-4 w-4 text-yellow-500" />}
                                                    {event.action === "appeal_reviewed" && <Clock className="h-4 w-4 text-blue-500" />}
                                                    {event.action === "resolved" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                                    {event.action === "expired" && <XCircle className="h-4 w-4 text-gray-500" />}
                                                    <span className="text-sm">{event.description}</span>
                                                </div>
                                                <span className="text-xs text-muted-foreground">
                                                    {new Date(event.timestamp).toLocaleString()}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    <DialogFooter>
                        {selectedStrike?.status === "active" && selectedStrike?.appeal_status === "not_appealed" && (
                            <Button
                                onClick={() => {
                                    setDetailsOpen(false);
                                    setAppealOpen(true);
                                }}
                            >
                                <FileText className="mr-2 h-4 w-4" />
                                Submit Appeal
                            </Button>
                        )}
                        <Button variant="outline" onClick={() => setDetailsOpen(false)}>
                            Close
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Appeal Dialog */}
            <Dialog open={appealOpen} onOpenChange={setAppealOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Submit Appeal</DialogTitle>
                        <DialogDescription>
                            Provide a reason for appealing this strike. Be specific and include any relevant evidence.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {selectedStrike && (
                            <div className="p-3 bg-muted/50 rounded-lg">
                                <p className="text-sm font-medium">{selectedStrike.reason}</p>
                                <p className="text-xs text-muted-foreground">
                                    {selectedStrike.channel_name} • {getStrikeTypeLabel(selectedStrike.type)}
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
                        <Button
                            variant="outline"
                            onClick={() => {
                                setAppealOpen(false);
                                setAppealReason("");
                            }}
                            disabled={submittingAppeal}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSubmitAppeal}
                            disabled={submittingAppeal || !appealReason.trim()}
                        >
                            {submittingAppeal ? (
                                <>
                                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                                    Submitting...
                                </>
                            ) : (
                                <>
                                    <Send className="mr-2 h-4 w-4" />
                                    Submit Appeal
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    );
}
