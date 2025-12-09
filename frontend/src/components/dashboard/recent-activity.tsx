"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Upload,
    Radio,
    UserPlus,
    Video,
    AlertCircle,
    CheckCircle,
    Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Activity {
    id: string;
    type: "upload" | "stream" | "account" | "video" | "error" | "success";
    title: string;
    description: string;
    timestamp: string;
}

// Mock data - will be replaced with real API data
const mockActivities: Activity[] = [
    {
        id: "1",
        type: "upload",
        title: "Video uploaded successfully",
        description: "My awesome video.mp4",
        timestamp: "2 minutes ago",
    },
    {
        id: "2",
        type: "stream",
        title: "Stream started",
        description: "Live Gaming Session #42",
        timestamp: "15 minutes ago",
    },
    {
        id: "3",
        type: "account",
        title: "New account connected",
        description: "Gaming Channel",
        timestamp: "1 hour ago",
    },
    {
        id: "4",
        type: "success",
        title: "Video published",
        description: "Tutorial: Getting Started",
        timestamp: "2 hours ago",
    },
    {
        id: "5",
        type: "video",
        title: "Metadata updated",
        description: "Updated title and description",
        timestamp: "3 hours ago",
    },
];

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

export function RecentActivity() {
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
                    <div className="space-y-3">
                        {mockActivities.map((activity) => {
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
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
