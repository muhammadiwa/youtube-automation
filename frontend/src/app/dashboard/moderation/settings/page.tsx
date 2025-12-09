"use client"

import { useState, useEffect } from "react"
import {
    Plus,
    Search,
    Edit,
    Trash2,
    Shield,
    AlertTriangle,
    Link2,
    Type,
    Hash,
    MessageSquare,
    Loader2,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { moderationApi, type ModerationRule, type CreateModerationRuleRequest } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

const RULE_TYPES = [
    { value: "keyword", label: "Keyword", icon: Type, description: "Block specific words or phrases" },
    { value: "regex", label: "Regex", icon: Hash, description: "Advanced pattern matching" },
    { value: "spam", label: "Spam", icon: MessageSquare, description: "Detect repetitive messages" },
    { value: "caps", label: "Caps Lock", icon: Type, description: "Limit excessive capitals" },
    { value: "links", label: "Links", icon: Link2, description: "Block URLs and links" },
    { value: "emotes", label: "Emotes", icon: MessageSquare, description: "Limit emote spam" },
] as const

const ACTIONS = [
    { value: "delete", label: "Delete", description: "Remove the message" },
    { value: "hide", label: "Hide", description: "Hide from public view" },
    { value: "timeout", label: "Timeout", description: "Temporarily mute user" },
    { value: "ban", label: "Ban", description: "Permanently ban user" },
    { value: "flag", label: "Flag", description: "Flag for review" },
] as const

export default function ModerationSettingsPage() {
    const [rules, setRules] = useState<ModerationRule[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingRule, setEditingRule] = useState<ModerationRule | null>(null)
    const [saving, setSaving] = useState(false)

    // Form state
    const [formData, setFormData] = useState<CreateModerationRuleRequest>({
        account_id: "",
        name: "",
        type: "keyword",
        pattern: "",
        action: "delete",
        timeout_duration: 60,
        enabled: true,
    })

    useEffect(() => {
        loadAccounts()
        loadRules()
    }, [accountFilter])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadRules = async () => {
        try {
            setLoading(true)
            const data = await moderationApi.getRules(accountFilter !== "all" ? accountFilter : undefined)
            setRules(data)
        } catch (error) {
            console.error("Failed to load rules:", error)
        } finally {
            setLoading(false)
        }
    }

    const filteredRules = rules.filter((rule) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            rule.name.toLowerCase().includes(query) ||
            rule.pattern.toLowerCase().includes(query)
        )
    })

    const openCreateDialog = () => {
        setEditingRule(null)
        setFormData({
            account_id: accounts[0]?.id || "",
            name: "",
            type: "keyword",
            pattern: "",
            action: "delete",
            timeout_duration: 60,
            enabled: true,
        })
        setDialogOpen(true)
    }

    const openEditDialog = (rule: ModerationRule) => {
        setEditingRule(rule)
        setFormData({
            account_id: rule.account_id,
            name: rule.name,
            type: rule.type,
            pattern: rule.pattern,
            action: rule.action,
            timeout_duration: rule.timeout_duration || 60,
            enabled: rule.enabled,
        })
        setDialogOpen(true)
    }

    const handleSave = async () => {
        if (!formData.name || !formData.pattern || !formData.account_id) {
            alert("Please fill in all required fields")
            return
        }

        try {
            setSaving(true)
            if (editingRule) {
                await moderationApi.updateRule(editingRule.id, formData)
            } else {
                await moderationApi.createRule(formData)
            }
            setDialogOpen(false)
            loadRules()
        } catch (error) {
            console.error("Failed to save rule:", error)
            alert("Failed to save rule")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (ruleId: string) => {
        if (!confirm("Are you sure you want to delete this rule?")) return
        try {
            await moderationApi.deleteRule(ruleId)
            loadRules()
        } catch (error) {
            console.error("Failed to delete rule:", error)
        }
    }

    const handleToggle = async (ruleId: string, enabled: boolean) => {
        try {
            await moderationApi.toggleRule(ruleId, enabled)
            setRules((prev) =>
                prev.map((rule) => (rule.id === ruleId ? { ...rule, enabled } : rule))
            )
        } catch (error) {
            console.error("Failed to toggle rule:", error)
        }
    }

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    const getRuleTypeIcon = (type: ModerationRule["type"]) => {
        const ruleType = RULE_TYPES.find((t) => t.value === type)
        return ruleType?.icon || Shield
    }

    const getActionBadge = (action: ModerationRule["action"]) => {
        const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
            delete: "destructive",
            ban: "destructive",
            timeout: "default",
            hide: "secondary",
            flag: "outline",
        }
        return <Badge variant={variants[action] || "default"}>{action}</Badge>
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Moderation" },
                { label: "Settings" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Shield className="h-8 w-8" />
                            Moderation Settings
                        </h1>
                        <p className="text-muted-foreground">
                            Configure automated chat moderation rules for your streams
                        </p>
                    </div>
                    <Button
                        onClick={openCreateDialog}
                        className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        Add Rule
                    </Button>
                </div>

                {/* Filters */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search rules..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                            <Select value={accountFilter} onValueChange={setAccountFilter}>
                                <SelectTrigger className="w-[200px]">
                                    <SelectValue placeholder="All Accounts" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Accounts</SelectItem>
                                    {accounts.map((account) => (
                                        <SelectItem key={account.id} value={account.id}>
                                            {account.channelTitle}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Rules List */}
                {loading ? (
                    <div className="space-y-4">
                        {[...Array(3)].map((_, i) => (
                            <Card key={i} className="border-0 shadow-lg">
                                <CardContent className="p-6">
                                    <div className="flex items-center gap-4">
                                        <Skeleton className="h-10 w-10 rounded-lg" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-48 mb-2" />
                                            <Skeleton className="h-3 w-32" />
                                        </div>
                                        <Skeleton className="h-6 w-16" />
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : filteredRules.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <Shield className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No moderation rules</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchQuery
                                    ? "No rules match your search"
                                    : "Create your first moderation rule to protect your chat"}
                            </p>
                            <Button onClick={openCreateDialog}>
                                <Plus className="mr-2 h-4 w-4" />
                                Add Rule
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-4">
                        {filteredRules.map((rule) => {
                            const Icon = getRuleTypeIcon(rule.type)
                            return (
                                <Card key={rule.id} className="border-0 shadow-lg">
                                    <CardContent className="p-6">
                                        <div className="flex items-center gap-4">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                                <Icon className="h-5 w-5 text-primary" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <h3 className="font-semibold">{rule.name}</h3>
                                                    {getActionBadge(rule.action)}
                                                    {rule.action === "timeout" && rule.timeout_duration && (
                                                        <Badge variant="outline">
                                                            {rule.timeout_duration}s
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate">
                                                    {rule.type}: <code className="bg-muted px-1 rounded">{rule.pattern}</code>
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {getAccountName(rule.account_id)}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={rule.enabled}
                                                    onCheckedChange={(checked) => handleToggle(rule.id, checked)}
                                                />
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => openEditDialog(rule)}
                                                >
                                                    <Edit className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleDelete(rule.id)}
                                                >
                                                    <Trash2 className="h-4 w-4 text-destructive" />
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Add/Edit Rule Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingRule ? "Edit Rule" : "Create Moderation Rule"}
                        </DialogTitle>
                        <DialogDescription>
                            Configure how this rule should detect and handle chat violations.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Account</Label>
                            <Select
                                value={formData.account_id}
                                onValueChange={(value) => setFormData({ ...formData, account_id: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select account" />
                                </SelectTrigger>
                                <SelectContent>
                                    {accounts.map((account) => (
                                        <SelectItem key={account.id} value={account.id}>
                                            {account.channelTitle}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Rule Name</Label>
                            <Input
                                placeholder="e.g., Block spam links"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Rule Type</Label>
                            <Select
                                value={formData.type}
                                onValueChange={(value: ModerationRule["type"]) =>
                                    setFormData({ ...formData, type: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {RULE_TYPES.map((type) => (
                                        <SelectItem key={type.value} value={type.value}>
                                            <div className="flex items-center gap-2">
                                                <type.icon className="h-4 w-4" />
                                                <span>{type.label}</span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-muted-foreground">
                                {RULE_TYPES.find((t) => t.value === formData.type)?.description}
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>Pattern</Label>
                            <Textarea
                                placeholder={
                                    formData.type === "regex"
                                        ? "Enter regex pattern..."
                                        : "Enter keywords (comma separated)..."
                                }
                                value={formData.pattern}
                                onChange={(e) => setFormData({ ...formData, pattern: e.target.value })}
                                rows={3}
                            />
                            {formData.type === "keyword" && (
                                <p className="text-xs text-muted-foreground">
                                    Separate multiple keywords with commas
                                </p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label>Action</Label>
                            <Select
                                value={formData.action}
                                onValueChange={(value: ModerationRule["action"]) =>
                                    setFormData({ ...formData, action: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {ACTIONS.map((action) => (
                                        <SelectItem key={action.value} value={action.value}>
                                            <div>
                                                <span>{action.label}</span>
                                                <span className="text-xs text-muted-foreground ml-2">
                                                    - {action.description}
                                                </span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {formData.action === "timeout" && (
                            <div className="space-y-2">
                                <Label>Timeout Duration (seconds)</Label>
                                <Select
                                    value={String(formData.timeout_duration)}
                                    onValueChange={(value) =>
                                        setFormData({ ...formData, timeout_duration: parseInt(value) })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="60">1 minute</SelectItem>
                                        <SelectItem value="300">5 minutes</SelectItem>
                                        <SelectItem value="600">10 minutes</SelectItem>
                                        <SelectItem value="1800">30 minutes</SelectItem>
                                        <SelectItem value="3600">1 hour</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}

                        <div className="flex items-center justify-between">
                            <Label>Enable Rule</Label>
                            <Switch
                                checked={formData.enabled}
                                onCheckedChange={(checked) => setFormData({ ...formData, enabled: checked })}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingRule ? "Save Changes" : "Create Rule"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
