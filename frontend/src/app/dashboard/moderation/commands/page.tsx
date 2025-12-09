"use client"

import { useState, useEffect } from "react"
import {
    Plus,
    Search,
    Edit,
    Trash2,
    Terminal,
    Loader2,
    Hash,
    Users,
    Clock,
    BarChart3,
} from "lucide-react"
import { DashboardLayout } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
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
import { moderationApi, type CustomCommand, type CreateCustomCommandRequest } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

const USER_LEVELS = [
    { value: "everyone", label: "Everyone", description: "All viewers can use" },
    { value: "subscriber", label: "Subscribers", description: "Subscribers only" },
    { value: "moderator", label: "Moderators", description: "Moderators only" },
    { value: "owner", label: "Owner", description: "Channel owner only" },
] as const

export default function CustomCommandsPage() {
    const [commands, setCommands] = useState<CustomCommand[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingCommand, setEditingCommand] = useState<CustomCommand | null>(null)
    const [saving, setSaving] = useState(false)

    // Form state
    const [formData, setFormData] = useState<CreateCustomCommandRequest>({
        account_id: "",
        trigger: "",
        response: "",
        description: "",
        cooldown: 5,
        user_level: "everyone",
        enabled: true,
    })

    useEffect(() => {
        loadAccounts()
        loadCommands()
    }, [accountFilter])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadCommands = async () => {
        try {
            setLoading(true)
            const data = await moderationApi.getCustomCommands(
                accountFilter !== "all" ? accountFilter : undefined
            )
            setCommands(data)
        } catch (error) {
            console.error("Failed to load commands:", error)
        } finally {
            setLoading(false)
        }
    }

    const filteredCommands = commands.filter((cmd) => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            cmd.trigger.toLowerCase().includes(query) ||
            cmd.response.toLowerCase().includes(query) ||
            cmd.description?.toLowerCase().includes(query)
        )
    })

    const openCreateDialog = () => {
        setEditingCommand(null)
        setFormData({
            account_id: accounts[0]?.id || "",
            trigger: "",
            response: "",
            description: "",
            cooldown: 5,
            user_level: "everyone",
            enabled: true,
        })
        setDialogOpen(true)
    }

    const openEditDialog = (command: CustomCommand) => {
        setEditingCommand(command)
        setFormData({
            account_id: command.account_id,
            trigger: command.trigger,
            response: command.response,
            description: command.description || "",
            cooldown: command.cooldown,
            user_level: command.user_level,
            enabled: command.enabled,
        })
        setDialogOpen(true)
    }

    const handleSave = async () => {
        if (!formData.trigger || !formData.response || !formData.account_id) {
            alert("Please fill in all required fields")
            return
        }

        // Ensure trigger starts with !
        const trigger = formData.trigger.startsWith("!")
            ? formData.trigger
            : `!${formData.trigger}`

        try {
            setSaving(true)
            if (editingCommand) {
                await moderationApi.updateCustomCommand(editingCommand.id, {
                    ...formData,
                    trigger,
                })
            } else {
                await moderationApi.createCustomCommand({
                    ...formData,
                    trigger,
                })
            }
            setDialogOpen(false)
            loadCommands()
        } catch (error) {
            console.error("Failed to save command:", error)
            alert("Failed to save command")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (commandId: string) => {
        if (!confirm("Are you sure you want to delete this command?")) return
        try {
            await moderationApi.deleteCustomCommand(commandId)
            loadCommands()
        } catch (error) {
            console.error("Failed to delete command:", error)
        }
    }

    const handleToggle = async (commandId: string, enabled: boolean) => {
        try {
            await moderationApi.toggleCustomCommand(commandId, enabled)
            setCommands((prev) =>
                prev.map((cmd) => (cmd.id === commandId ? { ...cmd, enabled } : cmd))
            )
        } catch (error) {
            console.error("Failed to toggle command:", error)
        }
    }

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    const getUserLevelBadge = (level: CustomCommand["user_level"]) => {
        const variants: Record<string, "default" | "secondary" | "outline"> = {
            everyone: "outline",
            subscriber: "secondary",
            moderator: "default",
            owner: "default",
        }
        return <Badge variant={variants[level]}>{level}</Badge>
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Moderation" },
                { label: "Commands" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Terminal className="h-8 w-8" />
                            Custom Commands
                        </h1>
                        <p className="text-muted-foreground">
                            Create custom chat commands for your live streams
                        </p>
                    </div>
                    <Button
                        onClick={openCreateDialog}
                        className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                    >
                        <Plus className="mr-2 h-4 w-4" />
                        Add Command
                    </Button>
                </div>

                {/* Filters */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center">
                            <div className="relative flex-1 max-w-md">
                                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                <Input
                                    placeholder="Search commands..."
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

                {/* Commands List */}
                {loading ? (
                    <div className="space-y-4">
                        {[...Array(3)].map((_, i) => (
                            <Card key={i} className="border-0 shadow-lg">
                                <CardContent className="p-6">
                                    <div className="flex items-center gap-4">
                                        <Skeleton className="h-10 w-10 rounded-lg" />
                                        <div className="flex-1">
                                            <Skeleton className="h-4 w-32 mb-2" />
                                            <Skeleton className="h-3 w-48" />
                                        </div>
                                        <Skeleton className="h-6 w-16" />
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : filteredCommands.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="py-12 text-center">
                            <Terminal className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No custom commands</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchQuery
                                    ? "No commands match your search"
                                    : "Create your first custom command for chat interaction"}
                            </p>
                            <Button onClick={openCreateDialog}>
                                <Plus className="mr-2 h-4 w-4" />
                                Add Command
                            </Button>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-4">
                        {filteredCommands.map((command) => (
                            <Card key={command.id} className="border-0 shadow-lg">
                                <CardContent className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                            <Hash className="h-5 w-5 text-primary" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <code className="text-lg font-semibold bg-muted px-2 py-0.5 rounded">
                                                    {command.trigger}
                                                </code>
                                                {getUserLevelBadge(command.user_level)}
                                                {command.cooldown > 0 && (
                                                    <Badge variant="outline" className="text-xs">
                                                        <Clock className="h-3 w-3 mr-1" />
                                                        {command.cooldown}s cooldown
                                                    </Badge>
                                                )}
                                            </div>
                                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                                {command.response}
                                            </p>
                                            {command.description && (
                                                <p className="text-xs text-muted-foreground mt-1 italic">
                                                    {command.description}
                                                </p>
                                            )}
                                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                <span>{getAccountName(command.account_id)}</span>
                                                <span className="flex items-center gap-1">
                                                    <BarChart3 className="h-3 w-3" />
                                                    {command.use_count} uses
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Switch
                                                checked={command.enabled}
                                                onCheckedChange={(checked) =>
                                                    handleToggle(command.id, checked)
                                                }
                                            />
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => openEditDialog(command)}
                                            >
                                                <Edit className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleDelete(command.id)}
                                            >
                                                <Trash2 className="h-4 w-4 text-destructive" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>

            {/* Add/Edit Command Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingCommand ? "Edit Command" : "Create Custom Command"}
                        </DialogTitle>
                        <DialogDescription>
                            Configure a custom chat command that viewers can trigger during streams.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Account</Label>
                            <Select
                                value={formData.account_id}
                                onValueChange={(value) =>
                                    setFormData({ ...formData, account_id: value })
                                }
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
                            <Label>Command Trigger</Label>
                            <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">!</span>
                                <Input
                                    placeholder="command"
                                    value={formData.trigger.replace(/^!/, "")}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            trigger: e.target.value.replace(/^!/, ""),
                                        })
                                    }
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Viewers will type !{formData.trigger || "command"} in chat
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>Response</Label>
                            <Textarea
                                placeholder="Enter the response message..."
                                value={formData.response}
                                onChange={(e) =>
                                    setFormData({ ...formData, response: e.target.value })
                                }
                                rows={3}
                            />
                            <p className="text-xs text-muted-foreground">
                                Use {"{user}"} for username, {"{channel}"} for channel name
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>Description (optional)</Label>
                            <Input
                                placeholder="Brief description of what this command does"
                                value={formData.description || ""}
                                onChange={(e) =>
                                    setFormData({ ...formData, description: e.target.value })
                                }
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>User Level</Label>
                                <Select
                                    value={formData.user_level}
                                    onValueChange={(value: CustomCommand["user_level"]) =>
                                        setFormData({ ...formData, user_level: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {USER_LEVELS.map((level) => (
                                            <SelectItem key={level.value} value={level.value}>
                                                <div className="flex items-center gap-2">
                                                    <Users className="h-4 w-4" />
                                                    <span>{level.label}</span>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>Cooldown (seconds)</Label>
                                <Select
                                    value={String(formData.cooldown)}
                                    onValueChange={(value) =>
                                        setFormData({ ...formData, cooldown: parseInt(value) })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="0">No cooldown</SelectItem>
                                        <SelectItem value="5">5 seconds</SelectItem>
                                        <SelectItem value="10">10 seconds</SelectItem>
                                        <SelectItem value="30">30 seconds</SelectItem>
                                        <SelectItem value="60">1 minute</SelectItem>
                                        <SelectItem value="300">5 minutes</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="flex items-center justify-between">
                            <Label>Enable Command</Label>
                            <Switch
                                checked={formData.enabled}
                                onCheckedChange={(checked) =>
                                    setFormData({ ...formData, enabled: checked })
                                }
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingCommand ? "Save Changes" : "Create Command"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
