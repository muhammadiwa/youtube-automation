"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import competitorsApi, {
    CompetitorAlert,
    CompetitorAlertPreference,
} from "@/lib/api/competitors";
import {
    Bell,
    BellOff,
    Video,
    TrendingUp,
    Award,
    Clock,
    Check,
    CheckCheck,
    Trash2,
    ExternalLink,
    Settings,
    Target,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function CompetitorAlertsPage() {
    const [alerts, setAlerts] = useState<CompetitorAlert[]>([]);
    const [preferences, setPreferences] = useState<CompetitorAlertPreference[]>([]);
    const [loading, setLoading] = useState(true);
    const [unreadCount, setUnreadCount] = useState(0);
    const [preferencesModalOpen, setPreferencesModalOpen] = useState(false);
    const [updatingPreference, setUpdatingPreference] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [alertsData, preferencesData] = await Promise.all([
                competitorsApi.getAlerts({ page_size: 50 }),
                competitorsApi.getAlertPreferences(),
            ]);
            setAlerts(alertsData.items || []);
            setUnreadCount(alertsData.unread_count || 0);
            setPreferences(preferencesData || []);
        } catch (error) {
            console.error("Failed to load alerts:", error);
        } finally {
            setLoading(false);
        }
    };


    const handleMarkAsRead = async (alertId: string) => {
        try {
            await competitorsApi.markAlertAsRead(alertId);
            setAlerts((prev) =>
                prev.map((a) => (a.id === alertId ? { ...a, read: true } : a))
            );
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch (error) {
            console.error("Failed to mark alert as read:", error);
        }
    };

    const handleMarkAllAsRead = async () => {
        try {
            await competitorsApi.markAllAlertsAsRead();
            setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error("Failed to mark all alerts as read:", error);
        }
    };

    const handleDeleteAlert = async (alertId: string) => {
        try {
            await competitorsApi.deleteAlert(alertId);
            const deletedAlert = alerts.find((a) => a.id === alertId);
            setAlerts((prev) => prev.filter((a) => a.id !== alertId));
            if (deletedAlert && !deletedAlert.read) {
                setUnreadCount((prev) => Math.max(0, prev - 1));
            }
        } catch (error) {
            console.error("Failed to delete alert:", error);
        }
    };

    const handleUpdatePreference = async (
        competitorId: string,
        field: keyof Omit<CompetitorAlertPreference, "competitor_id" | "competitor_name">,
        value: boolean
    ) => {
        try {
            setUpdatingPreference(`${competitorId}-${field}`);
            await competitorsApi.updateAlertPreference(competitorId, { [field]: value });
            setPreferences((prev) =>
                prev.map((p) =>
                    p.competitor_id === competitorId ? { ...p, [field]: value } : p
                )
            );
        } catch (error) {
            console.error("Failed to update preference:", error);
        } finally {
            setUpdatingPreference(null);
        }
    };

    const getAlertIcon = (type: string) => {
        switch (type) {
            case "new_video":
                return Video;
            case "milestone":
                return Award;
            case "trending":
                return TrendingUp;
            case "upload_frequency":
                return Clock;
            default:
                return Bell;
        }
    };

    const getAlertColor = (type: string) => {
        switch (type) {
            case "new_video":
                return "bg-blue-500/10 text-blue-500";
            case "milestone":
                return "bg-amber-500/10 text-amber-500";
            case "trending":
                return "bg-green-500/10 text-green-500";
            case "upload_frequency":
                return "bg-purple-500/10 text-purple-500";
            default:
                return "bg-gray-500/10 text-gray-500";
        }
    };

    const unreadAlerts = alerts.filter((a) => !a.read);
    const readAlerts = alerts.filter((a) => a.read);

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Competitors", href: "/dashboard/competitors" },
                { label: "Alerts" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Competitor Alerts</h1>
                        <p className="text-muted-foreground">
                            Stay updated on competitor activity
                        </p>
                    </div>
                    <div className="flex gap-2">
                        {unreadCount > 0 && (
                            <Button variant="outline" onClick={handleMarkAllAsRead}>
                                <CheckCheck className="mr-2 h-4 w-4" />
                                Mark All Read
                            </Button>
                        )}
                        <Button
                            variant="outline"
                            onClick={() => setPreferencesModalOpen(true)}
                        >
                            <Settings className="mr-2 h-4 w-4" />
                            Preferences
                        </Button>
                    </div>
                </div>


                {/* Alerts Content */}
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3].map((i) => (
                            <Skeleton key={i} className="h-24" />
                        ))}
                    </div>
                ) : alerts.length === 0 ? (
                    <Card className="border-0 bg-card shadow-lg">
                        <CardContent className="py-12 text-center">
                            <BellOff className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No alerts yet</h3>
                            <p className="text-muted-foreground mb-4">
                                You'll receive notifications when your competitors publish new content
                            </p>
                            <Link href="/dashboard/competitors">
                                <Button>
                                    <Target className="mr-2 h-4 w-4" />
                                    Manage Competitors
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <Tabs defaultValue="unread" className="space-y-6">
                        <TabsList>
                            <TabsTrigger value="unread" className="relative">
                                Unread
                                {unreadCount > 0 && (
                                    <Badge
                                        variant="destructive"
                                        className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs"
                                    >
                                        {unreadCount}
                                    </Badge>
                                )}
                            </TabsTrigger>
                            <TabsTrigger value="all">All Alerts</TabsTrigger>
                        </TabsList>

                        <TabsContent value="unread" className="space-y-4">
                            {unreadAlerts.length === 0 ? (
                                <Card className="border-0 bg-card shadow-lg">
                                    <CardContent className="py-8 text-center">
                                        <Check className="mx-auto h-12 w-12 text-green-500 mb-4" />
                                        <h3 className="text-lg font-semibold mb-2">All caught up!</h3>
                                        <p className="text-muted-foreground">
                                            No unread alerts at the moment
                                        </p>
                                    </CardContent>
                                </Card>
                            ) : (
                                unreadAlerts.map((alert) => (
                                    <AlertCard
                                        key={alert.id}
                                        alert={alert}
                                        onMarkAsRead={handleMarkAsRead}
                                        onDelete={handleDeleteAlert}
                                        getAlertIcon={getAlertIcon}
                                        getAlertColor={getAlertColor}
                                    />
                                ))
                            )}
                        </TabsContent>

                        <TabsContent value="all" className="space-y-4">
                            {alerts.map((alert) => (
                                <AlertCard
                                    key={alert.id}
                                    alert={alert}
                                    onMarkAsRead={handleMarkAsRead}
                                    onDelete={handleDeleteAlert}
                                    getAlertIcon={getAlertIcon}
                                    getAlertColor={getAlertColor}
                                />
                            ))}
                        </TabsContent>
                    </Tabs>
                )}
            </div>

            {/* Preferences Modal */}
            <Dialog open={preferencesModalOpen} onOpenChange={setPreferencesModalOpen}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>Alert Preferences</DialogTitle>
                        <DialogDescription>
                            Configure which alerts you want to receive for each competitor
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-6 py-4">
                        {preferences.length === 0 ? (
                            <div className="text-center py-8 text-muted-foreground">
                                <Target className="mx-auto h-12 w-12 mb-4 opacity-50" />
                                <p>No competitors tracked yet</p>
                                <Link href="/dashboard/competitors">
                                    <Button variant="link">Add competitors to configure alerts</Button>
                                </Link>
                            </div>
                        ) : (
                            preferences.map((pref) => (
                                <Card key={pref.competitor_id} className="border">
                                    <CardHeader className="pb-3">
                                        <CardTitle className="text-base">{pref.competitor_name}</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor={`${pref.competitor_id}-new-video`} className="flex items-center gap-2">
                                                    <Video className="h-4 w-4 text-blue-500" />
                                                    New Videos
                                                </Label>
                                                <Switch
                                                    id={`${pref.competitor_id}-new-video`}
                                                    checked={pref.new_video_enabled}
                                                    onCheckedChange={(checked) =>
                                                        handleUpdatePreference(pref.competitor_id, "new_video_enabled", checked)
                                                    }
                                                    disabled={updatingPreference === `${pref.competitor_id}-new_video_enabled`}
                                                />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor={`${pref.competitor_id}-milestone`} className="flex items-center gap-2">
                                                    <Award className="h-4 w-4 text-amber-500" />
                                                    Milestones
                                                </Label>
                                                <Switch
                                                    id={`${pref.competitor_id}-milestone`}
                                                    checked={pref.milestone_enabled}
                                                    onCheckedChange={(checked) =>
                                                        handleUpdatePreference(pref.competitor_id, "milestone_enabled", checked)
                                                    }
                                                    disabled={updatingPreference === `${pref.competitor_id}-milestone_enabled`}
                                                />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor={`${pref.competitor_id}-trending`} className="flex items-center gap-2">
                                                    <TrendingUp className="h-4 w-4 text-green-500" />
                                                    Trending
                                                </Label>
                                                <Switch
                                                    id={`${pref.competitor_id}-trending`}
                                                    checked={pref.trending_enabled}
                                                    onCheckedChange={(checked) =>
                                                        handleUpdatePreference(pref.competitor_id, "trending_enabled", checked)
                                                    }
                                                    disabled={updatingPreference === `${pref.competitor_id}-trending_enabled`}
                                                />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor={`${pref.competitor_id}-frequency`} className="flex items-center gap-2">
                                                    <Clock className="h-4 w-4 text-purple-500" />
                                                    Upload Frequency
                                                </Label>
                                                <Switch
                                                    id={`${pref.competitor_id}-frequency`}
                                                    checked={pref.upload_frequency_enabled}
                                                    onCheckedChange={(checked) =>
                                                        handleUpdatePreference(pref.competitor_id, "upload_frequency_enabled", checked)
                                                    }
                                                    disabled={updatingPreference === `${pref.competitor_id}-upload_frequency_enabled`}
                                                />
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))
                        )}
                    </div>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    );
}


// Alert Card Component
function AlertCard({
    alert,
    onMarkAsRead,
    onDelete,
    getAlertIcon,
    getAlertColor,
}: {
    alert: CompetitorAlert;
    onMarkAsRead: (id: string) => void;
    onDelete: (id: string) => void;
    getAlertIcon: (type: string) => any;
    getAlertColor: (type: string) => string;
}) {
    const Icon = getAlertIcon(alert.type);

    return (
        <Card
            className={cn(
                "border-0 bg-card shadow-lg transition-all",
                !alert.read && "ring-2 ring-primary/20"
            )}
        >
            <CardContent className="p-4">
                <div className="flex gap-4">
                    {/* Video Thumbnail or Icon */}
                    {alert.video_thumbnail ? (
                        <div className="relative w-32 h-20 rounded-lg overflow-hidden flex-shrink-0">
                            <img
                                src={alert.video_thumbnail}
                                alt={alert.video_title || "Video"}
                                className="w-full h-full object-cover"
                            />
                        </div>
                    ) : (
                        <div
                            className={cn(
                                "h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0",
                                getAlertColor(alert.type)
                            )}
                        >
                            <Icon className="h-6 w-6" />
                        </div>
                    )}

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <h4 className="font-semibold">{alert.title}</h4>
                                    {!alert.read && (
                                        <Badge variant="default" className="text-xs">
                                            New
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                    {alert.message}
                                </p>
                                <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                                    <span>{alert.competitor_name}</span>
                                    <span>•</span>
                                    <span>{new Date(alert.created_at).toLocaleString()}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                        {!alert.read && (
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => onMarkAsRead(alert.id)}
                            >
                                <Check className="h-4 w-4" />
                            </Button>
                        )}
                        {alert.video_id && (
                            <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                                <a
                                    href={`https://youtube.com/watch?v=${alert.video_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    <ExternalLink className="h-4 w-4" />
                                </a>
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => onDelete(alert.id)}
                        >
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
