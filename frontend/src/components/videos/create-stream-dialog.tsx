/**
 * Create Stream Dialog Component
 * 
 * Dialog for creating 24/7 live streams from library videos.
 * Requirements: 3.1 (Streaming Integration)
 * Design: CreateStreamDialog component
 */

"use client"

import { useState, useEffect } from "react"
import { Loader2, Radio, AlertTriangle } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/components/ui/toast"
import { SchedulePicker } from "@/components/videos/schedule-picker"
import { videoLibraryApi } from "@/lib/api/video-library"
import type { Video, YouTubeAccount } from "@/types"

interface CreateStreamDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: (streamJobId: string) => void
    video: Video | null
    accounts: YouTubeAccount[]
}

const RESOLUTION_PRESETS = [
    { value: "720p", label: "720p (1280x720)", bitrate: 3000, fps: 30 },
    { value: "1080p", label: "1080p (1920x1080)", bitrate: 6000, fps: 30 },
    { value: "1440p", label: "1440p (2560x1440)", bitrate: 9000, fps: 30 },
    { value: "4k", label: "4K (3840x2160)", bitrate: 20000, fps: 30 },
]

const FPS_OPTIONS = [24, 30, 60]

export function CreateStreamDialog({
    open,
    onOpenChange,
    onSuccess,
    video,
    accounts,
}: CreateStreamDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [streamScheduled, setStreamScheduled] = useState(false)

    const [formData, setFormData] = useState({
        accountId: "",
        title: "",
        loopMode: "infinite" as "none" | "count" | "infinite",
        loopCount: 1,
        resolution: "1080p" as "720p" | "1080p" | "1440p" | "4k",
        targetBitrate: 6000,
        targetFps: 30,
        scheduledStartAt: null as Date | null,
    })
    const [errors, setErrors] = useState<Record<string, string>>({})

    // Pre-fill form when video changes
    useEffect(() => {
        if (video) {
            // Find first active account
            const activeAccounts = accounts.filter(a => a.status === "active")
            const defaultAccount = activeAccounts.length > 0 ? activeAccounts[0] : (accounts.length > 0 ? accounts[0] : null)

            setFormData({
                accountId: defaultAccount?.id || "",
                title: `${video.title} - 24/7 Live Stream`,
                loopMode: "infinite",
                loopCount: 1,
                resolution: "1080p" as "720p" | "1080p" | "1440p" | "4k",
                targetBitrate: 6000,
                targetFps: 30,
                scheduledStartAt: null,
            })
            setStreamScheduled(false)
            setErrors({})
        }
    }, [video, accounts])

    // Get selected account details
    const selectedAccount = accounts.find(a => a.id === formData.accountId)
    const isSelectedAccountExpired = selectedAccount?.status === "expired"
    const isSelectedAccountError = selectedAccount?.status === "error"
    const hasActiveAccounts = accounts.some(a => a.status === "active")

    const validateForm = () => {
        const newErrors: Record<string, string> = {}

        if (!formData.accountId) {
            newErrors.accountId = "Please select a YouTube account"
        } else if (isSelectedAccountExpired || isSelectedAccountError) {
            newErrors.accountId = "Selected account needs to be reconnected"
        }
        if (!formData.title.trim()) {
            newErrors.title = "Stream title is required"
        }
        if (formData.loopMode === "count" && formData.loopCount < 1) {
            newErrors.loopCount = "Loop count must be at least 1"
        }
        if (formData.targetBitrate < 1000 || formData.targetBitrate > 50000) {
            newErrors.targetBitrate = "Bitrate must be between 1000 and 50000 kbps"
        }
        if (streamScheduled && !formData.scheduledStartAt) {
            newErrors.scheduledStartAt = "Please select a start date and time"
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleResolutionChange = (resolution: string) => {
        const preset = RESOLUTION_PRESETS.find((p) => p.value === resolution)
        if (preset) {
            setFormData({
                ...formData,
                resolution: resolution as "720p" | "1080p" | "1440p" | "4k",
                targetBitrate: preset.bitrate,
                targetFps: preset.fps,
            })
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!video || !validateForm()) return

        try {
            setLoading(true)
            const result = await videoLibraryApi.createStream(video.id, {
                accountId: formData.accountId,
                title: formData.title,
                loopMode: formData.loopMode,
                loopCount: formData.loopMode === "count" ? formData.loopCount : undefined,
                resolution: formData.resolution,
                targetBitrate: formData.targetBitrate,
                targetFps: formData.targetFps,
                scheduledStartAt: streamScheduled && formData.scheduledStartAt
                    ? formData.scheduledStartAt.toISOString()
                    : undefined,
            })

            addToast({
                type: "success",
                title: "Success",
                description: streamScheduled
                    ? "Stream scheduled successfully"
                    : "Stream created successfully",
            })

            onSuccess(result.streamJobId)
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to create stream:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to create stream",
            })
        } finally {
            setLoading(false)
        }
    }

    if (!video) return null

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Radio className="h-5 w-5 text-red-600" />
                            Create Live Stream
                        </DialogTitle>
                        <DialogDescription>
                            Create a 24/7 looping live stream from &quot;{video.title}&quot;
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        {/* Account Selector */}
                        <div className="space-y-2">
                            <Label htmlFor="accountId">
                                YouTube Account <span className="text-destructive">*</span>
                            </Label>
                            {accounts.length === 0 ? (
                                <div className="rounded-lg border border-destructive bg-destructive/10 p-3 text-sm">
                                    No YouTube accounts connected. Please connect an account first.
                                </div>
                            ) : !hasActiveAccounts ? (
                                <div className="rounded-lg border border-amber-500 bg-amber-500/10 p-3 text-sm space-y-2">
                                    <div className="flex items-center gap-2 text-amber-600">
                                        <AlertTriangle className="h-4 w-4" />
                                        <span className="font-medium">All accounts need reconnection</span>
                                    </div>
                                    <p className="text-muted-foreground">
                                        Your YouTube account tokens have expired. Please go to Accounts page and reconnect your accounts.
                                    </p>
                                </div>
                            ) : (
                                <>
                                    <Select
                                        value={formData.accountId}
                                        onValueChange={(value) =>
                                            setFormData({ ...formData, accountId: value })
                                        }
                                        disabled={loading}
                                    >
                                        <SelectTrigger id="accountId">
                                            <SelectValue placeholder="Select account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accounts.map((account) => (
                                                <SelectItem
                                                    key={account.id}
                                                    value={account.id}
                                                    disabled={account.status !== "active"}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        {account.thumbnailUrl && (
                                                            <img
                                                                src={account.thumbnailUrl}
                                                                alt={account.channelTitle}
                                                                className="h-6 w-6 rounded-full"
                                                            />
                                                        )}
                                                        <span>{account.channelTitle}</span>
                                                        {account.status === "expired" && (
                                                            <span className="text-xs text-amber-600 flex items-center gap-1">
                                                                <AlertTriangle className="h-3 w-3" />
                                                                Expired
                                                            </span>
                                                        )}
                                                        {account.status === "error" && (
                                                            <span className="text-xs text-destructive flex items-center gap-1">
                                                                <AlertTriangle className="h-3 w-3" />
                                                                Error
                                                            </span>
                                                        )}
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    {(isSelectedAccountExpired || isSelectedAccountError) && (
                                        <div className="rounded-lg border border-amber-500 bg-amber-500/10 p-3 text-sm space-y-2">
                                            <div className="flex items-center gap-2 text-amber-600">
                                                <AlertTriangle className="h-4 w-4" />
                                                <span className="font-medium">Account needs reconnection</span>
                                            </div>
                                            <p className="text-muted-foreground">
                                                This account&apos;s token has expired or been revoked. Please go to Accounts page and reconnect this account.
                                            </p>
                                        </div>
                                    )}
                                </>
                            )}
                            {errors.accountId && (
                                <p className="text-sm text-destructive">{errors.accountId}</p>
                            )}
                        </div>

                        {/* Stream Title */}
                        <div className="space-y-2">
                            <Label htmlFor="title">
                                Stream Title <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="title"
                                value={formData.title}
                                onChange={(e) =>
                                    setFormData({ ...formData, title: e.target.value })
                                }
                                placeholder="Stream title"
                                disabled={loading}
                                className={errors.title ? "border-destructive" : ""}
                            />
                            {errors.title && (
                                <p className="text-sm text-destructive">{errors.title}</p>
                            )}
                        </div>

                        {/* Loop Mode */}
                        <div className="space-y-2">
                            <Label>Loop Mode</Label>
                            <RadioGroup
                                value={formData.loopMode}
                                onValueChange={(value: any) =>
                                    setFormData({ ...formData, loopMode: value })
                                }
                                disabled={loading}
                            >
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="infinite" id="infinite" />
                                    <Label htmlFor="infinite" className="cursor-pointer">
                                        Infinite - Loop forever (24/7)
                                    </Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="count" id="count" />
                                    <Label htmlFor="count" className="cursor-pointer">
                                        Count - Loop specific number of times
                                    </Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="none" id="none" />
                                    <Label htmlFor="none" className="cursor-pointer">
                                        None - Play once
                                    </Label>
                                </div>
                            </RadioGroup>

                            {formData.loopMode === "count" && (
                                <div className="ml-6 space-y-2">
                                    <Label htmlFor="loopCount">Loop Count</Label>
                                    <Input
                                        id="loopCount"
                                        type="number"
                                        min="1"
                                        value={formData.loopCount}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                loopCount: parseInt(e.target.value) || 1,
                                            })
                                        }
                                        disabled={loading}
                                        className={errors.loopCount ? "border-destructive" : ""}
                                    />
                                    {errors.loopCount && (
                                        <p className="text-sm text-destructive">{errors.loopCount}</p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Quality Settings */}
                        <div className="space-y-4 rounded-lg border p-4">
                            <h4 className="font-semibold">Quality Settings</h4>

                            {/* Resolution */}
                            <div className="space-y-2">
                                <Label htmlFor="resolution">Resolution</Label>
                                <Select
                                    value={formData.resolution}
                                    onValueChange={handleResolutionChange}
                                    disabled={loading}
                                >
                                    <SelectTrigger id="resolution">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {RESOLUTION_PRESETS.map((preset) => (
                                            <SelectItem key={preset.value} value={preset.value}>
                                                {preset.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Bitrate */}
                            <div className="space-y-2">
                                <Label htmlFor="bitrate">
                                    Bitrate (kbps)
                                </Label>
                                <Input
                                    id="bitrate"
                                    type="number"
                                    min="1000"
                                    max="50000"
                                    step="100"
                                    value={formData.targetBitrate}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            targetBitrate: parseInt(e.target.value) || 6000,
                                        })
                                    }
                                    disabled={loading}
                                    className={errors.targetBitrate ? "border-destructive" : ""}
                                />
                                {errors.targetBitrate && (
                                    <p className="text-sm text-destructive">{errors.targetBitrate}</p>
                                )}
                                <p className="text-xs text-muted-foreground">
                                    Recommended: 720p=3000, 1080p=6000, 1440p=9000, 4K=20000
                                </p>
                            </div>

                            {/* FPS */}
                            <div className="space-y-2">
                                <Label htmlFor="fps">Frame Rate (FPS)</Label>
                                <Select
                                    value={formData.targetFps.toString()}
                                    onValueChange={(value) =>
                                        setFormData({ ...formData, targetFps: parseInt(value) })
                                    }
                                    disabled={loading}
                                >
                                    <SelectTrigger id="fps">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {FPS_OPTIONS.map((fps) => (
                                            <SelectItem key={fps} value={fps.toString()}>
                                                {fps} FPS
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        {/* Schedule Stream */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="schedule">Schedule Stream</Label>
                                <Switch
                                    id="schedule"
                                    checked={streamScheduled}
                                    onCheckedChange={setStreamScheduled}
                                    disabled={loading}
                                />
                            </div>
                            {streamScheduled && (
                                <div className="space-y-2">
                                    <SchedulePicker
                                        value={formData.scheduledStartAt}
                                        onChange={(value) =>
                                            setFormData({ ...formData, scheduledStartAt: value })
                                        }
                                        disabled={loading}
                                    />
                                    {errors.scheduledStartAt && (
                                        <p className="text-sm text-destructive">
                                            {errors.scheduledStartAt}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={loading || accounts.length === 0 || !hasActiveAccounts || isSelectedAccountExpired || isSelectedAccountError}
                        >
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {streamScheduled ? "Schedule Stream" : "Create Stream"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
