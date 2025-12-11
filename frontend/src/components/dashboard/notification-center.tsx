"use client";

import { useState, useEffect, useCallback } from "react";
import { Bell, Check, Settings as SettingsIcon, X, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import notificationsApi, { Notification as ApiNotification } from "@/lib/api/notifications";

interface Notification {
    id: string;
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    type: "info" | "success" | "warning" | "error";
    action_url?: string;
}

// Map API notification type to UI type
const mapNotificationType = (apiType: string): "info" | "success" | "warning" | "error" => {
    const successTypes = ["payment_success", "subscription_activated", "subscription_renewed", "upload_complete", "stream_started"];
    const warningTypes = ["quota_warning", "token_expiring", "subscription_expiring", "subscription_cancelled"];
    const errorTypes = ["payment_failed", "stream_error", "upload_failed", "strike_detected", "subscription_expired"];

    if (successTypes.includes(apiType)) return "success";
    if (warningTypes.includes(apiType)) return "warning";
    if (errorTypes.includes(apiType)) return "error";
    return "info";
};

// Format timestamp to relative time
const formatTimestamp = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
    return date.toLocaleDateString();
};


const typeColors = {
    info: "bg-blue-500",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    error: "bg-red-500",
};

interface NotificationCenterProps {
    onOpenPreferences?: () => void;
}

export function NotificationCenter({
    onOpenPreferences,
}: NotificationCenterProps) {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(false);

    // Fetch notifications from API
    const fetchNotifications = useCallback(async () => {
        try {
            const response = await notificationsApi.getNotifications({ page_size: 20 });
            const mappedNotifications: Notification[] = response.items.map((item: ApiNotification) => ({
                id: item.id,
                title: item.title,
                message: item.message,
                timestamp: formatTimestamp(item.created_at),
                read: item.read,
                type: mapNotificationType(item.type),
                action_url: item.action_url,
            }));
            setNotifications(mappedNotifications);
            setUnreadCount(response.unread_count);
        } catch (error) {
            console.error("Failed to fetch notifications:", error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch unread count periodically
    const fetchUnreadCount = useCallback(async () => {
        try {
            const count = await notificationsApi.getUnreadCount();
            setUnreadCount(count);
        } catch (error) {
            console.error("Failed to fetch unread count:", error);
        }
    }, []);

    // Initial fetch and polling
    useEffect(() => {
        fetchNotifications();

        // Poll for new notifications every 30 seconds
        const interval = setInterval(fetchUnreadCount, 30000);
        return () => clearInterval(interval);
    }, [fetchNotifications, fetchUnreadCount]);


    // Refresh when dropdown opens
    useEffect(() => {
        if (open) {
            fetchNotifications();
        }
    }, [open, fetchNotifications]);

    const markAsRead = async (id: string) => {
        try {
            await notificationsApi.markAsRead(id);
            setNotifications((prev) =>
                prev.map((n) => (n.id === id ? { ...n, read: true } : n))
            );
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch (error) {
            console.error("Failed to mark notification as read:", error);
        }
    };

    const markAllAsRead = async () => {
        try {
            await notificationsApi.markAllAsRead();
            setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
            setUnreadCount(0);
        } catch (error) {
            console.error("Failed to mark all as read:", error);
        }
    };

    const deleteNotification = async (id: string) => {
        try {
            await notificationsApi.deleteNotification(id);
            const wasUnread = notifications.find((n) => n.id === id && !n.read);
            setNotifications((prev) => prev.filter((n) => n.id !== id));
            if (wasUnread) {
                setUnreadCount((prev) => Math.max(0, prev - 1));
            }
        } catch (error) {
            console.error("Failed to delete notification:", error);
        }
    };

    return (
        <DropdownMenu open={open} onOpenChange={setOpen}>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                        <Badge
                            variant="destructive"
                            className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
                        >
                            {unreadCount > 9 ? "9+" : unreadCount}
                        </Badge>
                    )}
                    <span className="sr-only">Notifications</span>
                </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-96 p-0">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <h3 className="font-semibold">Notifications</h3>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => fetchNotifications()}
                            className="h-8 w-8"
                            disabled={loading}
                        >
                            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                            <span className="sr-only">Refresh</span>
                        </Button>
                        {unreadCount > 0 && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={markAllAsRead}
                                className="h-8 text-xs"
                            >
                                <Check className="mr-1 h-3 w-3" />
                                Mark all read
                            </Button>
                        )}
                        {onOpenPreferences && (
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={onOpenPreferences}
                                className="h-8 w-8"
                            >
                                <SettingsIcon className="h-4 w-4" />
                                <span className="sr-only">Notification preferences</span>
                            </Button>
                        )}
                    </div>
                </div>

                {/* Notifications List */}
                <ScrollArea className="h-[400px]">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-[200px] text-center p-4">
                            <RefreshCw className="h-8 w-8 text-muted-foreground animate-spin mb-2" />
                            <p className="text-sm text-muted-foreground">Loading notifications...</p>
                        </div>
                    ) : notifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-[200px] text-center p-4">
                            <Bell className="h-12 w-12 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">No notifications yet</p>
                        </div>
                    ) : (

                        <div className="divide-y">
                            {notifications.map((notification) => (
                                <div
                                    key={notification.id}
                                    className={cn(
                                        "p-4 hover:bg-muted/50 transition-colors cursor-pointer group relative",
                                        !notification.read && "bg-muted/30"
                                    )}
                                    onClick={() => {
                                        if (!notification.read) {
                                            markAsRead(notification.id);
                                        }
                                        if (notification.action_url) {
                                            window.location.href = notification.action_url;
                                        }
                                    }}
                                >
                                    <div className="flex gap-3">
                                        {/* Type Indicator */}
                                        <div
                                            className={cn(
                                                "w-2 h-2 rounded-full mt-2 flex-shrink-0",
                                                typeColors[notification.type]
                                            )}
                                        />

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2">
                                                <p className="text-sm font-medium leading-none">
                                                    {notification.title}
                                                </p>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteNotification(notification.id);
                                                    }}
                                                >
                                                    <X className="h-3 w-3" />
                                                    <span className="sr-only">Delete</span>
                                                </Button>
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                {notification.message}
                                            </p>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {notification.timestamp}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </ScrollArea>


                {/* Footer */}
                {notifications.length > 0 && (
                    <>
                        <Separator />
                        <div className="p-2">
                            <Button
                                variant="ghost"
                                className="w-full text-sm"
                                onClick={() => setOpen(false)}
                            >
                                View all notifications
                            </Button>
                        </div>
                    </>
                )}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
