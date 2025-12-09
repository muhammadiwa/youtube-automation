"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
    Upload,
    Radio,
    UserPlus,
    Video,
    AlertCircle,
    CheckCircle,
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

const activityIcons = {
    upload: Upload,
    stream: Radio,
    account: UserPlus,
    video: Video,
    error: AlertCircle,
    success: CheckCircle,
};

const activityColors = {
    upload: "text-blue-500",
    stream: "text-red-500",
    account: "text-green-500",
    video: "text-purple-500",
    error: "text-red-500",
    success: "text-green-500",
};

export function RecentActivity() {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
                <ScrollArea className="h-[400px] pr-4">
                    <div className="space-y-4">
                        {mockActivities.map((activity) => {
                            const Icon = activityIcons[activity.type];
                            const colorClass = activityColors[activity.type];

                            return (
                                <div key={activity.id} className="flex items-start gap-4">
                                    <div
                                        className={cn(
                                            "mt-1 rounded-full p-2 bg-muted",
                                            colorClass
                                        )}
                                    >
                                        <Icon className="h-4 w-4" />
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <p className="text-sm font-medium leading-none">
                                            {activity.title}
                                        </p>
                                        <p className="text-sm text-muted-foreground">
                                            {activity.description}
                                        </p>
                                        <p className="text-xs text-muted-foreground">
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
