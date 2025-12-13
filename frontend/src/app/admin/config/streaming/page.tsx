"use client"

import { useState, useEffect, useCallback } from "react"
import { Radio, Activity, Layers, Clock, RefreshCw } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { configApi, type StreamingConfig } from "@/lib/api/admin"

const defaultConfig: StreamingConfig = {
    max_concurrent_streams_per_account: 1,
    max_stream_duration_hours: 12,
    health_check_interval_seconds: 10,
    reconnect_max_attempts: 5,
    reconnect_initial_delay_seconds: 2,
    reconnect_max_delay_seconds: 30,
    default_latency_mode: "normal",
    enable_dvr_by_default: true,
    simulcast_max_platforms: 5,
    playlist_max_videos: 100,
    stream_start_tolerance_seconds: 30,
}

const latencyModeOptions = [
    { value: "normal", label: "Normal", description: "Standard latency (~15-30 seconds)" },
    { value: "low", label: "Low", description: "Reduced latency (~5-10 seconds)" },
    { value: "ultra-low", label: "Ultra Low", description: "Minimal latency (~2-5 seconds)" },
]

export default function StreamingConfigPage() {
    const [config, setConfig] = useState<StreamingConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<StreamingConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getStreamingConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch streaming config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])


    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateStreamingConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof StreamingConfig>(key: K, value: StreamingConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    return (
        <ConfigFormWrapper
            title="Streaming Configuration"
            description="Configure stream limits, health monitoring, and simulcast settings."
            icon={<Radio className="h-5 w-5 text-red-600 dark:text-red-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Stream Limits */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Stream Limits</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_concurrent_streams_per_account">
                                    Max Concurrent Streams per Account
                                </Label>
                                <Input
                                    id="max_concurrent_streams_per_account"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.max_concurrent_streams_per_account}
                                    onChange={(e) =>
                                        updateConfig("max_concurrent_streams_per_account", parseInt(e.target.value) || 1)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-10 streams per account</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_stream_duration_hours">
                                    Max Stream Duration (hours)
                                </Label>
                                <Input
                                    id="max_stream_duration_hours"
                                    type="number"
                                    min={1}
                                    max={48}
                                    value={config.max_stream_duration_hours}
                                    onChange={(e) =>
                                        updateConfig("max_stream_duration_hours", parseInt(e.target.value) || 12)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-48 hours maximum</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="default_latency_mode">Default Latency Mode</Label>
                                <Select
                                    value={config.default_latency_mode}
                                    onValueChange={(value) => updateConfig("default_latency_mode", value)}
                                >
                                    <SelectTrigger id="default_latency_mode">
                                        <SelectValue placeholder="Select latency mode" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {latencyModeOptions.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                <div className="flex flex-col">
                                                    <span>{option.label}</span>
                                                    <span className="text-xs text-slate-500">{option.description}</span>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-slate-500">Default latency for new streams</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="stream_start_tolerance_seconds">
                                    Stream Start Tolerance (seconds)
                                </Label>
                                <Input
                                    id="stream_start_tolerance_seconds"
                                    type="number"
                                    min={5}
                                    max={120}
                                    value={config.stream_start_tolerance_seconds}
                                    onChange={(e) =>
                                        updateConfig("stream_start_tolerance_seconds", parseInt(e.target.value) || 30)
                                    }
                                />
                                <p className="text-xs text-slate-500">5-120 seconds tolerance</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="enable_dvr_by_default">Enable DVR by Default</Label>
                                <p className="text-xs text-slate-500">
                                    Allow viewers to rewind and pause live streams
                                </p>
                            </div>
                            <Switch
                                id="enable_dvr_by_default"
                                checked={config.enable_dvr_by_default}
                                onCheckedChange={(checked) =>
                                    updateConfig("enable_dvr_by_default", checked)
                                }
                            />
                        </div>
                    </div>
                </div>

                <Separator />


                {/* Health Monitoring */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Activity className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Health Monitoring</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="health_check_interval_seconds">
                                    Health Check Interval (seconds)
                                </Label>
                                <Input
                                    id="health_check_interval_seconds"
                                    type="number"
                                    min={5}
                                    max={60}
                                    value={config.health_check_interval_seconds}
                                    onChange={(e) =>
                                        updateConfig("health_check_interval_seconds", parseInt(e.target.value) || 10)
                                    }
                                />
                                <p className="text-xs text-slate-500">5-60 seconds between checks</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="reconnect_max_attempts">
                                    Max Reconnection Attempts
                                </Label>
                                <Input
                                    id="reconnect_max_attempts"
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={config.reconnect_max_attempts}
                                    onChange={(e) =>
                                        updateConfig("reconnect_max_attempts", parseInt(e.target.value) || 5)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-20 attempts before giving up</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="reconnect_initial_delay_seconds">
                                    Initial Reconnect Delay (seconds)
                                </Label>
                                <Input
                                    id="reconnect_initial_delay_seconds"
                                    type="number"
                                    min={1}
                                    max={30}
                                    value={config.reconnect_initial_delay_seconds}
                                    onChange={(e) =>
                                        updateConfig("reconnect_initial_delay_seconds", parseInt(e.target.value) || 2)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-30 seconds initial delay</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="reconnect_max_delay_seconds">
                                    Max Reconnect Delay (seconds)
                                </Label>
                                <Input
                                    id="reconnect_max_delay_seconds"
                                    type="number"
                                    min={5}
                                    max={300}
                                    value={config.reconnect_max_delay_seconds}
                                    onChange={(e) =>
                                        updateConfig("reconnect_max_delay_seconds", parseInt(e.target.value) || 30)
                                    }
                                />
                                <p className="text-xs text-slate-500">5-300 seconds maximum delay</p>
                            </div>
                        </div>

                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/50">
                            <div className="flex items-start gap-2">
                                <RefreshCw className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                                        Exponential Backoff
                                    </p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                        Reconnection delay increases exponentially from initial delay up to max delay.
                                        This helps prevent overwhelming the server during outages.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Simulcast Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Layers className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Simulcast Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="simulcast_max_platforms">
                                    Max Simulcast Platforms
                                </Label>
                                <Input
                                    id="simulcast_max_platforms"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.simulcast_max_platforms}
                                    onChange={(e) =>
                                        updateConfig("simulcast_max_platforms", parseInt(e.target.value) || 5)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    1-10 platforms for simultaneous streaming
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="playlist_max_videos">
                                    Max Videos per Playlist Stream
                                </Label>
                                <Input
                                    id="playlist_max_videos"
                                    type="number"
                                    min={10}
                                    max={500}
                                    value={config.playlist_max_videos}
                                    onChange={(e) =>
                                        updateConfig("playlist_max_videos", parseInt(e.target.value) || 100)
                                    }
                                />
                                <p className="text-xs text-slate-500">
                                    10-500 videos per playlist stream
                                </p>
                            </div>
                        </div>

                        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                            <div className="flex items-start gap-2">
                                <Layers className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                        Simulcast Bandwidth
                                    </p>
                                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                                        Each additional simulcast platform increases bandwidth usage.
                                        Consider plan limits when setting max platforms.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
