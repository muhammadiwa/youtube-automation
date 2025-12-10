"use client"

import { useState, useEffect } from "react"
import {
    Webhook,
    Plus,
    Edit,
    Trash2,
    Loader2,
    Check,
    X,
    TestTube,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    RefreshCw,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import {
    Alert,
    AlertDescription,
} from "@/components/ui/alert"
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { apiClient } from "@/lib/api/client"

interface WebhookType {
    id: string
    name: string
    url: string
    events: string[]
    secret: string
    is_active: boolean
    last_delivery_at?: string
    last_delivery_status?: string
    total_deliveries: number
    successful_deliveries: number
    failed_deliveries: number
    created_at: string
}

interface WebhookDelivery {
    id: string
    webhook_id: string
    event_type: string
    status: string
    response_status?: number
    response_time_ms?: number
    created_at: string
}

interface TestWebhookResponse {
    success: boolean
    status_code?: number
    response_time_ms?: number
    error?: string
}

const WEBHOOK_EVENTS = [
    { value: "video.uploaded", label: "Video Uploaded", category: "Videos" },
    { value: "video.published", label: "Video Published", category: "Videos" },
    { value: "video.deleted", label: "Video Deleted", category: "Videos" },
    { value: "stream.started", label: "Stream Started", category: "Streams" },
    { value: "stream.ended", label: "Stream Ended", category: "Streams" },
    { value: "stream.error", label: "Stream Error", category: "Streams" },
    { value: "account.connected", label: "Account Connected", category: "Accounts" },
    { value: "account.disconnected", label: "Account Disconnected", category: "Accounts" },
    { value: "subscription.created", label: "Subscription Created", category: "Billing" },
    { value: "subscription.cancelled", label: "Subscription Cancelled", category: "Billing" },
    { value: "payment.completed", label: "Payment Completed", category: "Billing" },
    { value: "payment.failed", label: "Payment Failed", category: "Billing" },
]

const EVENT_CATEGORIES = ["Videos", "Streams", "Accounts", "Billing"]

export default function WebhooksPage() {
    const [webhooks, setWebhooks] = useState<WebhookType[]>([])
    const [loading, setLoading] = useState(true)
    const [dialogOpen, setDialogOpen] = useState(false)
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
    const [editingWebhook, setEditingWebhook] = useState<WebhookType | null>(null)
    const [webhookToDelete, setWebhookToDelete] = useState<WebhookType | null>(null)
    const [saving, setSaving] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [testing, setTesting] = useState<string | null>(null)
    const [testResult, setTestResult] = useState<TestWebhookResponse | null>(null)
    const [error, setError] = useState("")

    // Form state
    const [name, setName] = useState("")
    const [url, setUrl] = useState("")
    const [selectedEvents, setSelectedEvents] = useState<string[]>([])

    // Delivery logs
    const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null)
    const [deliveries, setDeliveries] = useState<Record<string, WebhookDelivery[]>>({})
    const [loadingDeliveries, setLoadingDeliveries] = useState<string | null>(null)

    useEffect(() => {
        loadWebhooks()
    }, [])

    const loadWebhooks = async () => {
        try {
            setLoading(true)
            const userId = localStorage.getItem("user_id") || "current"
            const response = await apiClient.get<{ webhooks: WebhookType[] }>(`/integration/webhooks?user_id=${userId}`)
            setWebhooks(response.webhooks || [])
        } catch (err) {
            console.error("Failed to load webhooks:", err)
            setWebhooks([])
        } finally {
            setLoading(false)
        }
    }

    const loadDeliveries = async (webhookId: string) => {
        try {
            setLoadingDeliveries(webhookId)
            const userId = localStorage.getItem("user_id") || "current"
            const response = await apiClient.get<{ deliveries: WebhookDelivery[] }>(
                `/integration/webhooks/${webhookId}/deliveries?user_id=${userId}`
            )
            setDeliveries((prev) => ({ ...prev, [webhookId]: response.deliveries || [] }))
        } catch (err) {
            console.error("Failed to load deliveries:", err)
        } finally {
            setLoadingDeliveries(null)
        }
    }

    const openCreateDialog = () => {
        setEditingWebhook(null)
        setName("")
        setUrl("")
        setSelectedEvents([])
        setTestResult(null)
        setError("")
        setDialogOpen(true)
    }

    const openEditDialog = (webhook: WebhookType) => {
        setEditingWebhook(webhook)
        setName(webhook.name)
        setUrl(webhook.url)
        setSelectedEvents(webhook.events)
        setTestResult(null)
        setError("")
        setDialogOpen(true)
    }

    const handleSave = async () => {
        if (!name.trim()) {
            setError("Please enter a webhook name")
            return
        }
        if (!url.trim()) {
            setError("Please enter a webhook URL")
            return
        }
        if (selectedEvents.length === 0) {
            setError("Please select at least one event")
            return
        }

        try {
            setSaving(true)
            setError("")
            const userId = localStorage.getItem("user_id") || "current"

            if (editingWebhook) {
                await apiClient.patch(`/integration/webhooks/${editingWebhook.id}?user_id=${userId}`, {
                    name: name.trim(),
                    url: url.trim(),
                    events: selectedEvents,
                })
            } else {
                await apiClient.post(`/integration/webhooks?user_id=${userId}`, {
                    name: name.trim(),
                    url: url.trim(),
                    events: selectedEvents,
                })
            }
            setDialogOpen(false)
            loadWebhooks()
        } catch (err) {
            console.error("Failed to save webhook:", err)
            setError("Failed to save webhook. Please try again.")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async () => {
        if (!webhookToDelete) return

        try {
            setDeleting(true)
            const userId = localStorage.getItem("user_id") || "current"
            await apiClient.delete(`/integration/webhooks/${webhookToDelete.id}?user_id=${userId}`)
            setWebhooks((prev) => prev.filter((w) => w.id !== webhookToDelete.id))
            setDeleteDialogOpen(false)
            setWebhookToDelete(null)
        } catch (err) {
            console.error("Failed to delete webhook:", err)
        } finally {
            setDeleting(false)
        }
    }

    const handleToggleActive = async (webhook: WebhookType) => {
        try {
            const userId = localStorage.getItem("user_id") || "current"
            await apiClient.patch(`/integration/webhooks/${webhook.id}?user_id=${userId}`, {
                is_active: !webhook.is_active
            })
            setWebhooks((prev) =>
                prev.map((w) =>
                    w.id === webhook.id ? { ...w, is_active: !w.is_active } : w
                )
            )
        } catch (err) {
            console.error("Failed to toggle webhook:", err)
        }
    }

    const handleTest = async (webhookId: string) => {
        try {
            setTesting(webhookId)
            setTestResult(null)
            const userId = localStorage.getItem("user_id") || "current"
            const result = await apiClient.post<TestWebhookResponse>(
                `/integration/webhooks/${webhookId}/test?user_id=${userId}`,
                { event_type: "test.ping" }
            )
            setTestResult(result)
        } catch (err) {
            setTestResult({ success: false, error: "Failed to send test webhook" })
        } finally {
            setTesting(null)
        }
    }

    const toggleEvent = (event: string) => {
        setSelectedEvents((prev) =>
            prev.includes(event)
                ? prev.filter((e) => e !== event)
                : [...prev, event]
        )
    }

    const toggleCategory = (category: string) => {
        const categoryEvents = WEBHOOK_EVENTS.filter((e) => e.category === category).map((e) => e.value)
        const allSelected = categoryEvents.every((e) => selectedEvents.includes(e))

        if (allSelected) {
            setSelectedEvents((prev) => prev.filter((e) => !categoryEvents.includes(e)))
        } else {
            setSelectedEvents((prev) => Array.from(new Set([...prev, ...categoryEvents])))
        }
    }

    const toggleExpandWebhook = (webhookId: string) => {
        if (expandedWebhook === webhookId) {
            setExpandedWebhook(null)
        } else {
            setExpandedWebhook(webhookId)
            if (!deliveries[webhookId]) {
                loadDeliveries(webhookId)
            }
        }
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Settings", href: "/dashboard/settings" },
                    { label: "Webhooks" },
                ]}
            >
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold flex items-center gap-2">
                                <Webhook className="h-8 w-8" />
                                Webhooks
                            </h1>
                            <p className="text-muted-foreground">
                                Configure webhook endpoints for real-time notifications
                            </p>
                        </div>
                        <Skeleton className="h-10 w-36" />
                    </div>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="p-6">
                            <div className="space-y-4">
                                {[...Array(2)].map((_, i) => (
                                    <div key={i} className="p-4 border rounded-lg">
                                        <div className="flex items-center gap-4">
                                            <Skeleton className="h-12 w-12 rounded-lg" />
                                            <div className="flex-1">
                                                <Skeleton className="h-4 w-32 mb-2" />
                                                <Skeleton className="h-3 w-64" />
                                            </div>
                                            <Skeleton className="h-6 w-12" />
                                        </div>
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
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Settings", href: "/dashboard/settings" },
                { label: "Webhooks" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Webhook className="h-8 w-8" />
                            Webhooks
                        </h1>
                        <p className="text-muted-foreground">
                            Configure webhook endpoints for real-time notifications
                        </p>
                    </div>
                    <Button onClick={openCreateDialog}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Webhook
                    </Button>
                </div>

                {/* Webhooks List */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Your Webhooks</CardTitle>
                        <CardDescription>
                            Webhooks send HTTP POST requests to your server when events occur. Use them to integrate with external systems.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {webhooks.length === 0 ? (
                            <div className="flex items-center gap-4 p-4 border rounded-lg">
                                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                    <Webhook className="h-6 w-6 text-primary" />
                                </div>
                                <div>
                                    <p className="font-medium">No webhooks configured</p>
                                    <p className="text-sm text-muted-foreground">
                                        Add a webhook using the button above to receive real-time notifications
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {webhooks.map((webhook) => (
                                    <Collapsible
                                        key={webhook.id}
                                        open={expandedWebhook === webhook.id}
                                        onOpenChange={() => toggleExpandWebhook(webhook.id)}
                                    >
                                        <div className="border rounded-lg">
                                            <div className="flex items-center gap-4 p-4">
                                                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                                    <Webhook className="h-6 w-6 text-primary" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <p className="font-semibold">{webhook.name}</p>
                                                        {webhook.is_active ? (
                                                            <Badge variant="default" className="bg-green-500 text-xs">
                                                                Active
                                                            </Badge>
                                                        ) : (
                                                            <Badge variant="secondary" className="text-xs">
                                                                Inactive
                                                            </Badge>
                                                        )}
                                                        {webhook.failed_deliveries > 0 && (
                                                            <Badge variant="destructive" className="text-xs">
                                                                {webhook.failed_deliveries} failures
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-muted-foreground truncate mt-1">
                                                        {webhook.url}
                                                    </p>
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {webhook.events.slice(0, 3).map((event) => (
                                                            <Badge key={event} variant="outline" className="text-xs">
                                                                {event}
                                                            </Badge>
                                                        ))}
                                                        {webhook.events.length > 3 && (
                                                            <Badge variant="outline" className="text-xs">
                                                                +{webhook.events.length - 3} more
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Switch
                                                        checked={webhook.is_active}
                                                        onCheckedChange={() => handleToggleActive(webhook)}
                                                    />
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleTest(webhook.id)}
                                                        disabled={testing === webhook.id}
                                                    >
                                                        {testing === webhook.id ? (
                                                            <Loader2 className="h-4 w-4 animate-spin" />
                                                        ) : (
                                                            <TestTube className="h-4 w-4" />
                                                        )}
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => openEditDialog(webhook)}
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => {
                                                            setWebhookToDelete(webhook)
                                                            setDeleteDialogOpen(true)
                                                        }}
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive" />
                                                    </Button>
                                                    <CollapsibleTrigger asChild>
                                                        <Button variant="ghost" size="icon">
                                                            {expandedWebhook === webhook.id ? (
                                                                <ChevronUp className="h-4 w-4" />
                                                            ) : (
                                                                <ChevronDown className="h-4 w-4" />
                                                            )}
                                                        </Button>
                                                    </CollapsibleTrigger>
                                                </div>
                                            </div>
                                            <CollapsibleContent>
                                                <div className="border-t p-4 bg-muted/30">
                                                    <div className="flex items-center justify-between mb-3">
                                                        <h4 className="font-medium text-sm">Recent Deliveries</h4>
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => loadDeliveries(webhook.id)}
                                                            disabled={loadingDeliveries === webhook.id}
                                                        >
                                                            {loadingDeliveries === webhook.id ? (
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            ) : (
                                                                <RefreshCw className="h-4 w-4" />
                                                            )}
                                                        </Button>
                                                    </div>
                                                    {loadingDeliveries === webhook.id ? (
                                                        <div className="space-y-2">
                                                            {[...Array(3)].map((_, i) => (
                                                                <Skeleton key={i} className="h-12 w-full" />
                                                            ))}
                                                        </div>
                                                    ) : deliveries[webhook.id]?.length === 0 ? (
                                                        <p className="text-sm text-muted-foreground text-center py-4">
                                                            No deliveries yet
                                                        </p>
                                                    ) : (
                                                        <div className="space-y-2">
                                                            {deliveries[webhook.id]?.slice(0, 5).map((delivery) => (
                                                                <div
                                                                    key={delivery.id}
                                                                    className="flex items-center gap-3 p-3 bg-background rounded border"
                                                                >
                                                                    {delivery.status === "success" ? (
                                                                        <Check className="h-4 w-4 text-green-500" />
                                                                    ) : (
                                                                        <X className="h-4 w-4 text-red-500" />
                                                                    )}
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {delivery.event_type}
                                                                    </Badge>
                                                                    <span className="text-xs text-muted-foreground">
                                                                        {delivery.response_status || "No response"}
                                                                    </span>
                                                                    {delivery.response_time_ms && (
                                                                        <span className="text-xs text-muted-foreground">
                                                                            {delivery.response_time_ms}ms
                                                                        </span>
                                                                    )}
                                                                    <span className="text-xs text-muted-foreground ml-auto">
                                                                        {formatDate(delivery.created_at)}
                                                                    </span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </CollapsibleContent>
                                        </div>
                                    </Collapsible>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>


            {/* Create/Edit Webhook Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingWebhook ? "Edit Webhook" : "Add Webhook"}
                        </DialogTitle>
                        <DialogDescription>
                            Configure the webhook endpoint and select which events to subscribe to
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="webhookName">Name</Label>
                            <Input
                                id="webhookName"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g., Production Webhook"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="webhookUrl">Endpoint URL</Label>
                            <Input
                                id="webhookUrl"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://your-server.com/webhook"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Events</Label>
                            <div className="max-h-64 overflow-y-auto border rounded-lg p-3 space-y-4">
                                {EVENT_CATEGORIES.map((category) => {
                                    const categoryEvents = WEBHOOK_EVENTS.filter((e) => e.category === category)
                                    const allSelected = categoryEvents.every((e) => selectedEvents.includes(e.value))
                                    const someSelected = categoryEvents.some((e) => selectedEvents.includes(e.value))

                                    return (
                                        <div key={category}>
                                            <div
                                                className="flex items-center space-x-2 mb-2 cursor-pointer"
                                                onClick={() => toggleCategory(category)}
                                            >
                                                <Checkbox
                                                    checked={allSelected}
                                                    className={someSelected && !allSelected ? "opacity-50" : ""}
                                                />
                                                <span className="font-medium text-sm">{category}</span>
                                            </div>
                                            <div className="ml-6 space-y-1">
                                                {categoryEvents.map((event) => (
                                                    <div
                                                        key={event.value}
                                                        className="flex items-center space-x-2 cursor-pointer py-1"
                                                        onClick={() => toggleEvent(event.value)}
                                                    >
                                                        <Checkbox
                                                            checked={selectedEvents.includes(event.value)}
                                                        />
                                                        <span className="text-sm">{event.label}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                        {testResult && (
                            <Alert variant={testResult.success ? "default" : "destructive"}>
                                {testResult.success ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                                <AlertDescription>
                                    {testResult.success
                                        ? `Test webhook sent successfully! (${testResult.response_time_ms}ms)`
                                        : testResult.error || "Test failed"
                                    }
                                </AlertDescription>
                            </Alert>
                        )}
                    </div>
                    <DialogFooter className="flex-col sm:flex-row gap-2">
                        {editingWebhook && (
                            <Button
                                variant="outline"
                                onClick={() => handleTest(editingWebhook.id)}
                                disabled={testing !== null}
                            >
                                {testing ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    <TestTube className="mr-2 h-4 w-4" />
                                )}
                                Test
                            </Button>
                        )}
                        <div className="flex gap-2 ml-auto">
                            <Button variant="outline" onClick={() => setDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                {editingWebhook ? "Save Changes" : "Create Webhook"}
                            </Button>
                        </div>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Webhook</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete &quot;{webhookToDelete?.name}&quot;? This action cannot be
                            undone and you will stop receiving notifications at this endpoint.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Delete Webhook
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </DashboardLayout>
    )
}
