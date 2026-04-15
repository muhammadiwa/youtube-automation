"use client"

import { useState, useEffect, useCallback } from "react"
import { Upload, FileVideo, RefreshCw, HardDrive } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { configApi, type UploadConfig } from "@/lib/api/admin"

const defaultConfig: UploadConfig = {
    max_file_size_gb: 5.0,
    allowed_formats: ["mp4", "mov", "avi", "wmv", "webm", "mpeg"],
    max_concurrent_uploads: 3,
    upload_chunk_size_mb: 10,
    max_retry_attempts: 3,
    retry_delay_seconds: 5,
    auto_generate_thumbnail: true,
    default_visibility: "private",
    max_title_length: 100,
    max_description_length: 5000,
    max_tags_count: 500,
}

const availableFormats = ["mp4", "mov", "avi", "wmv", "webm", "mpeg", "mkv", "flv", "m4v", "3gp"]
const visibilityOptions = [
    { value: "private", label: "Private" },
    { value: "unlisted", label: "Unlisted" },
    { value: "public", label: "Public" },
]

export default function UploadConfigPage() {
    const [config, setConfig] = useState<UploadConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<UploadConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getUploadConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch upload config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateUploadConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof UploadConfig>(key: K, value: UploadConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    const toggleFormat = (format: string) => {
        const currentFormats = config.allowed_formats
        if (currentFormats.includes(format)) {
            updateConfig("allowed_formats", currentFormats.filter((f) => f !== format))
        } else {
            updateConfig("allowed_formats", [...currentFormats, format])
        }
    }

    return (
        <ConfigFormWrapper
            title="Upload Configuration"
            description="Configure file limits, upload behavior, and video defaults."
            icon={<Upload className="h-5 w-5 text-green-600 dark:text-green-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* File Limits */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <HardDrive className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">File Limits</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_file_size_gb">Max File Size (GB)</Label>
                                <Input
                                    id="max_file_size_gb"
                                    type="number"
                                    min={0.1}
                                    max={50}
                                    step={0.1}
                                    value={config.max_file_size_gb}
                                    onChange={(e) =>
                                        updateConfig("max_file_size_gb", parseFloat(e.target.value) || 5.0)
                                    }
                                />
                                <p className="text-xs text-slate-500">0.1-50 GB per file</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_concurrent_uploads">Max Concurrent Uploads</Label>
                                <Input
                                    id="max_concurrent_uploads"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.max_concurrent_uploads}
                                    onChange={(e) =>
                                        updateConfig("max_concurrent_uploads", parseInt(e.target.value) || 3)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-10 uploads per user</p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Allowed Video Formats</Label>
                            <div className="flex flex-wrap gap-2 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                {availableFormats.map((format) => {
                                    const isSelected = config.allowed_formats.includes(format)
                                    return (
                                        <Badge
                                            key={format}
                                            variant={isSelected ? "default" : "outline"}
                                            className={`cursor-pointer transition-colors ${isSelected
                                                    ? "bg-green-600 hover:bg-green-700"
                                                    : "hover:bg-slate-200 dark:hover:bg-slate-700"
                                                }`}
                                            onClick={() => toggleFormat(format)}
                                        >
                                            .{format}
                                        </Badge>
                                    )
                                })}
                            </div>
                            <p className="text-xs text-slate-500">
                                Click to toggle formats. Selected: {config.allowed_formats.length} formats
                            </p>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Upload Behavior */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <RefreshCw className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Upload Behavior</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="upload_chunk_size_mb">Chunk Size (MB)</Label>
                                <Input
                                    id="upload_chunk_size_mb"
                                    type="number"
                                    min={1}
                                    max={100}
                                    value={config.upload_chunk_size_mb}
                                    onChange={(e) =>
                                        updateConfig("upload_chunk_size_mb", parseInt(e.target.value) || 10)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-100 MB per chunk</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_retry_attempts">Max Retry Attempts</Label>
                                <Input
                                    id="max_retry_attempts"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.max_retry_attempts}
                                    onChange={(e) =>
                                        updateConfig("max_retry_attempts", parseInt(e.target.value) || 3)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-10 retries on failure</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="retry_delay_seconds">Retry Delay (seconds)</Label>
                                <Input
                                    id="retry_delay_seconds"
                                    type="number"
                                    min={1}
                                    max={60}
                                    value={config.retry_delay_seconds}
                                    onChange={(e) =>
                                        updateConfig("retry_delay_seconds", parseInt(e.target.value) || 5)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-60 seconds between retries</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="auto_generate_thumbnail">Auto-Generate Thumbnail</Label>
                                <p className="text-xs text-slate-500">
                                    Automatically generate thumbnail from video frame
                                </p>
                            </div>
                            <Switch
                                id="auto_generate_thumbnail"
                                checked={config.auto_generate_thumbnail}
                                onCheckedChange={(checked) =>
                                    updateConfig("auto_generate_thumbnail", checked)
                                }
                            />
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Video Defaults */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <FileVideo className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Video Defaults</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="default_visibility">Default Visibility</Label>
                                <Select
                                    value={config.default_visibility}
                                    onValueChange={(value) => updateConfig("default_visibility", value)}
                                >
                                    <SelectTrigger id="default_visibility">
                                        <SelectValue placeholder="Select visibility" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {visibilityOptions.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                {option.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-slate-500">Default visibility for new uploads</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_title_length">Max Title Length</Label>
                                <Input
                                    id="max_title_length"
                                    type="number"
                                    min={10}
                                    max={200}
                                    value={config.max_title_length}
                                    onChange={(e) =>
                                        updateConfig("max_title_length", parseInt(e.target.value) || 100)
                                    }
                                />
                                <p className="text-xs text-slate-500">10-200 characters</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_description_length">Max Description Length</Label>
                                <Input
                                    id="max_description_length"
                                    type="number"
                                    min={100}
                                    max={10000}
                                    value={config.max_description_length}
                                    onChange={(e) =>
                                        updateConfig("max_description_length", parseInt(e.target.value) || 5000)
                                    }
                                />
                                <p className="text-xs text-slate-500">100-10,000 characters</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="max_tags_count">Max Tags Count</Label>
                                <Input
                                    id="max_tags_count"
                                    type="number"
                                    min={10}
                                    max={1000}
                                    value={config.max_tags_count}
                                    onChange={(e) =>
                                        updateConfig("max_tags_count", parseInt(e.target.value) || 500)
                                    }
                                />
                                <p className="text-xs text-slate-500">10-1,000 tags per video</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
