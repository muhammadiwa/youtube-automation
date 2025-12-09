"use client";

import { useState } from "react";
import { Bell, Check, Settings as SettingsIcon, X } from "lucide-react";
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

interface Notification {
    id: string;
    title: string;
    message: string;
    timestamp: string;
    read: boolean;
    type: "info" | "success" | "warning" | "error";
}

// Mock notifications - will be replaced with real API data
const mockNotifications: Notification[] = [
    {
        id: "1",
        title: "Stream Started",
        message: "Your stream 'Live Gaming Session' has started successfully",
        timestamp: "2 minutes ago",
        read: false,
        type: "success",
    },
    {
        id: "2",
        title: "Upload Complete",
        message: "Video 'Tutorial #5' has been uploaded and is processing",
        timestamp: "15 minutes ago",
        read: false,
        type: "info",
    },
    {
        id: "3",
        title: "Quota Warning",
        message: "You've reached 80% of your API quota for this month",
        timestamp: "1 hour ago",
        read: false,
        type: "warning",
    },
    {
        id: "4",
        title: "New Subscriber Milestone",
        message: "Congratulations! You've reached 10,000 subscribers",
        timestamp: "2 hours ago",
        read: true,
        type: "success",
    },
    {
        id: "5",
        title: "Token Expiring Soon",
        message: "YouTube token for 'Gaming Channel' expires in 3 days",
        timestamp: "5 hours ago",
        read: true,
        type: "warning",
    },
];

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
    const [notifications, setNotifications] =
        useState<Notification[]>(mockNotifications);
    const [open, setOpen] = useState(false);

    const unreadCount = notifications.filter((n) => !n.read).length;

    const markAsRead = (id: string) => {
        setNotifications((prev) =>
            prev.map((n) => (n.id === id ? { ...n, read: true } : n))
        );
    };

    const markAllAsRead = () => {
        setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    };

    const deleteNotification = (id: string) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
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
                    {notifications.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-[200px] text-center p-4">
                            <Bell className="h-12 w-12 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">
                                No notifications yet
                            </p>
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
                                    onClick={() => markAsRead(notification.id)}
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
