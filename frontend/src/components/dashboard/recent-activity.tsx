"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Upload,
    Radio,
    UserPlus,
    Video,
    AlertCircle,
    CheckCircle,
    Clock,
    Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { notificationsApi, type Notification } from "@/lib/api/notifications";

type ActivityType = "upload" | "stream" | "account" | "video" | "error" | "success";

interface ActivityItem {
    id: string;
    type: ActivityType;
    title: string;
    description: string;
    timestamp: string;
}

const activityConfig = {
    upload: {
        icon: Upload,
        bgColor: "bg-blue-500/10",
        iconColor: "text-blue-500",
    },
    stream: {
        icon: Radio,
        bgColor: "bg-red-500/10",
        iconColor: "text-red-500",
    },
    account: {
        icon: UserPlus,
        bgColor: "bg-green-500/10",
        iconColor: "text-green-500",
    },
    video: {
        icon: Video,
        bgColor: "bg-purple-500/10",
        iconColor: "text-purple-500",
    },
    error: {
        icon: AlertCircle,
        bgColor: "bg-red-500/10",
        iconColor: "text-red-500",
    },
    success: {
        icon: CheckCircle,
        bgColor: "bg-green-500/10",
        iconColor: "text-green-500",
    },
};

// Map notification types to activity types
function mapNotificationToActivity(notification: Notification): ActivityItem {
    let type: ActivityType = "success";

    // Map based on notification type/category
    if (notification.type?.includes("upload") || notification.type?.includes("video")) {
        type = "upload";
    } else if (notification.type?.includes("stream") || notification.type?.includes("live")) {
        type = "stream";
    } else if (notification.type?.includes("account") || notification.type?.includes("channel")) {
        type = "account";
    } else if (notification.type?.includes("error") || notification.type?.includes("fail")) {
        type = "error";
    }

    // Format timestamp
    const date = new Date(notification.created_at);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    let timestamp = "";
    if (diffMins < 1) {
        timestamp = "Just now";
    } else if (diffMins < 60) {
        timestamp = `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    } else if (diffHours < 24) {
        timestamp = `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    } else {
        timestamp = `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
    }

    return {
        id: notification.id,
        type,
        title: notification.title,
        description: notification.message || "",
        timestamp,
    };
}

export function RecentActivity() {
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadActivities = async () => {
            try {
                const notifications = await notificationsApi.getNotifications({
                    page: 1,
                    page_size: 10,
                });

                if (Array.isArray(notifications)) {
                    setActivities(notifications.map(mapNotificationToActivity));
                } else if (notifications?.items) {
                    setActivities(notifications.items.map(mapNotificationToActivity));
                }
            } catch (error) {
                console.error("Failed to load recent activity:", error);
            } finally {
                setLoading(false);
            }
        };
        loadActivities();
    }, []);

    return (
        <Card className="border-0 bg-card shadow-lg h-full">
            <CardHeader className="pb-4">
                <div className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-lg">Recent Activity</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <ScrollArea className="h-[350px] pr-4">
                    {loading ? (
                        <div className="space-y-3">
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="flex items-start gap-4 p-3">
                                    <Skeleton className="h-10 w-10 rounded-xl" />
                                    <div className="flex-1 space-y-2">
                                        <Skeleton className="h-4 w-3/4" />
                                        <Skeleton className="h-3 w-1/2" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : activities.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center py-8">
                            <Activity className="h-12 w-12 text-muted-foreground/50 mb-4" />
                            <p className="text-sm text-muted-foreground">No recent activity</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {activities.map((activity) => {
                                const config = activityConfig[activity.type];
                                const Icon = config.icon;

                                return (
                                    <div
                                        key={activity.id}
                                        className="group flex items-start gap-4 p-3 rounded-xl transition-all duration-300 hover:bg-accent/50"
                                    >
                                        <div
                                            className={cn(
                                                "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110",
                                                config.bgColor
                                            )}
                                        >
                                            <Icon className={cn("h-5 w-5", config.iconColor)} />
                                        </div>
                                        <div className="flex-1 min-w-0 space-y-1">
                                            <p className="text-sm font-medium leading-none truncate">
                                                {activity.title}
                                            </p>
                                            <p className="text-sm text-muted-foreground truncate">
                                                {activity.description}
                                            </p>
                                            <p className="text-xs text-muted-foreground/70">
                                                {activity.timestamp}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
