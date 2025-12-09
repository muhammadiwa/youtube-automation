"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import { useToast } from "@/components/ui/toast";
import strikesApi, {
    StrikeAlert,
    PausedStream,
} from "@/lib/api/strikes";
import {
    AlertTriangle,
    X,
    Play,
    PauseCircle,
    Bell,
    ShieldAlert,
    Clock,
    CheckCircle2,
    XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

// ============ Strike Warning Banner ============
interface StrikeWarningBannerProps {
    className?: string;
}

export function StrikeWarningBanner({ className }: StrikeWarningBannerProps) {
    const [alerts, setAlerts] = useState<StrikeAlert[]>([]);
    const [dismissed, setDismissed] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAlerts();
    }, []);

    const loadAlerts = async () => {
        try {
            setLoading(false);
            const data = await strikesApi.getAlerts({ unread_only: true, page_size: 5 });
            setAlerts(data.items || []);
        } catch (error) {
            console.error("Failed to load strike alerts:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDismiss = async (alertId: string) => {
        try {
            await strikesApi.markAlertAsRead(alertId);
            setDismissed((prev) => new Set(Array.from(prev).concat(alertId)));
        } catch (error) {
            console.error("Failed to dismiss alert:", error);
        }
    };

    const visibleAlerts = alerts.filter((a) => !dismissed.has(a.id));
    const criticalAlerts = visibleAlerts.filter((a) => a.severity === "critical" || a.severity === "error");

    if (loading || criticalAlerts.length === 0) return null;

    return (
        <div className={cn("space-y-2", className)}>
            {criticalAlerts.map((alert) => (
                <div
                    key={alert.id}
                    className={cn(
                        "flex items-center justify-between gap-4 px-4 py-3 rounded-lg",
                        alert.severity === "critical" && "bg-red-500/10 border border-red-500/20",
                        alert.severity === "error" && "bg-orange-500/10 border border-orange-500/20"
                    )}
                >
                    <div className="flex items-center gap-3">
                        <AlertTriangle className={cn(
                            "h-5 w-5 flex-shrink-0",
                            alert.severity === "critical" && "text-red-500",
                            alert.severity === "error" && "text-orange-500"
                        )} />
                        <div>
                            <p className="font-medium text-sm">{alert.title}</p>
                            <p className="text-xs text-muted-foreground">{alert.message}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Link href="/dashboard/strikes">
                            <Button variant="outline" size="sm">
                                View Details
                            </Button>
                        </Link>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleDismiss(alert.id)}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            ))}
        </div>
    );
}


// ============ Paused Streams Indicator ============
interface PausedStreamsIndicatorProps {
    className?: string;
    compact?: boolean;
}

export function PausedStreamsIndicator({ className, compact = false }: PausedStreamsIndicatorProps) {
    const [pausedStreams, setPausedStreams] = useState<PausedStream[]>([]);
    const [loading, setLoading] = useState(true);
    const [resumeDialogOpen, setResumeDialogOpen] = useState(false);
    const [selectedStream, setSelectedStream] = useState<PausedStream | null>(null);
    const [resuming, setResuming] = useState(false);
    const { addToast } = useToast();

    useEffect(() => {
        loadPausedStreams();
    }, []);

    const loadPausedStreams = async () => {
        try {
            setLoading(false);
            const data = await strikesApi.getPausedStreams();
            setPausedStreams(data.items || []);
        } catch (error) {
            console.error("Failed to load paused streams:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleResumeClick = (stream: PausedStream) => {
        setSelectedStream(stream);
        setResumeDialogOpen(true);
    };

    const handleConfirmResume = async () => {
        if (!selectedStream) return;
        try {
            setResuming(true);
            await strikesApi.resumeStream(selectedStream.id);
            addToast({
                type: "success",
                title: "Stream Resumed",
                description: `"${selectedStream.stream_title}" has been resumed successfully.`,
            });
            setResumeDialogOpen(false);
            setSelectedStream(null);
            await loadPausedStreams();
        } catch (error) {
            console.error("Failed to resume stream:", error);
            addToast({
                type: "error",
                title: "Failed to Resume",
                description: "There was an error resuming the stream. Please try again.",
            });
        } finally {
            setResuming(false);
        }
    };

    if (loading || pausedStreams.length === 0) return null;

    if (compact) {
        return (
            <>
                <Link href="/dashboard/strikes">
                    <Badge
                        variant="destructive"
                        className={cn("cursor-pointer hover:bg-destructive/90", className)}
                    >
                        <PauseCircle className="mr-1 h-3 w-3" />
                        {pausedStreams.length} Paused
                    </Badge>
                </Link>
            </>
        );
    }

    return (
        <>
            <div className={cn("space-y-3", className)}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <PauseCircle className="h-5 w-5 text-orange-500" />
                        <h3 className="font-semibold">Paused Streams</h3>
                        <Badge variant="secondary">{pausedStreams.length}</Badge>
                    </div>
                    <Link href="/dashboard/strikes">
                        <Button variant="ghost" size="sm">
                            View All
                        </Button>
                    </Link>
                </div>
                <div className="space-y-2">
                    {pausedStreams.slice(0, 3).map((stream) => (
                        <div
                            key={stream.id}
                            className="flex items-center justify-between p-3 bg-orange-500/5 border border-orange-500/20 rounded-lg"
                        >
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">{stream.stream_title}</p>
                                <p className="text-xs text-muted-foreground">
                                    {stream.channel_name} • Paused due to strike
                                </p>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleResumeClick(stream)}
                            >
                                <Play className="mr-1 h-3 w-3" />
                                Resume
                            </Button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Resume Confirmation Dialog */}
            <AlertDialog open={resumeDialogOpen} onOpenChange={setResumeDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Resume Stream?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This stream was paused due to a strike on the channel. Are you sure you want to resume it?
                            <br /><br />
                            <strong>Stream:</strong> {selectedStream?.stream_title}
                            <br />
                            <strong>Channel:</strong> {selectedStream?.channel_name}
                            <br />
                            <strong>Reason:</strong> {selectedStream?.pause_reason}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={resuming}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmResume}
                            disabled={resuming}
                            className="bg-green-600 hover:bg-green-700"
                        >
                            {resuming ? "Resuming..." : "Yes, Resume Stream"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}


// ============ Strike Notification Toast Hook ============
export function useStrikeNotifications() {
    const { addToast } = useToast();
    const [lastChecked, setLastChecked] = useState<Date>(new Date());

    useEffect(() => {
        // Check for new alerts every 30 seconds
        const interval = setInterval(async () => {
            try {
                const data = await strikesApi.getAlerts({ unread_only: true, page_size: 10 });
                const newAlerts = (data.items || []).filter(
                    (alert) => new Date(alert.created_at) > lastChecked
                );

                newAlerts.forEach((alert) => {
                    const toastType = alert.severity === "critical" || alert.severity === "error"
                        ? "error"
                        : alert.severity === "warning"
                            ? "warning"
                            : "info";

                    addToast({
                        type: toastType,
                        title: alert.title,
                        description: alert.message,
                    });
                });

                if (newAlerts.length > 0) {
                    setLastChecked(new Date());
                }
            } catch (error) {
                // Silently fail - don't spam errors
            }
        }, 30000);

        return () => clearInterval(interval);
    }, [lastChecked, addToast]);
}

// ============ Strike Alert Badge (for header) ============
interface StrikeAlertBadgeProps {
    className?: string;
}

export function StrikeAlertBadge({ className }: StrikeAlertBadgeProps) {
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadUnreadCount();
        // Refresh every minute
        const interval = setInterval(loadUnreadCount, 60000);
        return () => clearInterval(interval);
    }, []);

    const loadUnreadCount = async () => {
        try {
            const data = await strikesApi.getAlerts({ unread_only: true, page_size: 1 });
            setUnreadCount(data.unread_count || 0);
        } catch (error) {
            // Silently fail
        } finally {
            setLoading(false);
        }
    };

    if (loading || unreadCount === 0) return null;

    return (
        <Link href="/dashboard/strikes">
            <Button
                variant="ghost"
                size="icon"
                className={cn("relative", className)}
            >
                <ShieldAlert className="h-5 w-5 text-orange-500" />
                <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">
                    {unreadCount > 9 ? "9+" : unreadCount}
                </span>
            </Button>
        </Link>
    );
}

// ============ Strike Status Mini Card ============
interface StrikeStatusMiniCardProps {
    accountId: string;
    channelName: string;
    strikeCount: number;
    className?: string;
}

export function StrikeStatusMiniCard({
    accountId,
    channelName,
    strikeCount,
    className,
}: StrikeStatusMiniCardProps) {
    if (strikeCount === 0) {
        return (
            <div className={cn("flex items-center gap-2 text-green-500", className)}>
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm">No strikes</span>
            </div>
        );
    }

    const severity = strikeCount >= 3 ? "critical" : strikeCount >= 2 ? "high" : "medium";

    return (
        <Link href="/dashboard/strikes">
            <div
                className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors",
                    severity === "critical" && "bg-red-500/10 text-red-500 hover:bg-red-500/20",
                    severity === "high" && "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
                    severity === "medium" && "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
                    className
                )}
            >
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">
                    {strikeCount} Strike{strikeCount !== 1 ? "s" : ""}
                </span>
                {severity === "critical" && (
                    <Badge variant="destructive" className="text-xs">
                        At Risk
                    </Badge>
                )}
            </div>
        </Link>
    );
}

// ============ Inline Strike Warning ============
interface InlineStrikeWarningProps {
    strikeCount: number;
    className?: string;
}

export function InlineStrikeWarning({ strikeCount, className }: InlineStrikeWarningProps) {
    if (strikeCount === 0) return null;

    const message =
        strikeCount >= 3
            ? "Channel at risk of termination!"
            : strikeCount === 2
                ? "Warning: 2 strikes - one more may result in termination"
                : "This channel has an active strike";

    return (
        <div
            className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-sm",
                strikeCount >= 3 && "bg-red-500/10 text-red-500 border border-red-500/20",
                strikeCount === 2 && "bg-orange-500/10 text-orange-500 border border-orange-500/20",
                strikeCount === 1 && "bg-yellow-500/10 text-yellow-500 border border-yellow-500/20",
                className
            )}
        >
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>{message}</span>
        </div>
    );
}

export default {
    StrikeWarningBanner,
    PausedStreamsIndicator,
    useStrikeNotifications,
    StrikeAlertBadge,
    StrikeStatusMiniCard,
    InlineStrikeWarning,
};
