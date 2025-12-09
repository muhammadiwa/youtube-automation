"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import {
    ArrowLeft,
    Plus,
    Trash2,
    Radio,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Loader2,
    Copy,
    Eye,
    EyeOff,
    Twitch,
    Facebook,
    Youtube,
    Server,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { streamsApi, type LiveEvent, type SimulcastTarget } from "@/lib/api/streams"

const PLATFORMS = [
    { id: "youtube", name: "YouTube", icon: Youtube, color: "text-red-500", rtmpUrl: "rtmp://a.rtmp.youtube.com/live2" },
    { id: "twitch", name: "Twitch", icon: Twitch, color: "text-purple-500", rtmpUrl: "rtmp://live.twitch.tv/app" },
    { id: "facebook", name: "Facebook", icon: Facebook, color: "text-blue-500", rtmpUrl: "rtmps://live-api-s.facebook.com:443/rtmp" },
    { id: "tiktok", name: "TikTok", icon: Radio, color: "text-pink-500", rtmpUrl: "rtmp://push.tiktok.com/live" },
    { id: "custom", name: "Custom RTMP", icon: Server, color: "text-gray-500", rtmpUrl: "" },
]

function PlatformIcon({ platform }: { platform: string }) {
    const config = PLATFORMS.find((p) => p.id === platform) || PLATFORMS[4]
    const Icon = config.icon
    return <Icon className={`h-5 w-5 ${config.color}`} />
}

function StatusBadge({ status }: { status: SimulcastTarget["status"] }) {
    switch (status) {
        case "active":
            return (
                <Badge className="bg-green-500 text-white">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Active
                </Badge>
            )
        case "error":
            return (
                <Badge variant="destructive">
                    <XCircle className="mr-1 h-3 w-3" />
                    Error
                </Badge>
            )
        default:
            return (
                <Badge variant="secondary">
                    <AlertTriangle className="mr-1 h-3 w-3" />
                    Inactive
                </Badge>
            )
    }
}

function AddTargetDialog({
    open,
    onOpenChange,
    onAdd,
}: {
    open: boolean
    onOpenChange: (open: boolean) => void
    onAdd: (platform: string, rtmpUrl: string, streamKey: string) => void
}) {
    const [platform, setPlatform] = useState("youtube")
    const [rtmpUrl, setRtmpUrl] = useState("")
    const [streamKey, setStreamKey] = useState("")
    const [showKey, setShowKey] = useState(false)

    useEffect(() => {
        const config = PLATFORMS.find((p) => p.id === platform)
        if (config && config.rtmpUrl) {
            setRtmpUrl(config.rtmpUrl)
        }
    }, [platform])

    const handleSubmit = () => {
        if (!rtmpUrl.trim() || !streamKey.trim()) {
            alert("Please fill in all fields")
            return
        }
        onAdd(platform, rtmpUrl, streamKey)
        setPlatform("youtube")
        setRtmpUrl("")
        setStreamKey("")
        onOpenChange(false)
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add Simulcast Target</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label>Platform</Label>
                        <Select value={platform} onValueChange={setPlatform}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {PLATFORMS.map((p) => (
                                    <SelectItem key={p.id} value={p.id}>
                                        <div className="flex items-center gap-2">
                                            <p.icon className={`h-4 w-4 ${p.color}`} />
                                            {p.name}
                                        </div>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label>RTMP URL</Label>
                        <Input
                            placeholder="rtmp://..."
                            value={rtmpUrl}
                            onChange={(e) => setRtmpUrl(e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Stream Key</Label>
                        <div className="flex gap-2">
                            <Input
                                type={showKey ? "text" : "password"}
                                placeholder="Enter stream key"
                                value={streamKey}
                                onChange={(e) => setStreamKey(e.target.value)}
                            />
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={() => setShowKey(!showKey)}
                            >
                                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button onClick={handleSubmit}>Add Target</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default function SimulcastPage() {
    const params = useParams()
    const router = useRouter()
    const eventId = params.id as string

    const [event, setEvent] = useState<LiveEvent | null>(null)
    const [targets, setTargets] = useState<SimulcastTarget[]>([])
    const [loading, setLoading] = useState(true)
    const [addDialogOpen, setAddDialogOpen] = useState(false)
    const [testingTarget, setTestingTarget] = useState<string | null>(null)
    const [copied, setCopied] = useState<string | null>(null)

    const loadData = useCallback(async () => {
        try {
            setLoading(true)
            const [eventData, targetsData] = await Promise.all([
                streamsApi.getEvent(eventId),
                streamsApi.getSimulcastTargets(eventId),
            ])
            setEvent(eventData)
            setTargets(targetsData)
        } catch (error) {
            console.error("Failed to load data:", error)
        } finally {
            setLoading(false)
        }
    }, [eventId])

    useEffect(() => {
        loadData()
    }, [loadData])

    const handleAddTarget = async (platform: string, rtmpUrl: string, streamKey: string) => {
        try {
            const newTarget = await streamsApi.addSimulcastTarget(eventId, {
                platform,
                rtmp_url: rtmpUrl,
                stream_key: streamKey,
            })
            setTargets((prev) => [...prev, newTarget])
        } catch (error) {
            console.error("Failed to add target:", error)
            alert("Failed to add simulcast target")
        }
    }

    const handleRemoveTarget = async (targetId: string) => {
        if (!confirm("Remove this simulcast target?")) return
        try {
            await streamsApi.removeSimulcastTarget(eventId, targetId)
            setTargets((prev) => prev.filter((t) => t.id !== targetId))
        } catch (error) {
            console.error("Failed to remove target:", error)
            alert("Failed to remove simulcast target")
        }
    }

    const handleTestConnection = async (targetId: string) => {
        setTestingTarget(targetId)
        // Simulate connection test
        await new Promise((resolve) => setTimeout(resolve, 2000))
        setTestingTarget(null)
        alert("Connection test completed successfully!")
    }

    const copyToClipboard = (text: string, field: string) => {
        navigator.clipboard.writeText(text)
        setCopied(field)
        setTimeout(() => setCopied(null), 2000)
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Streams", href: "/dashboard/streams" },
                    { label: "Simulcast" },
                ]}
            >
                <div className="max-w-4xl mx-auto space-y-6">
                    <Skeleton className="h-10 w-64" />
                    <Skeleton className="h-[200px]" />
                    <Skeleton className="h-[200px]" />
                </div>
            </DashboardLayout>
        )
    }

    if (!event) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Streams", href: "/dashboard/streams" },
                    { label: "Simulcast" },
                ]}
            >
                <div className="text-center py-12">
                    <h2 className="text-xl font-semibold mb-2">Stream not found</h2>
                    <Button onClick={() => router.push("/dashboard/streams")}>Back to Streams</Button>
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Streams", href: "/dashboard/streams" },
                { label: event.title, href: `/dashboard/streams/${eventId}/control` },
                { label: "Simulcast" },
            ]}
        >
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => router.push(`/dashboard/streams/${eventId}/control`)}
                    >
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div className="flex-1">
                        <h1 className="text-3xl font-bold">Simulcast Configuration</h1>
                        <p className="text-muted-foreground">
                            Stream to multiple platforms simultaneously
                        </p>
                    </div>
                    <Button onClick={() => setAddDialogOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Platform
                    </Button>
                </div>

                {/* Stream Info */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="text-lg">Primary Stream</CardTitle>
                        <CardDescription>Your main YouTube stream</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-lg">
                                <Youtube className="h-8 w-8 text-red-500" />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold">{event.title}</h3>
                                <p className="text-sm text-muted-foreground">
                                    Status: {event.status}
                                </p>
                            </div>
                            <Badge
                                className={
                                    event.status === "live"
                                        ? "bg-red-500 text-white animate-pulse"
                                        : "bg-gray-500 text-white"
                                }
                            >
                                {event.status === "live" ? "LIVE" : event.status}
                            </Badge>
                        </div>
                    </CardContent>
                </Card>

                {/* Simulcast Targets */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Radio className="h-5 w-5" />
                            Simulcast Targets
                        </CardTitle>
                        <CardDescription>
                            {targets.length} platform(s) configured
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {targets.length === 0 ? (
                            <div className="text-center py-8 border-2 border-dashed rounded-lg">
                                <Radio className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                                <p className="text-muted-foreground mb-4">
                                    No simulcast targets configured
                                </p>
                                <Button onClick={() => setAddDialogOpen(true)}>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Add Your First Platform
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {targets.map((target) => (
                                    <div
                                        key={target.id}
                                        className="flex items-center gap-4 p-4 bg-muted rounded-lg"
                                    >
                                        <div className="p-2 bg-background rounded-lg">
                                            <PlatformIcon platform={target.platform} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-semibold capitalize">
                                                    {PLATFORMS.find((p) => p.id === target.platform)?.name ||
                                                        target.platform}
                                                </h3>
                                                <StatusBadge status={target.status} />
                                            </div>
                                            <div className="flex items-center gap-2 mt-1">
                                                <code className="text-xs text-muted-foreground truncate max-w-[300px]">
                                                    {target.rtmp_url}
                                                </code>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6"
                                                    onClick={() => copyToClipboard(target.rtmp_url, target.id)}
                                                >
                                                    {copied === target.id ? (
                                                        <CheckCircle className="h-3 w-3 text-green-500" />
                                                    ) : (
                                                        <Copy className="h-3 w-3" />
                                                    )}
                                                </Button>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleTestConnection(target.id)}
                                                disabled={testingTarget === target.id}
                                            >
                                                {testingTarget === target.id ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        Testing...
                                                    </>
                                                ) : (
                                                    "Test Connection"
                                                )}
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleRemoveTarget(target.id)}
                                            >
                                                <Trash2 className="h-4 w-4 text-destructive" />
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Quick Add Platforms */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle className="text-lg">Quick Add Platforms</CardTitle>
                        <CardDescription>
                            Select platforms to add with default RTMP URLs
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {PLATFORMS.filter((p) => p.id !== "custom").map((platform) => {
                                const isAdded = targets.some((t) => t.platform === platform.id)
                                return (
                                    <div
                                        key={platform.id}
                                        className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${isAdded
                                                ? "border-primary bg-primary/5"
                                                : "border-border hover:border-primary/50 cursor-pointer"
                                            }`}
                                        onClick={() => {
                                            if (!isAdded) {
                                                setAddDialogOpen(true)
                                            }
                                        }}
                                    >
                                        <platform.icon className={`h-8 w-8 ${platform.color}`} />
                                        <span className="text-sm font-medium">{platform.name}</span>
                                        {isAdded && (
                                            <Badge variant="secondary" className="text-xs">
                                                Added
                                            </Badge>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    </CardContent>
                </Card>

                {/* Tips */}
                <Card className="border-0 shadow-lg bg-blue-50 dark:bg-blue-900/20">
                    <CardContent className="pt-6">
                        <h3 className="font-semibold mb-2">Tips for Simulcasting</h3>
                        <ul className="text-sm text-muted-foreground space-y-1">
                            <li>• Ensure your internet upload speed can handle multiple streams</li>
                            <li>• Each platform may have different stream key formats</li>
                            <li>• Test connections before going live</li>
                            <li>• Monitor each platform&apos;s health during the stream</li>
                        </ul>
                    </CardContent>
                </Card>
            </div>

            <AddTargetDialog
                open={addDialogOpen}
                onOpenChange={setAddDialogOpen}
                onAdd={handleAddTarget}
            />
        </DashboardLayout>
    )
}
