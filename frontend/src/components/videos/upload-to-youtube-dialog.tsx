/**
 * Upload to YouTube Dialog Component
 * 
 * Dialog for uploading library videos to YouTube with full configuration.
 * Requirements: 2.1, 2.2, 2.3 (YouTube Upload)
 * Design: UploadToYouTubeDialog component
 */

"use client"

import { useState, useEffect } from "react"
import { Loader2, Youtube, Calendar, AlertTriangle, RefreshCw } from "lucide-react"
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
import { CategorySelect } from "@/components/videos/category-select"
import { SchedulePicker } from "@/components/videos/schedule-picker"
import { videoLibraryApi } from "@/lib/api/video-library"
import type { Video, YouTubeAccount } from "@/types"

interface UploadToYouTubeDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    video: Video | null
    accounts: YouTubeAccount[]
}

export function UploadToYouTubeDialog({
    open,
    onOpenChange,
    onSuccess,
    video,
    accounts,
}: UploadToYouTubeDialogProps) {
    const { addToast } = useToast()
    const [loading, setLoading] = useState(false)
    const [uploadScheduled, setUploadScheduled] = useState(false)

    const [formData, setFormData] = useState({
        accountId: "",
        title: "",
        description: "",
        tags: [] as string[],
        categoryId: "",
        visibility: "private" as "public" | "unlisted" | "private",
        scheduledPublishAt: null as Date | null,
    })
    const [tagInput, setTagInput] = useState("")
    const [errors, setErrors] = useState<Record<string, string>>({})

    // Pre-fill form when video changes
    useEffect(() => {
        if (video) {
            // Find first active account, or first account if none active
            const activeAccounts = accounts.filter(a => a.status === "active")
            const defaultAccount = activeAccounts.length > 0 ? activeAccounts[0] : (accounts.length > 0 ? accounts[0] : null)

            setFormData({
                accountId: defaultAccount?.id || "",
                title: video.title,
                description: video.description || "",
                tags: video.tags || [],
                categoryId: video.categoryId || "",
                visibility: "private",
                scheduledPublishAt: null,
            })
            setTagInput("")
            setUploadScheduled(false)
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
            newErrors.title = "Title is required"
        } else if (formData.title.length > 100) {
            newErrors.title = "Title must be less than 100 characters"
        }
        if (formData.description && formData.description.length > 5000) {
            newErrors.description = "Description must be less than 5000 characters"
        }
        if (uploadScheduled && !formData.scheduledPublishAt) {
            newErrors.scheduledPublishAt = "Please select a publish date and time"
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleAddTag = () => {
        const tag = tagInput.trim()
        if (tag && !formData.tags.includes(tag)) {
            setFormData({ ...formData, tags: [...formData.tags, tag] })
            setTagInput("")
        }
    }

    const handleRemoveTag = (tagToRemove: string) => {
        setFormData({
            ...formData,
            tags: formData.tags.filter((tag) => tag !== tagToRemove),
        })
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!video || !validateForm()) return

        try {
            setLoading(true)
            const result = await videoLibraryApi.uploadToYouTube(video.id, {
                accountId: formData.accountId,
                title: formData.title,
                description: formData.description || undefined,
                tags: formData.tags.length > 0 ? formData.tags : undefined,
                categoryId: formData.categoryId || undefined,
                visibility: formData.visibility,
                scheduledPublishAt: uploadScheduled && formData.scheduledPublishAt
                    ? formData.scheduledPublishAt.toISOString()
                    : undefined,
            })

            addToast({
                type: "success",
                title: "Success",
                description: uploadScheduled
                    ? "Video scheduled for upload to YouTube"
                    : "Video upload to YouTube started",
            })

            onSuccess()
            onOpenChange(false)
        } catch (error: any) {
            console.error("Failed to upload to YouTube:", error)
            addToast({
                type: "error",
                title: "Error",
                description: error.message || "Failed to upload to YouTube",
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
                            <Youtube className="h-5 w-5 text-red-600" />
                            Upload to YouTube
                        </DialogTitle>
                        <DialogDescription>
                            Configure and upload &quot;{video.title}&quot; to YouTube
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

                        {/* Title */}
                        <div className="space-y-2">
                            <Label htmlFor="title">
                                Title <span className="text-destructive">*</span>
                            </Label>
                            <Input
                                id="title"
                                value={formData.title}
                                onChange={(e) =>
                                    setFormData({ ...formData, title: e.target.value })
                                }
                                placeholder="Video title"
                                disabled={loading}
                                className={errors.title ? "border-destructive" : ""}
                            />
                            {errors.title && (
                                <p className="text-sm text-destructive">{errors.title}</p>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {formData.title.length}/100 characters
                            </p>
                        </div>

                        {/* Description */}
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                value={formData.description}
                                onChange={(e) =>
                                    setFormData({ ...formData, description: e.target.value })
                                }
                                placeholder="Video description"
                                rows={4}
                                disabled={loading}
                                className={errors.description ? "border-destructive" : ""}
                            />
                            {errors.description && (
                                <p className="text-sm text-destructive">{errors.description}</p>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {formData.description.length}/5000 characters
                            </p>
                        </div>

                        {/* Tags */}
                        <div className="space-y-2">
                            <Label htmlFor="tags">Tags</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="tags"
                                    value={tagInput}
                                    onChange={(e) => setTagInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") {
                                            e.preventDefault()
                                            handleAddTag()
                                        }
                                    }}
                                    placeholder="Add tag and press Enter"
                                    disabled={loading}
                                />
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handleAddTag}
                                    disabled={loading || !tagInput.trim()}
                                >
                                    Add
                                </Button>
                            </div>
                            {formData.tags.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {formData.tags.map((tag) => (
                                        <div
                                            key={tag}
                                            className="flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-sm"
                                        >
                                            <span>{tag}</span>
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveTag(tag)}
                                                className="text-muted-foreground hover:text-foreground"
                                                disabled={loading}
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Category */}
                        <div className="space-y-2">
                            <Label htmlFor="category">Category</Label>
                            <CategorySelect
                                value={formData.categoryId}
                                onValueChange={(value) =>
                                    setFormData({ ...formData, categoryId: value })
                                }
                                disabled={loading}
                            />
                        </div>

                        {/* Visibility */}
                        <div className="space-y-2">
                            <Label>Visibility</Label>
                            <RadioGroup
                                value={formData.visibility}
                                onValueChange={(value: any) =>
                                    setFormData({ ...formData, visibility: value })
                                }
                                disabled={loading}
                            >
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="public" id="public" />
                                    <Label htmlFor="public" className="cursor-pointer">
                                        Public - Anyone can see
                                    </Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="unlisted" id="unlisted" />
                                    <Label htmlFor="unlisted" className="cursor-pointer">
                                        Unlisted - Only people with the link
                                    </Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="private" id="private" />
                                    <Label htmlFor="private" className="cursor-pointer">
                                        Private - Only you can see
                                    </Label>
                                </div>
                            </RadioGroup>
                        </div>

                        {/* Schedule Upload */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="schedule">Schedule Upload</Label>
                                <Switch
                                    id="schedule"
                                    checked={uploadScheduled}
                                    onCheckedChange={setUploadScheduled}
                                    disabled={loading}
                                />
                            </div>
                            {uploadScheduled && (
                                <div className="space-y-2">
                                    <SchedulePicker
                                        value={formData.scheduledPublishAt}
                                        onChange={(value) =>
                                            setFormData({ ...formData, scheduledPublishAt: value })
                                        }
                                        disabled={loading}
                                    />
                                    {errors.scheduledPublishAt && (
                                        <p className="text-sm text-destructive">
                                            {errors.scheduledPublishAt}
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
                            {uploadScheduled ? "Schedule Upload" : "Upload Now"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
