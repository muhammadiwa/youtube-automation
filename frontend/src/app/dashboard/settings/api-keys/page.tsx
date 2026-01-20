"use client"

import { useState, useEffect } from "react"
import {
    Key,
    Plus,
    Copy,
    Trash2,
    Loader2,
    Check,
    Eye,
    EyeOff,
    Clock,
    AlertTriangle,
    Activity,
    ChevronDown,
    ChevronUp,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
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
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
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
import { Progress } from "@/components/ui/progress"
import { apiClient } from "@/lib/api/client"

interface ApiKey {
    id: string
    name: string
    key_prefix: string
    scopes: string[]
    rate_limit_per_minute: number
    rate_limit_per_hour: number
    rate_limit_per_day: number
    total_requests: number
    last_used_at?: string
    expires_at?: string
    created_at: string
    is_active: boolean
}

interface RateLimitStatus {
    api_key_id: string
    minute_limit: number
    minute_used: number
    minute_remaining: number
    hour_limit: number
    hour_used: number
    hour_remaining: number
    day_limit: number
    day_used: number
    day_remaining: number
    is_rate_limited: boolean
    reset_at: string
}

interface CreateApiKeyResponse {
    id: string
    name: string
    key: string
    key_prefix: string
    scopes: string[]
    expires_at?: string
    created_at: string
}

const SCOPES = [
    { value: "read:accounts", label: "Read Accounts", description: "View connected YouTube accounts" },
    { value: "read:videos", label: "Read Videos", description: "View video library and metadata" },
    { value: "write:videos", label: "Write Videos", description: "Upload and manage videos" },
    { value: "read:streams", label: "Read Streams", description: "View live stream information" },
    { value: "write:streams", label: "Write Streams", description: "Create and manage live streams" },
    { value: "read:analytics", label: "Read Analytics", description: "Access analytics data" },
    { value: "read:comments", label: "Read Comments", description: "View comments" },
    { value: "write:comments", label: "Write Comments", description: "Post and manage comments" },
    { value: "admin:accounts", label: "Admin Accounts", description: "Full account management" },
    { value: "admin:webhooks", label: "Admin Webhooks", description: "Manage webhooks" },
    { value: "*", label: "Full Access", description: "Access to all resources" },
]

export default function ApiKeysPage() {
    const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
    const [loading, setLoading] = useState(true)
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(false)
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
    const [keyToDelete, setKeyToDelete] = useState<ApiKey | null>(null)
    const [creating, setCreating] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [copied, setCopied] = useState(false)
    const [error, setError] = useState("")

    // Form state
    const [keyName, setKeyName] = useState("")
    const [selectedScopes, setSelectedScopes] = useState<string[]>([])
    const [expiresIn, setExpiresIn] = useState<string>("never")

    // New key result
    const [newKey, setNewKey] = useState<CreateApiKeyResponse | null>(null)
    const [showKey, setShowKey] = useState(false)

    // Rate limit state
    const [expandedKey, setExpandedKey] = useState<string | null>(null)
    const [rateLimits, setRateLimits] = useState<Record<string, RateLimitStatus>>({})
    const [loadingRateLimits, setLoadingRateLimits] = useState<string | null>(null)

    useEffect(() => {
        loadApiKeys()
    }, [])

    const loadApiKeys = async () => {
        try {
            setLoading(true)
            // Get user_id from auth context or localStorage
            const userId = localStorage.getItem("user_id") || "current"
            const response = await apiClient.get<{ keys: ApiKey[] }>(`/integration/api-keys?user_id=${userId}`)
            setApiKeys(response.keys || [])
        } catch (error) {
            console.error("Failed to load API keys:", error)
            setApiKeys([])
        } finally {
            setLoading(false)
        }
    }

    const loadRateLimitStatus = async (keyId: string) => {
        try {
            setLoadingRateLimits(keyId)
            const userId = localStorage.getItem("user_id") || "current"
            const response = await apiClient.get<RateLimitStatus>(`/integration/api-keys/${keyId}/rate-limit?user_id=${userId}`)
            setRateLimits((prev) => ({ ...prev, [keyId]: response }))
        } catch (error) {
            console.error("Failed to load rate limit status:", error)
        } finally {
            setLoadingRateLimits(null)
        }
    }

    const toggleExpandKey = (keyId: string) => {
        if (expandedKey === keyId) {
            setExpandedKey(null)
        } else {
            setExpandedKey(keyId)
            if (!rateLimits[keyId]) {
                loadRateLimitStatus(keyId)
            }
        }
    }

    const formatResetTime = (resetAt: string) => {
        const reset = new Date(resetAt)
        const now = new Date()
        const diffMs = reset.getTime() - now.getTime()
        const diffSecs = Math.max(0, Math.floor(diffMs / 1000))

        if (diffSecs < 60) {
            return `${diffSecs}s`
        }
        const diffMins = Math.floor(diffSecs / 60)
        return `${diffMins}m ${diffSecs % 60}s`
    }

    const getUsagePercentage = (used: number, limit: number) => {
        if (limit === 0) return 0
        return Math.min(100, (used / limit) * 100)
    }

    const getUsageColor = (percentage: number) => {
        if (percentage >= 90) return "bg-red-500"
        if (percentage >= 70) return "bg-yellow-500"
        return "bg-green-500"
    }

    const openCreateDialog = () => {
        setKeyName("")
        setSelectedScopes([])
        setExpiresIn("never")
        setError("")
        setCreateDialogOpen(true)
    }

    const handleCreateKey = async () => {
        if (!keyName.trim()) {
            setError("Please enter a key name")
            return
        }
        if (selectedScopes.length === 0) {
            setError("Please select at least one permission")
            return
        }

        try {
            setCreating(true)
            setError("")
            const userId = localStorage.getItem("user_id") || "current"
            const result = await apiClient.post<CreateApiKeyResponse>(`/integration/api-keys?user_id=${userId}`, {
                name: keyName.trim(),
                scopes: selectedScopes,
                expires_in_days: expiresIn === "never" ? null : parseInt(expiresIn),
            })
            setNewKey(result)
            setCreateDialogOpen(false)
            setNewKeyDialogOpen(true)
            loadApiKeys()
        } catch (err) {
            console.error("Failed to create API key:", err)
            setError("Failed to create API key. Please try again.")
        } finally {
            setCreating(false)
        }
    }

    const handleRevokeKey = async () => {
        if (!keyToDelete) return

        try {
            setDeleting(true)
            const userId = localStorage.getItem("user_id") || "current"
            await apiClient.post(`/integration/api-keys/${keyToDelete.id}/revoke?user_id=${userId}`, {
                reason: "User requested revocation"
            })
            setApiKeys((prev) => prev.filter((k) => k.id !== keyToDelete.id))
            setDeleteDialogOpen(false)
            setKeyToDelete(null)
        } catch (error) {
            console.error("Failed to revoke API key:", error)
        } finally {
            setDeleting(false)
        }
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const toggleScope = (scope: string) => {
        setSelectedScopes((prev) =>
            prev.includes(scope)
                ? prev.filter((s) => s !== scope)
                : [...prev, scope]
        )
    }

    const formatDate = (dateString?: string) => {
        if (!dateString) return "Never"
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        })
    }

    const isExpired = (expiresAt?: string) => {
        if (!expiresAt) return false
        return new Date(expiresAt) < new Date()
    }

    if (loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Settings", href: "/dashboard/settings" },
                    { label: "API Keys" },
                ]}
            >
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold flex items-center gap-2">
                                <Key className="h-8 w-8" />
                                API Keys
                            </h1>
                            <p className="text-muted-foreground">
                                Manage API keys for external integrations
                            </p>
                        </div>
                        <Skeleton className="h-10 w-32" />
                    </div>
                    <Card className="border-0 shadow-lg">
                        <CardContent className="p-6">
                            <div className="space-y-4">
                                {[...Array(3)].map((_, i) => (
                                    <div key={i} className="flex items-center gap-4 p-4 border rounded-lg">
                                        <Skeleton className="h-12 w-12 rounded-lg" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-32 mb-2" />
                                            <Skeleton className="h-3 w-48" />
                                        </div>
                                        <Skeleton className="h-8 w-20" />
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
                { label: "API Keys" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Key className="h-8 w-8" />
                            API Keys
                        </h1>
                        <p className="text-muted-foreground">
                            Manage API keys for external integrations
                        </p>
                    </div>
                    <Button onClick={openCreateDialog}>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Key
                    </Button>
                </div>

                {/* API Keys List */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Your API Keys</CardTitle>
                        <CardDescription>
                            API keys allow external applications to access your account. Keep them secure and never share them publicly.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {apiKeys.length === 0 ? (
                            <div className="flex items-center gap-4 p-4 border rounded-lg">
                                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                    <Key className="h-6 w-6 text-primary" />
                                </div>
                                <div>
                                    <p className="font-medium">No API keys yet</p>
                                    <p className="text-sm text-muted-foreground">
                                        Create your first API key using the button above
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {apiKeys.map((key) => (
                                    <Collapsible
                                        key={key.id}
                                        open={expandedKey === key.id}
                                        onOpenChange={() => key.is_active && toggleExpandKey(key.id)}
                                    >
                                        <div className={`border rounded-lg ${isExpired(key.expires_at) || !key.is_active ? "opacity-60 bg-muted/30" : ""}`}>
                                            <div className="flex items-center gap-4 p-4">
                                                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                                    <Key className="h-6 w-6 text-primary" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <p className="font-semibold">{key.name}</p>
                                                        {!key.is_active && (
                                                            <Badge variant="destructive" className="text-xs">
                                                                Revoked
                                                            </Badge>
                                                        )}
                                                        {isExpired(key.expires_at) && key.is_active && (
                                                            <Badge variant="destructive" className="text-xs">
                                                                Expired
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                                                        <code className="bg-muted px-2 py-0.5 rounded text-xs">
                                                            {key.key_prefix}...
                                                        </code>
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="h-3 w-3" />
                                                            {key.last_used_at
                                                                ? `Last used ${formatDate(key.last_used_at)}`
                                                                : "Never used"}
                                                        </span>
                                                        {key.total_requests > 0 && (
                                                            <span className="flex items-center gap-1">
                                                                <Activity className="h-3 w-3" />
                                                                {key.total_requests.toLocaleString()} requests
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex flex-wrap gap-1 mt-2">
                                                        {key.scopes.slice(0, 4).map((scope) => (
                                                            <Badge key={scope} variant="secondary" className="text-xs">
                                                                {scope}
                                                            </Badge>
                                                        ))}
                                                        {key.scopes.length > 4 && (
                                                            <Badge variant="secondary" className="text-xs">
                                                                +{key.scopes.length - 4} more
                                                            </Badge>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {key.expires_at && key.is_active && !isExpired(key.expires_at) && (
                                                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                                                            Expires {formatDate(key.expires_at)}
                                                        </span>
                                                    )}
                                                    {key.is_active && (
                                                        <>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={(e) => {
                                                                    e.stopPropagation()
                                                                    setKeyToDelete(key)
                                                                    setDeleteDialogOpen(true)
                                                                }}
                                                            >
                                                                <Trash2 className="h-4 w-4 mr-1" />
                                                                Revoke
                                                            </Button>
                                                            <CollapsibleTrigger asChild>
                                                                <Button variant="ghost" size="icon">
                                                                    {expandedKey === key.id ? (
                                                                        <ChevronUp className="h-4 w-4" />
                                                                    ) : (
                                                                        <ChevronDown className="h-4 w-4" />
                                                                    )}
                                                                </Button>
                                                            </CollapsibleTrigger>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                            <CollapsibleContent>
                                                <div className="border-t p-4 bg-muted/30">
                                                    <div className="flex items-center justify-between mb-3">
                                                        <h4 className="font-medium text-sm flex items-center gap-2">
                                                            <Activity className="h-4 w-4" />
                                                            Rate Limit Usage
                                                        </h4>
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => loadRateLimitStatus(key.id)}
                                                            disabled={loadingRateLimits === key.id}
                                                        >
                                                            {loadingRateLimits === key.id ? (
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            ) : (
                                                                "Refresh"
                                                            )}
                                                        </Button>
                                                    </div>
                                                    {loadingRateLimits === key.id ? (
                                                        <div className="space-y-3">
                                                            {[...Array(3)].map((_, i) => (
                                                                <Skeleton key={i} className="h-8 w-full" />
                                                            ))}
                                                        </div>
                                                    ) : rateLimits[key.id] ? (
                                                        <div className="space-y-4">
                                                            {rateLimits[key.id].is_rate_limited && (
                                                                <Alert variant="destructive" className="mb-4">
                                                                    <AlertTriangle className="h-4 w-4" />
                                                                    <AlertDescription>
                                                                        Rate limit exceeded. Resets in {formatResetTime(rateLimits[key.id].reset_at)}
                                                                    </AlertDescription>
                                                                </Alert>
                                                            )}
                                                            <div className="grid gap-4 md:grid-cols-3">
                                                                {/* Per Minute */}
                                                                <div className="space-y-2">
                                                                    <div className="flex justify-between text-sm">
                                                                        <span className="text-muted-foreground">Per Minute</span>
                                                                        <span className="font-medium">
                                                                            {rateLimits[key.id].minute_used} / {rateLimits[key.id].minute_limit}
                                                                        </span>
                                                                    </div>
                                                                    <Progress
                                                                        value={getUsagePercentage(rateLimits[key.id].minute_used, rateLimits[key.id].minute_limit)}
                                                                        className="h-2"
                                                                    />
                                                                    <p className="text-xs text-muted-foreground">
                                                                        {rateLimits[key.id].minute_remaining} remaining
                                                                    </p>
                                                                </div>
                                                                {/* Per Hour */}
                                                                <div className="space-y-2">
                                                                    <div className="flex justify-between text-sm">
                                                                        <span className="text-muted-foreground">Per Hour</span>
                                                                        <span className="font-medium">
                                                                            {rateLimits[key.id].hour_used} / {rateLimits[key.id].hour_limit}
                                                                        </span>
                                                                    </div>
                                                                    <Progress
                                                                        value={getUsagePercentage(rateLimits[key.id].hour_used, rateLimits[key.id].hour_limit)}
                                                                        className="h-2"
                                                                    />
                                                                    <p className="text-xs text-muted-foreground">
                                                                        {rateLimits[key.id].hour_remaining} remaining
                                                                    </p>
                                                                </div>
                                                                {/* Per Day */}
                                                                <div className="space-y-2">
                                                                    <div className="flex justify-between text-sm">
                                                                        <span className="text-muted-foreground">Per Day</span>
                                                                        <span className="font-medium">
                                                                            {rateLimits[key.id].day_used} / {rateLimits[key.id].day_limit}
                                                                        </span>
                                                                    </div>
                                                                    <Progress
                                                                        value={getUsagePercentage(rateLimits[key.id].day_used, rateLimits[key.id].day_limit)}
                                                                        className="h-2"
                                                                    />
                                                                    <p className="text-xs text-muted-foreground">
                                                                        {rateLimits[key.id].day_remaining} remaining
                                                                    </p>
                                                                </div>
                                                            </div>
                                                            <div className="text-xs text-muted-foreground mt-2">
                                                                Next reset: {new Date(rateLimits[key.id].reset_at).toLocaleTimeString()}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <p className="text-sm text-muted-foreground text-center py-4">
                                                            Click refresh to load rate limit status
                                                        </p>
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


            {/* Create Key Dialog */}
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Create API Key</DialogTitle>
                        <DialogDescription>
                            Create a new API key with specific permissions for your integration
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="keyName">Key Name</Label>
                            <Input
                                id="keyName"
                                value={keyName}
                                onChange={(e) => setKeyName(e.target.value)}
                                placeholder="e.g., Production API Key"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Expiration</Label>
                            <Select value={expiresIn} onValueChange={setExpiresIn}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="never">Never expires</SelectItem>
                                    <SelectItem value="30">30 days</SelectItem>
                                    <SelectItem value="90">90 days</SelectItem>
                                    <SelectItem value="180">180 days</SelectItem>
                                    <SelectItem value="365">1 year</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label>Permissions</Label>
                            <div className="grid gap-3 max-h-64 overflow-y-auto p-1">
                                {SCOPES.map((scope) => (
                                    <div
                                        key={scope.value}
                                        className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                                        onClick={() => toggleScope(scope.value)}
                                    >
                                        <Checkbox
                                            checked={selectedScopes.includes(scope.value)}
                                            onCheckedChange={() => toggleScope(scope.value)}
                                        />
                                        <div className="flex-1">
                                            <p className="text-sm font-medium">{scope.label}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {scope.description}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleCreateKey}
                            disabled={creating}
                        >
                            {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Key
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* New Key Created Dialog */}
            <Dialog open={newKeyDialogOpen} onOpenChange={setNewKeyDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Check className="h-5 w-5 text-green-500" />
                            API Key Created
                        </DialogTitle>
                        <DialogDescription>
                            Make sure to copy your API key now. You won&apos;t be able to see it again!
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                            <div className="flex items-start gap-2">
                                <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-yellow-600">
                                        This is the only time you&apos;ll see this key
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Store it securely. If you lose it, you&apos;ll need to create a new one.
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Your API Key</Label>
                            <div className="flex gap-2">
                                <div className="relative flex-1">
                                    <Input
                                        value={showKey ? newKey?.key || "" : "•".repeat(40)}
                                        readOnly
                                        className="font-mono pr-10"
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-0 top-0 h-full px-3"
                                        onClick={() => setShowKey(!showKey)}
                                    >
                                        {showKey ? (
                                            <EyeOff className="h-4 w-4" />
                                        ) : (
                                            <Eye className="h-4 w-4" />
                                        )}
                                    </Button>
                                </div>
                                <Button
                                    variant="outline"
                                    onClick={() => newKey && copyToClipboard(newKey.key)}
                                >
                                    {copied ? (
                                        <Check className="h-4 w-4" />
                                    ) : (
                                        <Copy className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            onClick={() => {
                                setNewKeyDialogOpen(false)
                                setNewKey(null)
                                setShowKey(false)
                            }}
                        >
                            Done
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to revoke &quot;{keyToDelete?.name}&quot;? This action cannot be
                            undone and any applications using this key will stop working immediately.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleRevokeKey}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Revoke Key
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </DashboardLayout>
    )
}
