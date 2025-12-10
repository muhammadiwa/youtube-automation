"use client"

import { useState, useEffect } from "react"
import { Bell, Mail, Send, Loader2, Check, Settings, TestTube } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { apiClient } from "@/lib/api/client"

type NotificationType =
    | "stream_started"
    | "stream_ended"
    | "stream_error"
    | "upload_complete"
    | "upload_failed"
    | "quota_warning"
    | "token_expiring"
    | "strike_detected"
    | "revenue_alert"
    | "competitor_update"
    | "system_alert"
    | "comment_received"
    | "subscriber_milestone"

interface NotificationPreference {
    id: string
    user_id: string
    event_type: NotificationType
    email_enabled: boolean
    telegram_enabled: boolean
}

interface NotificationChannelData {
    type: "email" | "telegram"
    enabled: boolean
    config?: Record<string, string>
}

interface ChannelState {
    type: "email" | "telegram"
    label: string
    description: string
    enabled: boolean
    config?: Record<string, string>
}

const EVENT_TYPES: { type: NotificationType; label: string; description: string }[] = [
    { type: "stream_started", label: "Stream Started", description: "When a live stream begins" },
    { type: "stream_ended", label: "Stream Ended", description: "When a live stream ends" },
    { type: "stream_error", label: "Stream Error", description: "When a stream encounters an error" },
    { type: "upload_complete", label: "Upload Complete", description: "When a video upload finishes" },
    { type: "upload_failed", label: "Upload Failed", description: "When a video upload fails" },
    { type: "quota_warning", label: "Quota Warning", description: "When API quota is running low" },
    { type: "token_expiring", label: "Token Expiring", description: "When OAuth token is about to expire" },
    { type: "strike_detected", label: "Strike Detected", description: "When a strike is detected on your channel" },
    { type: "revenue_alert", label: "Revenue Alert", description: "Significant changes in revenue" },
    { type: "competitor_update", label: "Competitor Update", description: "When competitors publish new content" },
    { type: "comment_received", label: "Comment Received", description: "When new comments need attention" },
    { type: "subscriber_milestone", label: "Subscriber Milestone", description: "When you reach subscriber milestones" },
]

const DEFAULT_PREFERENCES: NotificationPreference[] = EVENT_TYPES.map((event, index) => ({
    id: `pref-${index}`,
    user_id: "",
    event_type: event.type,
    email_enabled: true,
    telegram_enabled: false,
}))

export default function NotificationSettingsPage() {
    const [channels, setChannels] = useState<ChannelState[]>([
        { type: "email", label: "Email", description: "Receive notifications via email", enabled: true },
        { type: "telegram", label: "Telegram", description: "Receive notifications via Telegram", enabled: false },
    ])
    const [preferences, setPreferences] = useState<NotificationPreference[]>(DEFAULT_PREFERENCES)
    const [loading, setLoading] = useState(true)
    const [configDialogOpen, setConfigDialogOpen] = useState(false)
    const [selectedChannel, setSelectedChannel] = useState<ChannelState | null>(null)
    const [saving, setSaving] = useState(false)
    const [testing, setTesting] = useState<string | null>(null)
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
    const [telegramBotToken, setTelegramBotToken] = useState("")
    const [telegramChatId, setTelegramChatId] = useState("")

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            setLoading(true)
            // Get user_id from localStorage or use "current"
            const userId = localStorage.getItem("user_id") || "current"

            // Load preferences from backend - endpoint: GET /notifications/preferences/{user_id}
            try {
                const prefsData = await apiClient.get<NotificationPreference[]>(`/notifications/preferences/${userId}`)
                if (prefsData && prefsData.length > 0) {
                    setPreferences(prefsData)
                    // Derive channel states from preferences
                    const hasEmailEnabled = prefsData.some(p => p.email_enabled)
                    const hasTelegramEnabled = prefsData.some(p => p.telegram_enabled)
                    setChannels([
                        { type: "email", label: "Email", description: "Receive notifications via email", enabled: hasEmailEnabled },
                        { type: "telegram", label: "Telegram", description: "Receive notifications via Telegram", enabled: hasTelegramEnabled },
                    ])
                }
            } catch {
                // Use default preferences if API fails
            }
        } catch (error) {
            console.error("Failed to load notification settings:", error)
        } finally {
            setLoading(false)
        }
    }

    const openConfigDialog = (channel: ChannelState) => {
        setSelectedChannel(channel)
        setTestResult(null)
        setConfigDialogOpen(true)
    }

    const handleSaveConfig = async () => {
        if (!selectedChannel) return
        try {
            setSaving(true)
            // Store telegram config in localStorage for now (backend can be extended to support this)
            if (selectedChannel.type === "telegram") {
                localStorage.setItem("telegram_bot_token", telegramBotToken)
                localStorage.setItem("telegram_chat_id", telegramChatId)
            }
            setChannels(prev => prev.map(c => c.type === selectedChannel.type ? { ...c, enabled: true, config: selectedChannel.type === "telegram" ? { bot_token: telegramBotToken, chat_id: telegramChatId } : undefined } : c))
            setConfigDialogOpen(false)
        } catch (error) {
            console.error("Failed to save channel config:", error)
        } finally {
            setSaving(false)
        }
    }

    const handleTestChannel = async (channelType: "email" | "telegram") => {
        try {
            setTesting(channelType)
            setTestResult(null)
            // Send test notification using the notification send endpoint
            const userId = localStorage.getItem("user_id") || "current"
            await apiClient.post("/notifications/send", {
                user_id: userId,
                channel: channelType,
                title: "Test Notification",
                message: `This is a test notification for ${channelType}`,
                priority: "low"
            })
            setTestResult({ success: true, message: "Test notification sent!" })
        } catch {
            setTestResult({ success: false, message: "Failed to send test notification" })
        } finally {
            setTesting(null)
        }
    }

    const handleToggleChannel = async (channelType: "email" | "telegram", enabled: boolean) => {
        try {
            if (enabled && channelType === "telegram") {
                const channel = channels.find(c => c.type === channelType)
                if (channel && !channel.config?.bot_token) {
                    // Load saved config from localStorage
                    const savedToken = localStorage.getItem("telegram_bot_token")
                    const savedChatId = localStorage.getItem("telegram_chat_id")
                    if (savedToken && savedChatId) {
                        setTelegramBotToken(savedToken)
                        setTelegramChatId(savedChatId)
                    } else {
                        openConfigDialog(channel)
                        return
                    }
                }
            }
            // Update local state - channel preferences are managed through individual event preferences
            setChannels(prev => prev.map(c => c.type === channelType ? { ...c, enabled } : c))
        } catch (error) {
            console.error("Failed to toggle channel:", error)
        }
    }

    const handleTogglePreference = async (eventType: NotificationType, field: "email_enabled" | "telegram_enabled", value: boolean) => {
        try {
            // Find the preference to get its ID
            const pref = preferences.find(p => p.event_type === eventType)
            if (pref && pref.id && !pref.id.startsWith("pref-")) {
                // Use PUT /notifications/preferences/{preference_id} for existing preferences
                await apiClient.put(`/notifications/preferences/${pref.id}`, {
                    event_type: eventType,
                    [field]: value
                })
            } else {
                // Create new preference if it doesn't exist
                const userId = localStorage.getItem("user_id") || "current"
                await apiClient.post(`/notifications/preferences?user_id=${userId}`, {
                    event_type: eventType,
                    email_enabled: field === "email_enabled" ? value : false,
                    telegram_enabled: field === "telegram_enabled" ? value : false,
                })
            }
            setPreferences(prev => prev.map(p => p.event_type === eventType ? { ...p, [field]: value } : p))
        } catch (error) {
            console.error("Failed to update preference:", error)
        }
    }

    const isChannelEnabled = (type: string) => channels.find(c => c.type === type)?.enabled || false

    if (loading) {
        return (
            <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings", href: "/dashboard/settings" }, { label: "Notifications" }]}>
                <div className="space-y-6">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Bell className="h-8 w-8" />
                            Notification Settings
                        </h1>
                        <p className="text-muted-foreground">Configure how and when you receive notifications</p>
                    </div>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="p-6">
                            <div className="space-y-4">
                                {[1, 2].map((i) => (
                                    <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
                                        <Skeleton className="h-12 w-12 rounded-lg" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-24 mb-2" />
                                            <Skeleton className="h-3 w-48" />
                                        </div>
                                        <Skeleton className="h-6 w-12" />
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings", href: "/dashboard/settings" }, { label: "Notifications" }]}>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <Bell className="h-8 w-8" />
                        Notification Settings
                    </h1>
                    <p className="text-muted-foreground">Configure how and when you receive notifications</p>
                </div>

                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Notification Channels</CardTitle>
                        <CardDescription>Enable and configure the channels through which you want to receive notifications</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {channels.map((channel) => (
                            <div key={channel.type} className="flex items-center justify-between p-4 border rounded-lg">
                                <div className="flex items-center gap-4">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                        {channel.type === "email" ? <Mail className="h-6 w-6 text-primary" /> : <Send className="h-6 w-6 text-primary" />}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium">{channel.label}</p>
                                            {channel.enabled && <Badge variant="default" className="bg-green-500 text-xs">Active</Badge>}
                                        </div>
                                        <p className="text-sm text-muted-foreground">{channel.description}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {channel.enabled && channel.type === "telegram" && (
                                        <Button variant="ghost" size="icon" onClick={() => openConfigDialog(channel)}><Settings className="h-4 w-4" /></Button>
                                    )}
                                    {channel.enabled && (
                                        <Button variant="ghost" size="icon" onClick={() => handleTestChannel(channel.type)} disabled={testing === channel.type}>
                                            {testing === channel.type ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                                        </Button>
                                    )}
                                    <Switch checked={channel.enabled} onCheckedChange={(checked) => handleToggleChannel(channel.type, checked)} />
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Event Preferences</CardTitle>
                        <CardDescription>Choose which events trigger notifications on each channel</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="grid grid-cols-[1fr,100px,100px] gap-4 pb-3 border-b">
                                <div className="font-medium">Event</div>
                                <div className="font-medium text-center flex items-center justify-center gap-2"><Mail className="h-4 w-4" /><span>Email</span></div>
                                <div className="font-medium text-center flex items-center justify-center gap-2"><Send className="h-4 w-4" /><span>Telegram</span></div>
                            </div>
                            {EVENT_TYPES.map((event) => {
                                const pref = preferences.find((p) => p.event_type === event.type)
                                return (
                                    <div key={event.type} className="grid grid-cols-[1fr,100px,100px] gap-4 py-3 border-b last:border-0 hover:bg-muted/50 rounded">
                                        <div>
                                            <p className="font-medium">{event.label}</p>
                                            <p className="text-sm text-muted-foreground">{event.description}</p>
                                        </div>
                                        <div className="flex justify-center items-center">
                                            <Switch checked={pref?.email_enabled || false} onCheckedChange={(checked) => handleTogglePreference(event.type, "email_enabled", checked)} disabled={!isChannelEnabled("email")} />
                                        </div>
                                        <div className="flex justify-center items-center">
                                            <Switch checked={pref?.telegram_enabled || false} onCheckedChange={(checked) => handleTogglePreference(event.type, "telegram_enabled", checked)} disabled={!isChannelEnabled("telegram")} />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>Configure Telegram</DialogTitle>
                        <DialogDescription>Enter your Telegram bot credentials to receive notifications</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="botToken">Bot Token</Label>
                            <Input id="botToken" value={telegramBotToken} onChange={(e) => setTelegramBotToken(e.target.value)} placeholder="123456:ABC-DEF..." />
                            <p className="text-xs text-muted-foreground">Get this from @BotFather on Telegram</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="chatId">Chat ID</Label>
                            <Input id="chatId" value={telegramChatId} onChange={(e) => setTelegramChatId(e.target.value)} placeholder="123456789" />
                            <p className="text-xs text-muted-foreground">Your Telegram user ID or group chat ID</p>
                        </div>
                        {testResult && (
                            <Alert variant={testResult.success ? "default" : "destructive"}>
                                {testResult.success && <Check className="h-4 w-4" />}
                                <AlertDescription>{testResult.success ? "Test notification sent successfully!" : testResult.message}</AlertDescription>
                            </Alert>
                        )}
                    </div>
                    <DialogFooter className="flex-col sm:flex-row gap-2">
                        <Button variant="outline" onClick={() => handleTestChannel("telegram")} disabled={testing !== null || !telegramBotToken || !telegramChatId}>
                            {testing === "telegram" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <TestTube className="mr-2 h-4 w-4" />}Test
                        </Button>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
                            <Button onClick={handleSaveConfig} disabled={saving || !telegramBotToken || !telegramChatId}>
                                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save
                            </Button>
                        </div>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
