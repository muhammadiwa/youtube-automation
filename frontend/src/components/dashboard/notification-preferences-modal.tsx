"use client";

import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface NotificationPreference {
    id: string;
    label: string;
    description: string;
    channels: {
        email: boolean;
        sms: boolean;
        slack: boolean;
        telegram: boolean;
    };
}

const defaultPreferences: NotificationPreference[] = [
    {
        id: "stream_started",
        label: "Stream Started",
        description: "When a scheduled stream starts",
        channels: { email: true, sms: false, slack: true, telegram: false },
    },
    {
        id: "stream_ended",
        label: "Stream Ended",
        description: "When a stream ends",
        channels: { email: false, sms: false, slack: true, telegram: false },
    },
    {
        id: "upload_complete",
        label: "Upload Complete",
        description: "When a video upload finishes",
        channels: { email: true, sms: false, slack: false, telegram: false },
    },
    {
        id: "quota_warning",
        label: "Quota Warning",
        description: "When API quota reaches 80%",
        channels: { email: true, sms: true, slack: true, telegram: false },
    },
    {
        id: "token_expiring",
        label: "Token Expiring",
        description: "When OAuth token is about to expire",
        channels: { email: true, sms: false, slack: true, telegram: false },
    },
    {
        id: "strike_detected",
        label: "Strike Detected",
        description: "When a channel receives a strike",
        channels: { email: true, sms: true, slack: true, telegram: true },
    },
    {
        id: "revenue_milestone",
        label: "Revenue Milestone",
        description: "When reaching revenue goals",
        channels: { email: true, sms: false, slack: false, telegram: false },
    },
    {
        id: "subscriber_milestone",
        label: "Subscriber Milestone",
        description: "When reaching subscriber milestones",
        channels: { email: true, sms: false, slack: true, telegram: false },
    },
];

interface NotificationPreferencesModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function NotificationPreferencesModal({
    open,
    onOpenChange,
}: NotificationPreferencesModalProps) {
    const [preferences, setPreferences] =
        useState<NotificationPreference[]>(defaultPreferences);
    const [isSaving, setIsSaving] = useState(false);

    const toggleChannel = (
        preferenceId: string,
        channel: keyof NotificationPreference["channels"]
    ) => {
        setPreferences((prev) =>
            prev.map((pref) =>
                pref.id === preferenceId
                    ? {
                        ...pref,
                        channels: {
                            ...pref.channels,
                            [channel]: !pref.channels[channel],
                        },
                    }
                    : pref
            )
        );
    };

    const handleSave = async () => {
        setIsSaving(true);
        // TODO: Save preferences to API
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setIsSaving(false);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[80vh]">
                <DialogHeader>
                    <DialogTitle>Notification Preferences</DialogTitle>
                    <DialogDescription>
                        Choose how you want to be notified for different events
                    </DialogDescription>
                </DialogHeader>

                <ScrollArea className="h-[500px] pr-4">
                    <div className="space-y-6">
                        {/* Channel Headers */}
                        <div className="grid grid-cols-[1fr,80px,80px,80px,80px] gap-4 items-center">
                            <div className="text-sm font-medium">Event Type</div>
                            <div className="text-sm font-medium text-center">Email</div>
                            <div className="text-sm font-medium text-center">SMS</div>
                            <div className="text-sm font-medium text-center">Slack</div>
                            <div className="text-sm font-medium text-center">Telegram</div>
                        </div>

                        <Separator />

                        {/* Preferences */}
                        {preferences.map((preference) => (
                            <div key={preference.id}>
                                <div className="grid grid-cols-[1fr,80px,80px,80px,80px] gap-4 items-center">
                                    <div>
                                        <Label className="text-sm font-medium">
                                            {preference.label}
                                        </Label>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {preference.description}
                                        </p>
                                    </div>
                                    <div className="flex justify-center">
                                        <Switch
                                            checked={preference.channels.email}
                                            onCheckedChange={() =>
                                                toggleChannel(preference.id, "email")
                                            }
                                        />
                                    </div>
                                    <div className="flex justify-center">
                                        <Switch
                                            checked={preference.channels.sms}
                                            onCheckedChange={() => toggleChannel(preference.id, "sms")}
                                        />
                                    </div>
                                    <div className="flex justify-center">
                                        <Switch
                                            checked={preference.channels.slack}
                                            onCheckedChange={() =>
                                                toggleChannel(preference.id, "slack")
                                            }
                                        />
                                    </div>
                                    <div className="flex justify-center">
                                        <Switch
                                            checked={preference.channels.telegram}
                                            onCheckedChange={() =>
                                                toggleChannel(preference.id, "telegram")
                                            }
                                        />
                                    </div>
                                </div>
                                <Separator className="mt-4" />
                            </div>
                        ))}
                    </div>
                </ScrollArea>

                <div className="flex justify-end gap-2 mt-4">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? "Saving..." : "Save Preferences"}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
