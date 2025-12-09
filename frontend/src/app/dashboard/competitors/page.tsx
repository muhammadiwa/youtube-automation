"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import competitorsApi, { Competitor } from "@/lib/api/competitors";
import {
    Plus,
    Search,
    Target,
    Users,
    Video,
    Eye,
    Trash2,
    ExternalLink,
    RefreshCw,
    TrendingUp,
    Bell,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function CompetitorsPage() {
    const [competitors, setCompetitors] = useState<Competitor[]>([]);
    const [filteredCompetitors, setFilteredCompetitors] = useState<Competitor[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [addModalOpen, setAddModalOpen] = useState(false);
    const [channelUrl, setChannelUrl] = useState("");
    const [adding, setAdding] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [competitorToDelete, setCompetitorToDelete] = useState<Competitor | null>(null);
    const [deleting, setDeleting] = useState(false);
    const [syncingId, setSyncingId] = useState<string | null>(null);

    useEffect(() => {
        loadCompetitors();
    }, []);

    useEffect(() => {
        filterCompetitors();
    }, [competitors, searchQuery]);


    const loadCompetitors = async () => {
        try {
            setLoading(true);
            const data = await competitorsApi.getCompetitors();
            setCompetitors(data.items || []);
        } catch (error) {
            console.error("Failed to load competitors:", error);
            setCompetitors([]);
        } finally {
            setLoading(false);
        }
    };

    const filterCompetitors = () => {
        if (!Array.isArray(competitors)) {
            setFilteredCompetitors([]);
            return;
        }

        let filtered = [...competitors];

        if (searchQuery) {
            filtered = filtered.filter((c) =>
                c.channel_name.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        setFilteredCompetitors(filtered);
    };

    const handleAddCompetitor = async () => {
        if (!channelUrl.trim()) return;

        try {
            setAdding(true);
            await competitorsApi.addCompetitor(channelUrl);
            setChannelUrl("");
            setAddModalOpen(false);
            await loadCompetitors();
        } catch (error) {
            console.error("Failed to add competitor:", error);
        } finally {
            setAdding(false);
        }
    };

    const handleDeleteCompetitor = async () => {
        if (!competitorToDelete) return;

        try {
            setDeleting(true);
            await competitorsApi.removeCompetitor(competitorToDelete.id);
            setDeleteDialogOpen(false);
            setCompetitorToDelete(null);
            await loadCompetitors();
        } catch (error) {
            console.error("Failed to delete competitor:", error);
        } finally {
            setDeleting(false);
        }
    };

    const handleSyncCompetitor = async (competitor: Competitor) => {
        try {
            setSyncingId(competitor.id);
            await competitorsApi.syncCompetitor(competitor.id);
            await loadCompetitors();
        } catch (error) {
            console.error("Failed to sync competitor:", error);
        } finally {
            setSyncingId(null);
        }
    };

    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    const safeCompetitors = Array.isArray(competitors) ? competitors : [];
    const safeFilteredCompetitors = Array.isArray(filteredCompetitors) ? filteredCompetitors : [];

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Competitors" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Competitor Analysis</h1>
                        <p className="text-muted-foreground">
                            Track and analyze competitor channels
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link href="/dashboard/competitors/alerts">
                            <Button variant="outline">
                                <Bell className="mr-2 h-4 w-4" />
                                Alerts
                            </Button>
                        </Link>
                        <Button
                            onClick={() => setAddModalOpen(true)}
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                        >
                            <Plus className="mr-2 h-4 w-4" />
                            Add Competitor
                        </Button>
                    </div>
                </div>

                {/* Search */}
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search competitors..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>


                {/* Competitors Grid */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map((i) => (
                            <Skeleton key={i} className="h-64" />
                        ))}
                    </div>
                ) : safeFilteredCompetitors.length === 0 ? (
                    <div className="text-center py-12 border-2 border-dashed rounded-lg">
                        <Target className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">
                            {safeCompetitors.length === 0
                                ? "No competitors tracked"
                                : "No competitors found"}
                        </h3>
                        <p className="text-muted-foreground mb-4">
                            {safeCompetitors.length === 0
                                ? "Add competitor channels to start tracking their performance"
                                : "Try adjusting your search"}
                        </p>
                        {safeCompetitors.length === 0 && (
                            <Button
                                onClick={() => setAddModalOpen(true)}
                                className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                            >
                                <Plus className="mr-2 h-4 w-4" />
                                Add Competitor
                            </Button>
                        )}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {safeFilteredCompetitors.map((competitor) => (
                            <Card
                                key={competitor.id}
                                className="border-0 bg-card shadow-lg hover:shadow-xl transition-all group"
                            >
                                <CardContent className="p-6">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <Avatar className="h-12 w-12">
                                                <AvatarImage
                                                    src={competitor.thumbnail_url}
                                                    alt={competitor.channel_name}
                                                />
                                                <AvatarFallback>
                                                    {competitor.channel_name.substring(0, 2).toUpperCase()}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div>
                                                <h3 className="font-semibold line-clamp-1">
                                                    {competitor.channel_name}
                                                </h3>
                                                <p className="text-xs text-muted-foreground">
                                                    Added {new Date(competitor.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8"
                                                onClick={() => handleSyncCompetitor(competitor)}
                                                disabled={syncingId === competitor.id}
                                            >
                                                <RefreshCw
                                                    className={cn(
                                                        "h-4 w-4",
                                                        syncingId === competitor.id && "animate-spin"
                                                    )}
                                                />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-destructive hover:text-destructive"
                                                onClick={() => {
                                                    setCompetitorToDelete(competitor);
                                                    setDeleteDialogOpen(true);
                                                }}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Metrics */}
                                    <div className="grid grid-cols-3 gap-4 mb-4">
                                        <div className="text-center p-3 bg-muted/50 rounded-lg">
                                            <Users className="h-4 w-4 mx-auto mb-1 text-blue-500" />
                                            <p className="text-sm font-semibold">
                                                {formatNumber(competitor.subscriber_count)}
                                            </p>
                                            <p className="text-xs text-muted-foreground">Subs</p>
                                        </div>
                                        <div className="text-center p-3 bg-muted/50 rounded-lg">
                                            <Video className="h-4 w-4 mx-auto mb-1 text-green-500" />
                                            <p className="text-sm font-semibold">
                                                {formatNumber(competitor.video_count)}
                                            </p>
                                            <p className="text-xs text-muted-foreground">Videos</p>
                                        </div>
                                        <div className="text-center p-3 bg-muted/50 rounded-lg">
                                            <Eye className="h-4 w-4 mx-auto mb-1 text-purple-500" />
                                            <p className="text-sm font-semibold">
                                                {formatNumber(competitor.view_count)}
                                            </p>
                                            <p className="text-xs text-muted-foreground">Views</p>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2">
                                        <Link href={`/dashboard/competitors/${competitor.id}`} className="flex-1">
                                            <Button variant="outline" className="w-full">
                                                <TrendingUp className="mr-2 h-4 w-4" />
                                                View Analysis
                                            </Button>
                                        </Link>
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            asChild
                                        >
                                            <a
                                                href={competitor.channel_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                <ExternalLink className="h-4 w-4" />
                                            </a>
                                        </Button>
                                    </div>

                                    {/* Last Synced */}
                                    {competitor.last_synced_at && (
                                        <p className="text-xs text-muted-foreground mt-3 text-center">
                                            Last synced: {new Date(competitor.last_synced_at).toLocaleString()}
                                        </p>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Results count */}
                {!loading && safeFilteredCompetitors.length > 0 && (
                    <div className="text-sm text-muted-foreground text-center">
                        Showing {safeFilteredCompetitors.length} of {safeCompetitors.length} competitor
                        {safeCompetitors.length !== 1 ? "s" : ""}
                    </div>
                )}
            </div>


            {/* Add Competitor Modal */}
            <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Add Competitor</DialogTitle>
                        <DialogDescription>
                            Enter the YouTube channel URL to start tracking a competitor.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Channel URL</label>
                            <Input
                                placeholder="https://youtube.com/@channelname or channel ID"
                                value={channelUrl}
                                onChange={(e) => setChannelUrl(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                You can paste the full channel URL or just the channel ID
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setAddModalOpen(false)}
                            disabled={adding}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleAddCompetitor}
                            disabled={adding || !channelUrl.trim()}
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                        >
                            {adding ? "Adding..." : "Add Competitor"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Remove Competitor</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to remove {competitorToDelete?.channel_name} from
                            your tracked competitors? This will delete all historical data for this
                            channel.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDeleteCompetitor}
                            disabled={deleting}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {deleting ? "Removing..." : "Remove"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </DashboardLayout>
    );
}
