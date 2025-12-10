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
import { apiClient } from "@/lib/api/client"

interface ApiKey {
    id: string
    name: string
    key_prefix: string
    scopes: string[]
    last_used_at?: string
    expires_at?: string
    created_at: string
    is_active: boolean
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
    { value: "write:accounts", label: "Write Accounts", description: "Manage YouTube account connections" },
    { value: "read:videos", label: "Read Videos", description: "View video library and metadata" },
    { value: "write:videos", label: "Write Videos", description: "Upload and manage videos" },
    { value: "read:streams", label: "Read Streams", description: "View live stream information" },
    { value: "write:streams", label: "Write Streams", description: "Create and manage live streams" },
    { value: "read:analytics", label: "Read Analytics", description: "Access analytics data" },
    { value: "read:billing", label: "Read Billing", description: "View billing and usage information" },
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
                                    <div
                                        key={key.id}
                                        className={`flex items-center gap-4 p-4 border rounded-lg ${isExpired(key.expires_at) || !key.is_active ? "opacity-60 bg-muted/30" : ""
                                            }`}
                                    >
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
                                        <div className="flex items-center gap-3">
                                            {key.expires_at && key.is_active && !isExpired(key.expires_at) && (
                                                <span className="text-xs text-muted-foreground whitespace-nowrap">
                                                    Expires {formatDate(key.expires_at)}
                                                </span>
                                            )}
                                            {key.is_active && (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        setKeyToDelete(key)
                                                        setDeleteDialogOpen(true)
                                                    }}
                                                >
                                                    <Trash2 className="h-4 w-4 mr-1" />
                                                    Revoke
                                                </Button>
                                            )}
                                        </div>
                                    </div>
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
