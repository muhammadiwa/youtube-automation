"use client"

import { useState, useEffect, useCallback } from "react"
import { Shield, Filter, Clock, AlertTriangle, MessageSquare } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Slider } from "@/components/ui/slider"
import { configApi, type ModerationConfig } from "@/lib/api/admin"

const defaultConfig: ModerationConfig = {
    moderation_analysis_timeout_seconds: 2,
    auto_slow_mode_threshold: 50,
    slow_mode_duration_seconds: 30,
    default_timeout_duration_seconds: 300,
    max_warnings_before_ban: 3,
    spam_detection_enabled: true,
    profanity_filter_enabled: true,
    link_filter_enabled: true,
    caps_filter_threshold_percent: 70,
}

export default function ModerationConfigPage() {
    const [config, setConfig] = useState<ModerationConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<ModerationConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getModerationConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch moderation config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateModerationConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof ModerationConfig>(key: K, value: ModerationConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }


    // Helper to format seconds to human readable
    const formatDuration = (seconds: number): string => {
        if (seconds < 60) return `${seconds} seconds`
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`
        return `${Math.floor(seconds / 3600)} hours`
    }

    return (
        <ConfigFormWrapper
            title="Moderation Configuration"
            description="Configure chat and comment moderation settings, filters, and penalty rules."
            icon={<Shield className="h-5 w-5 text-orange-600 dark:text-orange-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Filter Toggles */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Filter className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Content Filters</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="spam_detection_enabled">Spam Detection</Label>
                                <p className="text-xs text-slate-500">
                                    Automatically detect and filter spam messages
                                </p>
                            </div>
                            <Switch
                                id="spam_detection_enabled"
                                checked={config.spam_detection_enabled}
                                onCheckedChange={(checked) =>
                                    updateConfig("spam_detection_enabled", checked)
                                }
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="profanity_filter_enabled">Profanity Filter</Label>
                                <p className="text-xs text-slate-500">
                                    Filter messages containing profanity or offensive language
                                </p>
                            </div>
                            <Switch
                                id="profanity_filter_enabled"
                                checked={config.profanity_filter_enabled}
                                onCheckedChange={(checked) =>
                                    updateConfig("profanity_filter_enabled", checked)
                                }
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="link_filter_enabled">Link Filter</Label>
                                <p className="text-xs text-slate-500">
                                    Block or moderate messages containing external links
                                </p>
                            </div>
                            <Switch
                                id="link_filter_enabled"
                                checked={config.link_filter_enabled}
                                onCheckedChange={(checked) =>
                                    updateConfig("link_filter_enabled", checked)
                                }
                            />
                        </div>

                        <div className="space-y-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label htmlFor="caps_filter_threshold_percent">Caps Filter Threshold</Label>
                                    <p className="text-xs text-slate-500">
                                        Filter messages with excessive capital letters
                                    </p>
                                </div>
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                    {config.caps_filter_threshold_percent}%
                                </span>
                            </div>
                            <Slider
                                id="caps_filter_threshold_percent"
                                min={50}
                                max={100}
                                step={5}
                                value={[config.caps_filter_threshold_percent]}
                                onValueChange={([value]) =>
                                    updateConfig("caps_filter_threshold_percent", value)
                                }
                                className="w-full"
                            />
                            <p className="text-xs text-slate-400">
                                Messages with more than {config.caps_filter_threshold_percent}% capital letters will be filtered
                            </p>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Penalty Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Penalty Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="default_timeout_duration_seconds">
                                    Default Timeout Duration
                                </Label>
                                <Input
                                    id="default_timeout_duration_seconds"
                                    type="number"
                                    min={60}
                                    max={86400}
                                    value={config.default_timeout_duration_seconds}
                                    onChange={(e) =>
                                        updateConfig("default_timeout_duration_seconds", parseInt(e.target.value) || 300)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    {formatDuration(config.default_timeout_duration_seconds)} (60-86400 seconds)
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_warnings_before_ban">
                                    Warnings Before Ban
                                </Label>
                                <Input
                                    id="max_warnings_before_ban"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.max_warnings_before_ban}
                                    onChange={(e) =>
                                        updateConfig("max_warnings_before_ban", parseInt(e.target.value) || 3)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    1-10 warnings before automatic ban
                                </p>
                            </div>
                        </div>

                        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                            <div className="flex items-start gap-2">
                                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                        Automatic Ban Policy
                                    </p>
                                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                                        Users will be automatically banned after receiving {config.max_warnings_before_ban} warnings.
                                        Each warning is logged and can be reviewed in the moderation queue.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Slow Mode Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Slow Mode Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="auto_slow_mode_threshold">
                                    Auto Slow Mode Threshold
                                </Label>
                                <Input
                                    id="auto_slow_mode_threshold"
                                    type="number"
                                    min={10}
                                    max={500}
                                    value={config.auto_slow_mode_threshold}
                                    onChange={(e) =>
                                        updateConfig("auto_slow_mode_threshold", parseInt(e.target.value) || 50)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    Messages per minute to trigger slow mode (10-500)
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="slow_mode_duration_seconds">
                                    Slow Mode Duration
                                </Label>
                                <Input
                                    id="slow_mode_duration_seconds"
                                    type="number"
                                    min={5}
                                    max={300}
                                    value={config.slow_mode_duration_seconds}
                                    onChange={(e) =>
                                        updateConfig("slow_mode_duration_seconds", parseInt(e.target.value) || 30)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    {formatDuration(config.slow_mode_duration_seconds)} between messages (5-300 seconds)
                                </p>
                            </div>
                        </div>

                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/50">
                            <div className="flex items-start gap-2">
                                <Clock className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                                        Slow Mode Behavior
                                    </p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                        When chat activity exceeds {config.auto_slow_mode_threshold} messages per minute,
                                        slow mode will automatically activate, requiring users to wait {config.slow_mode_duration_seconds} seconds
                                        between messages.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Analysis Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Analysis Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="moderation_analysis_timeout_seconds">
                                Moderation Analysis Timeout
                            </Label>
                            <Input
                                id="moderation_analysis_timeout_seconds"
                                type="number"
                                min={1}
                                max={10}
                                value={config.moderation_analysis_timeout_seconds}
                                onChange={(e) =>
                                    updateConfig("moderation_analysis_timeout_seconds", parseInt(e.target.value) || 2)
                                }
                                className="max-w-[200px]"
                            />
                            <p className="text-xs text-slate-500">
                                Maximum time to analyze a message before allowing it through (1-10 seconds)
                            </p>
                        </div>

                        <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                If moderation analysis takes longer than {config.moderation_analysis_timeout_seconds} seconds,
                                the message will be allowed through to prevent delays in chat.
                                Consider increasing this value if you need stricter moderation.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
