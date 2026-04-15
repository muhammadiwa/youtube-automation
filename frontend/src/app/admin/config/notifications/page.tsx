"use client"

import { useState, useEffect, useCallback } from "react"
import { Bell, Mail, MessageSquare, Send, Clock, Archive, AlertTriangle } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Checkbox } from "@/components/ui/checkbox"
import { configApi, type NotificationConfig } from "@/lib/api/admin"

const defaultConfig: NotificationConfig = {
    email_enabled: true,
    sms_enabled: false,
    slack_enabled: true,
    telegram_enabled: true,
    whatsapp_enabled: false,
    notification_batch_interval_seconds: 60,
    max_notifications_per_batch: 10,
    critical_alert_channels: ["email", "slack"],
    notification_retention_days: 90,
}

const AVAILABLE_CHANNELS = [
    { id: "email", label: "Email", icon: Mail },
    { id: "sms", label: "SMS", icon: MessageSquare },
    { id: "slack", label: "Slack", icon: MessageSquare },
    { id: "telegram", label: "Telegram", icon: Send },
    { id: "whatsapp", label: "WhatsApp", icon: MessageSquare },
]

export default function NotificationConfigPage() {
    const [config, setConfig] = useState<NotificationConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<NotificationConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getNotificationConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch notification config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])


    const handleSave = async () => {
        await configApi.updateNotificationConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof NotificationConfig>(key: K, value: NotificationConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    // Check if a channel is enabled
    const isChannelEnabled = (channelId: string): boolean => {
        const channelKey = `${channelId}_enabled` as keyof NotificationConfig
        return config[channelKey] as boolean
    }

    // Toggle critical alert channel
    const toggleCriticalChannel = (channelId: string, checked: boolean) => {
        const currentChannels = config.critical_alert_channels || []
        if (checked) {
            updateConfig("critical_alert_channels", [...currentChannels, channelId])
        } else {
            updateConfig("critical_alert_channels", currentChannels.filter((c) => c !== channelId))
        }
    }

    // Helper to format seconds to human readable
    const formatDuration = (seconds: number): string => {
        if (seconds < 60) return `${seconds} seconds`
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`
        return `${Math.floor(seconds / 3600)} hours`
    }

    return (
        <ConfigFormWrapper
            title="Notification Configuration"
            description="Configure notification channels, batching behavior, and retention settings."
            icon={<Bell className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Channel Toggles */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Mail className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Notification Channels</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">
                        Enable or disable notification channels. Disabled channels will not send any notifications.
                    </p>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <Mail className="h-5 w-5 text-blue-500" />
                                <div>
                                    <Label htmlFor="email_enabled">Email</Label>
                                    <p className="text-xs text-slate-500">
                                        Send notifications via email
                                    </p>
                                </div>
                            </div>
                            <Switch
                                id="email_enabled"
                                checked={config.email_enabled}
                                onCheckedChange={(checked) => updateConfig("email_enabled", checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <MessageSquare className="h-5 w-5 text-green-500" />
                                <div>
                                    <Label htmlFor="sms_enabled">SMS</Label>
                                    <p className="text-xs text-slate-500">
                                        Send notifications via SMS text messages
                                    </p>
                                </div>
                            </div>
                            <Switch
                                id="sms_enabled"
                                checked={config.sms_enabled}
                                onCheckedChange={(checked) => updateConfig("sms_enabled", checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <svg className="h-5 w-5 text-purple-500" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
                                </svg>
                                <div>
                                    <Label htmlFor="slack_enabled">Slack</Label>
                                    <p className="text-xs text-slate-500">
                                        Send notifications to Slack channels
                                    </p>
                                </div>
                            </div>
                            <Switch
                                id="slack_enabled"
                                checked={config.slack_enabled}
                                onCheckedChange={(checked) => updateConfig("slack_enabled", checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <Send className="h-5 w-5 text-sky-500" />
                                <div>
                                    <Label htmlFor="telegram_enabled">Telegram</Label>
                                    <p className="text-xs text-slate-500">
                                        Send notifications via Telegram bot
                                    </p>
                                </div>
                            </div>
                            <Switch
                                id="telegram_enabled"
                                checked={config.telegram_enabled}
                                onCheckedChange={(checked) => updateConfig("telegram_enabled", checked)}
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <svg className="h-5 w-5 text-green-600" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                                </svg>
                                <div>
                                    <Label htmlFor="whatsapp_enabled">WhatsApp</Label>
                                    <p className="text-xs text-slate-500">
                                        Send notifications via WhatsApp Business API
                                    </p>
                                </div>
                            </div>
                            <Switch
                                id="whatsapp_enabled"
                                checked={config.whatsapp_enabled}
                                onCheckedChange={(checked) => updateConfig("whatsapp_enabled", checked)}
                            />
                        </div>
                    </div>
                </div>

                <Separator />


                {/* Batching Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Batching Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">
                        Configure how notifications are batched together to reduce notification fatigue.
                    </p>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="notification_batch_interval_seconds">
                                    Batch Interval
                                </Label>
                                <Input
                                    id="notification_batch_interval_seconds"
                                    type="number"
                                    min={10}
                                    max={3600}
                                    value={config.notification_batch_interval_seconds}
                                    onChange={(e) =>
                                        updateConfig("notification_batch_interval_seconds", parseInt(e.target.value) || 60)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    {formatDuration(config.notification_batch_interval_seconds)} (10-3600 seconds)
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_notifications_per_batch">
                                    Max Notifications Per Batch
                                </Label>
                                <Input
                                    id="max_notifications_per_batch"
                                    type="number"
                                    min={1}
                                    max={100}
                                    value={config.max_notifications_per_batch}
                                    onChange={(e) =>
                                        updateConfig("max_notifications_per_batch", parseInt(e.target.value) || 10)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    1-100 notifications per batch
                                </p>
                            </div>
                        </div>

                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/50">
                            <div className="flex items-start gap-2">
                                <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                                        Batching Behavior
                                    </p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                        Notifications will be collected for up to {formatDuration(config.notification_batch_interval_seconds)} before being sent.
                                        A maximum of {config.max_notifications_per_batch} notifications will be included in each batch.
                                        Critical alerts bypass batching and are sent immediately.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Critical Alert Channels */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Critical Alert Channels</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">
                        Select which channels should receive critical alerts. Critical alerts bypass batching and are sent immediately.
                    </p>
                    <div className="space-y-3">
                        {AVAILABLE_CHANNELS.map((channel) => {
                            const isEnabled = isChannelEnabled(channel.id)
                            const isSelected = config.critical_alert_channels?.includes(channel.id) || false
                            return (
                                <div
                                    key={channel.id}
                                    className={`flex items-center space-x-3 p-3 rounded-lg ${isEnabled
                                            ? "bg-slate-50 dark:bg-slate-800/50"
                                            : "bg-slate-100 dark:bg-slate-800/30 opacity-60"
                                        }`}
                                >
                                    <Checkbox
                                        id={`critical_${channel.id}`}
                                        checked={isSelected}
                                        onCheckedChange={(checked) =>
                                            toggleCriticalChannel(channel.id, checked as boolean)
                                        }
                                        disabled={!isEnabled}
                                    />
                                    <div className="flex items-center gap-2">
                                        <channel.icon className="h-4 w-4 text-slate-500" />
                                        <Label
                                            htmlFor={`critical_${channel.id}`}
                                            className={!isEnabled ? "text-slate-400" : ""}
                                        >
                                            {channel.label}
                                            {!isEnabled && (
                                                <span className="ml-2 text-xs text-slate-400">(disabled)</span>
                                            )}
                                        </Label>
                                    </div>
                                </div>
                            )
                        })}
                    </div>

                    <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                        <div className="flex items-start gap-2">
                            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                    Critical Alerts
                                </p>
                                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                                    Critical alerts include system errors, security incidents, payment failures, and other urgent notifications.
                                    It&apos;s recommended to have at least one channel enabled for critical alerts.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Retention Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Archive className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Retention Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">
                        Configure how long notification history is retained in the system.
                    </p>
                    <div className="space-y-4">
                        <div className="space-y-2 max-w-md">
                            <Label htmlFor="notification_retention_days">
                                Notification Retention Period
                            </Label>
                            <Input
                                id="notification_retention_days"
                                type="number"
                                min={7}
                                max={365}
                                value={config.notification_retention_days}
                                onChange={(e) =>
                                    updateConfig("notification_retention_days", parseInt(e.target.value) || 90)
                                }
                            />
                            <p className="text-xs text-slate-500">
                                {config.notification_retention_days} days (7-365 days)
                            </p>
                        </div>

                        <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                Notification history older than {config.notification_retention_days} days will be automatically deleted.
                                This helps manage storage and comply with data retention policies.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
