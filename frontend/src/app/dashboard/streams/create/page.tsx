"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    ArrowLeft,
    ArrowRight,
    Check,
    Upload,
    Calendar,
    Clock,
    Repeat,
    Image as ImageIcon,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { streamsApi, type CreateLiveEventRequest } from "@/lib/api/streams"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

const STEPS = [
    { id: 1, title: "Select Account", description: "Choose your YouTube channel" },
    { id: 2, title: "Stream Details", description: "Title, description & thumbnail" },
    { id: 3, title: "Settings", description: "Latency, DVR & category" },
    { id: 4, title: "Schedule", description: "When to go live" },
]

const CATEGORIES = [
    { id: "1", name: "Film & Animation" },
    { id: "2", name: "Autos & Vehicles" },
    { id: "10", name: "Music" },
    { id: "15", name: "Pets & Animals" },
    { id: "17", name: "Sports" },
    { id: "20", name: "Gaming" },
    { id: "22", name: "People & Blogs" },
    { id: "23", name: "Comedy" },
    { id: "24", name: "Entertainment" },
    { id: "25", name: "News & Politics" },
    { id: "26", name: "Howto & Style" },
    { id: "27", name: "Education" },
    { id: "28", name: "Science & Technology" },
]

interface FormData {
    accountId: string
    title: string
    description: string
    thumbnailUrl: string
    thumbnailFile: File | null
    privacyStatus: "public" | "unlisted" | "private"
    latencyMode: "normal" | "low" | "ultraLow"
    enableDvr: boolean
    enableAutoStart: boolean
    enableAutoStop: boolean
    category: string
    scheduleType: "now" | "scheduled"
    scheduledStart: string
    scheduledEnd: string
    isRecurring: boolean
    recurrencePattern: "daily" | "weekly" | "monthly"
}

function StepIndicator({ currentStep }: { currentStep: number }) {
    return (
        <div className="flex items-center justify-center mb-8">
            {STEPS.map((step, index) => (
                <div key={step.id} className="flex items-center">
                    <div className="flex flex-col items-center">
                        <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors ${currentStep > step.id
                                ? "bg-green-500 border-green-500 text-white"
                                : currentStep === step.id
                                    ? "bg-primary border-primary text-primary-foreground"
                                    : "border-muted-foreground/30 text-muted-foreground"
                                }`}
                        >
                            {currentStep > step.id ? (
                                <Check className="h-5 w-5" />
                            ) : (
                                <span className="text-sm font-medium">{step.id}</span>
                            )}
                        </div>
                        <span className="text-xs mt-1 text-center max-w-[80px] hidden sm:block">
                            {step.title}
                        </span>
                    </div>
                    {index < STEPS.length - 1 && (
                        <div
                            className={`w-12 sm:w-20 h-0.5 mx-2 ${currentStep > step.id ? "bg-green-500" : "bg-muted-foreground/30"
                                }`}
                        />
                    )}
                </div>
            ))}
        </div>
    )
}

export default function CreateStreamPage() {
    const router = useRouter()
    const [currentStep, setCurrentStep] = useState(1)
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(false)
    const [submitting, setSubmitting] = useState(false)

    const [formData, setFormData] = useState<FormData>({
        accountId: "",
        title: "",
        description: "",
        thumbnailUrl: "",
        thumbnailFile: null,
        privacyStatus: "public",
        latencyMode: "normal",
        enableDvr: true,
        enableAutoStart: true,
        enableAutoStop: false,
        category: "20",
        scheduleType: "now",
        scheduledStart: "",
        scheduledEnd: "",
        isRecurring: false,
        recurrencePattern: "weekly",
    })

    useEffect(() => {
        loadAccounts()
    }, [])

    const loadAccounts = async () => {
        try {
            setLoading(true)
            const data = await accountsApi.getAccounts()
            const accountList = Array.isArray(data) ? data : []
            setAccounts(accountList.filter((a) => a.hasLiveStreamingEnabled))
        } catch (error) {
            console.error("Failed to load accounts:", error)
        } finally {
            setLoading(false)
        }
    }

    const updateFormData = (updates: Partial<FormData>) => {
        setFormData((prev) => ({ ...prev, ...updates }))
    }

    const handleThumbnailUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            updateFormData({
                thumbnailFile: file,
                thumbnailUrl: URL.createObjectURL(file),
            })
        }
    }

    const canProceed = () => {
        switch (currentStep) {
            case 1:
                return !!formData.accountId
            case 2:
                return !!formData.title.trim()
            case 3:
                return true
            case 4:
                if (formData.scheduleType === "scheduled") {
                    return !!formData.scheduledStart
                }
                return true
            default:
                return false
        }
    }

    const handleSubmit = async () => {
        try {
            setSubmitting(true)
            const scheduledStart =
                formData.scheduleType === "now"
                    ? new Date().toISOString()
                    : new Date(formData.scheduledStart).toISOString()

            const request: CreateLiveEventRequest = {
                account_id: formData.accountId,
                title: formData.title,
                description: formData.description || undefined,
                scheduled_start: scheduledStart,
                scheduled_end: formData.scheduledEnd
                    ? new Date(formData.scheduledEnd).toISOString()
                    : undefined,
                privacy_status: formData.privacyStatus,
                enable_dvr: formData.enableDvr,
                enable_auto_start: formData.enableAutoStart,
                enable_auto_stop: formData.enableAutoStop,
                thumbnail_url: formData.thumbnailUrl || undefined,
            }

            const event = await streamsApi.createEvent(request)
            router.push(`/dashboard/streams/${event.id}/control`)
        } catch (error) {
            console.error("Failed to create stream:", error)
            alert("Failed to create stream. Please try again.")
        } finally {
            setSubmitting(false)
        }
    }

    const nextStep = () => {
        if (currentStep < 4) setCurrentStep(currentStep + 1)
    }

    const prevStep = () => {
        if (currentStep > 1) setCurrentStep(currentStep - 1)
    }

    const selectedAccount = accounts.find((a) => a.id === formData.accountId)

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: "Create Stream" },
            ]}
        >
            <div className="max-w-3xl mx-auto space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold">Create Live Stream</h1>
                    <p className="text-muted-foreground">
                        Set up a new live stream for your YouTube channel
                    </p>
                </div>

                {/* Step Indicator */}
                <StepIndicator currentStep={currentStep} />

                {/* Step Content */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>{STEPS[currentStep - 1].title}</CardTitle>
                        <CardDescription>{STEPS[currentStep - 1].description}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* Step 1: Select Account */}
                        {currentStep === 1 && (
                            <div className="space-y-4">
                                {loading ? (
                                    <p className="text-muted-foreground">Loading accounts...</p>
                                ) : accounts.length === 0 ? (
                                    <div className="text-center py-8">
                                        <p className="text-muted-foreground mb-4">
                                            No accounts with live streaming enabled found.
                                        </p>
                                        <Button
                                            variant="outline"
                                            onClick={() => router.push("/dashboard/accounts")}
                                        >
                                            Manage Accounts
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="grid gap-3">
                                        {accounts.map((account) => (
                                            <div
                                                key={account.id}
                                                onClick={() => updateFormData({ accountId: account.id })}
                                                className={`flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-colors ${formData.accountId === account.id
                                                    ? "border-primary bg-primary/5"
                                                    : "border-border hover:border-primary/50"
                                                    }`}
                                            >
                                                <img
                                                    src={account.thumbnailUrl || "/placeholder-avatar.jpg"}
                                                    alt={account.channelTitle}
                                                    className="w-12 h-12 rounded-full object-cover"
                                                />
                                                <div className="flex-1">
                                                    <h3 className="font-semibold">{account.channelTitle}</h3>
                                                    <p className="text-sm text-muted-foreground">
                                                        {account.subscriberCount.toLocaleString()} subscribers
                                                    </p>
                                                </div>
                                                {formData.accountId === account.id && (
                                                    <Check className="h-5 w-5 text-primary" />
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Step 2: Stream Details */}
                        {currentStep === 2 && (
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <Label htmlFor="title">Stream Title *</Label>
                                    <Input
                                        id="title"
                                        placeholder="Enter your stream title"
                                        value={formData.title}
                                        onChange={(e) => updateFormData({ title: e.target.value })}
                                        maxLength={100}
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        {formData.title.length}/100 characters
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="description">Description</Label>
                                    <Textarea
                                        id="description"
                                        placeholder="Describe your stream..."
                                        value={formData.description}
                                        onChange={(e) => updateFormData({ description: e.target.value })}
                                        rows={4}
                                        maxLength={5000}
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        {formData.description.length}/5000 characters
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label>Thumbnail</Label>
                                    <div className="flex items-start gap-4">
                                        <div className="w-40 aspect-video bg-muted rounded-lg overflow-hidden flex items-center justify-center">
                                            {formData.thumbnailUrl ? (
                                                <img
                                                    src={formData.thumbnailUrl}
                                                    alt="Thumbnail preview"
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <ImageIcon className="h-8 w-8 text-muted-foreground" />
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <Input
                                                type="file"
                                                accept="image/*"
                                                onChange={handleThumbnailUpload}
                                                className="hidden"
                                                id="thumbnail-upload"
                                            />
                                            <Label
                                                htmlFor="thumbnail-upload"
                                                className="inline-flex items-center gap-2 px-4 py-2 border rounded-md cursor-pointer hover:bg-muted"
                                            >
                                                <Upload className="h-4 w-4" />
                                                Upload Thumbnail
                                            </Label>
                                            <p className="text-xs text-muted-foreground mt-2">
                                                Recommended: 1280x720 pixels (16:9 ratio)
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 3: Settings */}
                        {currentStep === 3 && (
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <Label>Latency Mode</Label>
                                    <RadioGroup
                                        value={formData.latencyMode}
                                        onValueChange={(value: string) =>
                                            updateFormData({ latencyMode: value as FormData["latencyMode"] })
                                        }
                                        className="grid gap-3"
                                    >
                                        <div className="flex items-center space-x-3 p-3 border rounded-lg">
                                            <RadioGroupItem value="normal" id="normal" />
                                            <Label htmlFor="normal" className="flex-1 cursor-pointer">
                                                <div className="font-medium">Normal Latency</div>
                                                <div className="text-sm text-muted-foreground">
                                                    Best quality, ~15-30 second delay
                                                </div>
                                            </Label>
                                        </div>
                                        <div className="flex items-center space-x-3 p-3 border rounded-lg">
                                            <RadioGroupItem value="low" id="low" />
                                            <Label htmlFor="low" className="flex-1 cursor-pointer">
                                                <div className="font-medium">Low Latency</div>
                                                <div className="text-sm text-muted-foreground">
                                                    Good for interaction, ~5-10 second delay
                                                </div>
                                            </Label>
                                        </div>
                                        <div className="flex items-center space-x-3 p-3 border rounded-lg">
                                            <RadioGroupItem value="ultraLow" id="ultraLow" />
                                            <Label htmlFor="ultraLow" className="flex-1 cursor-pointer">
                                                <div className="font-medium">Ultra-Low Latency</div>
                                                <div className="text-sm text-muted-foreground">
                                                    Near real-time, ~2-4 second delay
                                                </div>
                                            </Label>
                                        </div>
                                    </RadioGroup>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="category">Category</Label>
                                    <Select
                                        value={formData.category}
                                        onValueChange={(value) => updateFormData({ category: value })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select category" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {CATEGORIES.map((cat) => (
                                                <SelectItem key={cat.id} value={cat.id}>
                                                    {cat.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="privacy">Privacy</Label>
                                    <Select
                                        value={formData.privacyStatus}
                                        onValueChange={(value) =>
                                            updateFormData({ privacyStatus: value as FormData["privacyStatus"] })
                                        }
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select privacy" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="public">Public</SelectItem>
                                            <SelectItem value="unlisted">Unlisted</SelectItem>
                                            <SelectItem value="private">Private</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <Label>Enable DVR</Label>
                                            <p className="text-sm text-muted-foreground">
                                                Allow viewers to rewind during live stream
                                            </p>
                                        </div>
                                        <Switch
                                            checked={formData.enableDvr}
                                            onCheckedChange={(checked) => updateFormData({ enableDvr: checked })}
                                        />
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <Label>Auto-Start</Label>
                                            <p className="text-sm text-muted-foreground">
                                                Automatically start when scheduled time arrives
                                            </p>
                                        </div>
                                        <Switch
                                            checked={formData.enableAutoStart}
                                            onCheckedChange={(checked) => updateFormData({ enableAutoStart: checked })}
                                        />
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <div>
                                            <Label>Auto-Stop</Label>
                                            <p className="text-sm text-muted-foreground">
                                                Automatically stop at scheduled end time
                                            </p>
                                        </div>
                                        <Switch
                                            checked={formData.enableAutoStop}
                                            onCheckedChange={(checked) => updateFormData({ enableAutoStop: checked })}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 4: Schedule */}
                        {currentStep === 4 && (
                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <Label>When to go live</Label>
                                    <RadioGroup
                                        value={formData.scheduleType}
                                        onValueChange={(value: string) =>
                                            updateFormData({ scheduleType: value as FormData["scheduleType"] })
                                        }
                                        className="grid gap-3"
                                    >
                                        <div className="flex items-center space-x-3 p-3 border rounded-lg">
                                            <RadioGroupItem value="now" id="now" />
                                            <Label htmlFor="now" className="flex-1 cursor-pointer">
                                                <div className="font-medium flex items-center gap-2">
                                                    <Clock className="h-4 w-4" />
                                                    Start Now
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    Go live immediately after creation
                                                </div>
                                            </Label>
                                        </div>
                                        <div className="flex items-center space-x-3 p-3 border rounded-lg">
                                            <RadioGroupItem value="scheduled" id="scheduled" />
                                            <Label htmlFor="scheduled" className="flex-1 cursor-pointer">
                                                <div className="font-medium flex items-center gap-2">
                                                    <Calendar className="h-4 w-4" />
                                                    Schedule for Later
                                                </div>
                                                <div className="text-sm text-muted-foreground">
                                                    Set a specific date and time
                                                </div>
                                            </Label>
                                        </div>
                                    </RadioGroup>
                                </div>

                                {formData.scheduleType === "scheduled" && (
                                    <>
                                        <div className="grid gap-4 sm:grid-cols-2">
                                            <div className="space-y-2">
                                                <Label htmlFor="start-time">Start Date & Time *</Label>
                                                <Input
                                                    id="start-time"
                                                    type="datetime-local"
                                                    value={formData.scheduledStart}
                                                    onChange={(e) => updateFormData({ scheduledStart: e.target.value })}
                                                    min={new Date().toISOString().slice(0, 16)}
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="end-time">End Date & Time (Optional)</Label>
                                                <Input
                                                    id="end-time"
                                                    type="datetime-local"
                                                    value={formData.scheduledEnd}
                                                    onChange={(e) => updateFormData({ scheduledEnd: e.target.value })}
                                                    min={formData.scheduledStart || new Date().toISOString().slice(0, 16)}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between p-4 border rounded-lg">
                                            <div className="flex items-center gap-3">
                                                <Repeat className="h-5 w-5 text-muted-foreground" />
                                                <div>
                                                    <Label>Recurring Stream</Label>
                                                    <p className="text-sm text-muted-foreground">
                                                        Automatically create future streams
                                                    </p>
                                                </div>
                                            </div>
                                            <Switch
                                                checked={formData.isRecurring}
                                                onCheckedChange={(checked) => updateFormData({ isRecurring: checked })}
                                            />
                                        </div>

                                        {formData.isRecurring && (
                                            <div className="space-y-2">
                                                <Label>Repeat</Label>
                                                <Select
                                                    value={formData.recurrencePattern}
                                                    onValueChange={(value) =>
                                                        updateFormData({
                                                            recurrencePattern: value as FormData["recurrencePattern"],
                                                        })
                                                    }
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue placeholder="Select frequency" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="daily">Daily</SelectItem>
                                                        <SelectItem value="weekly">Weekly</SelectItem>
                                                        <SelectItem value="monthly">Monthly</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        )}
                                    </>
                                )}

                                {/* Summary */}
                                <div className="p-4 bg-muted rounded-lg space-y-2">
                                    <h4 className="font-medium">Stream Summary</h4>
                                    <div className="text-sm space-y-1">
                                        <p>
                                            <span className="text-muted-foreground">Channel:</span>{" "}
                                            {selectedAccount?.channelTitle || "Not selected"}
                                        </p>
                                        <p>
                                            <span className="text-muted-foreground">Title:</span>{" "}
                                            {formData.title || "Not set"}
                                        </p>
                                        <p>
                                            <span className="text-muted-foreground">Privacy:</span>{" "}
                                            {formData.privacyStatus}
                                        </p>
                                        <p>
                                            <span className="text-muted-foreground">Latency:</span>{" "}
                                            {formData.latencyMode === "ultraLow"
                                                ? "Ultra-Low"
                                                : formData.latencyMode === "low"
                                                    ? "Low"
                                                    : "Normal"}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Navigation Buttons */}
                <div className="flex items-center justify-between">
                    <Button
                        variant="outline"
                        onClick={currentStep === 1 ? () => router.push("/dashboard/streams") : prevStep}
                    >
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        {currentStep === 1 ? "Cancel" : "Back"}
                    </Button>

                    {currentStep < 4 ? (
                        <Button onClick={nextStep} disabled={!canProceed()}>
                            Next
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    ) : (
                        <Button
                            onClick={handleSubmit}
                            disabled={!canProceed() || submitting}
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                        >
                            {submitting ? "Creating..." : "Create Stream"}
                        </Button>
                    )}
                </div>
            </div>
        </DashboardLayout>
    )
}
