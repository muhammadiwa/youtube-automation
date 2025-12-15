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
    Eye,
    Sparkles,
    CheckCircle2,
    MessageCircle,
    HelpCircle,
    Heart,
    Gamepad2,
    Info,
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

// Command Templates
interface CommandTemplate {
    id: string
    name: string
    description: string
    category: "info" | "social" | "fun" | "moderation"
    icon: typeof Terminal
    color: string
    commands: Omit<CreateCustomCommandRequest, "account_id">[]
}

const COMMAND_TEMPLATES: CommandTemplate[] = [
    {
        id: "basic-info",
        name: "Basic Info Commands",
        description: "Essential information commands for your stream",
        category: "info",
        icon: Info,
        color: "from-blue-500 to-blue-600",
        commands: [
            {
                trigger: "!help",
                response_text: "Available commands: !socials, !discord, !schedule, !donate. Type any command to learn more!",
                description: "Shows available commands",
                cooldown_seconds: 5,
                is_enabled: true,
            },
            {
                trigger: "!about",
                response_text: "Welcome to the stream! I'm a content creator who loves gaming and chatting with viewers. Thanks for stopping by! 🎮",
                description: "About the streamer",
                cooldown_seconds: 30,
                is_enabled: true,
            },
            {
                trigger: "!schedule",
                response_text: "📅 Stream Schedule: Mon, Wed, Fri at 7PM. Follow to get notified when I go live!",
                description: "Shows stream schedule",
                cooldown_seconds: 30,
                is_enabled: true,
            },
        ],
    },
    {
        id: "social-links",
        name: "Social Media Links",
        description: "Commands to share your social media profiles",
        category: "social",
        icon: Heart,
        color: "from-pink-500 to-pink-600",
        commands: [
            {
                trigger: "!socials",
                response_text: "Follow me on: Twitter @username | Instagram @username | TikTok @username",
                description: "All social media links",
                cooldown_seconds: 30,
                is_enabled: true,
            },
            {
                trigger: "!discord",
                response_text: "Join our Discord community: discord.gg/yourserver 🎮",
                description: "Discord server link",
                cooldown_seconds: 30,
                is_enabled: true,
            },
            {
                trigger: "!twitter",
                response_text: "Follow me on Twitter: twitter.com/username 🐦",
                description: "Twitter link",
                cooldown_seconds: 30,
                is_enabled: true,
            },
            {
                trigger: "!instagram",
                response_text: "Follow me on Instagram: instagram.com/username 📸",
                description: "Instagram link",
                cooldown_seconds: 30,
                is_enabled: true,
            },
        ],
    },
    {
        id: "engagement",
        name: "Viewer Engagement",
        description: "Fun commands to engage with your audience",
        category: "fun",
        icon: Gamepad2,
        color: "from-purple-500 to-purple-600",
        commands: [
            {
                trigger: "!hug",
                response_text: "🤗 {user} sends a warm hug to the chat! Group hug everyone!",
                description: "Send a virtual hug",
                cooldown_seconds: 10,
                is_enabled: true,
            },
            {
                trigger: "!love",
                response_text: "❤️ {user} spreads love in the chat! You're all amazing!",
                description: "Spread love",
                cooldown_seconds: 10,
                is_enabled: true,
            },
            {
                trigger: "!lurk",
                response_text: "👀 {user} is now lurking! Thanks for keeping the stream company!",
                description: "Lurk announcement",
                cooldown_seconds: 60,
                is_enabled: true,
            },
            {
                trigger: "!gg",
                response_text: "🎮 GG! Well played everyone!",
                description: "Good game",
                cooldown_seconds: 5,
                is_enabled: true,
            },
        ],
    },
    {
        id: "support",
        name: "Support & Donations",
        description: "Commands for viewer support options",
        category: "info",
        icon: Heart,
        color: "from-red-500 to-red-600",
        commands: [
            {
                trigger: "!donate",
                response_text: "💝 Support the stream: streamlabs.com/username - Every donation helps! Thank you!",
                description: "Donation link",
                cooldown_seconds: 60,
                is_enabled: true,
            },
            {
                trigger: "!merch",
                response_text: "👕 Check out the merch store: yourstore.com - Rep the community!",
                description: "Merchandise link",
                cooldown_seconds: 60,
                is_enabled: true,
            },
            {
                trigger: "!subscribe",
                response_text: "⭐ Subscribe to support the channel and get exclusive perks! Thanks for the support!",
                description: "Subscribe reminder",
                cooldown_seconds: 120,
                is_enabled: true,
            },
        ],
    },
    {
        id: "faq",
        name: "FAQ Commands",
        description: "Frequently asked questions",
        category: "info",
        icon: HelpCircle,
        color: "from-green-500 to-green-600",
        commands: [
            {
                trigger: "!pc",
                response_text: "🖥️ My PC specs: CPU: Ryzen 9 5900X | GPU: RTX 3080 | RAM: 32GB | Storage: 2TB NVMe",
                description: "PC specifications",
                cooldown_seconds: 60,
                is_enabled: true,
            },
            {
                trigger: "!setup",
                response_text: "🎙️ Streaming setup: Camera: Sony A6400 | Mic: Shure SM7B | Lights: Elgato Key Light",
                description: "Streaming setup",
                cooldown_seconds: 60,
                is_enabled: true,
            },
            {
                trigger: "!age",
                response_text: "I'm old enough to know better, young enough to do it anyway! 😄",
                description: "Age question",
                cooldown_seconds: 120,
                is_enabled: true,
            },
            {
                trigger: "!game",
                response_text: "🎮 Currently playing: Check the stream title for the current game!",
                description: "Current game",
                cooldown_seconds: 30,
                is_enabled: true,
            },
        ],
    },
    {
        id: "mod-commands",
        name: "Moderator Commands",
        description: "Commands for stream moderators",
        category: "moderation",
        icon: Users,
        color: "from-yellow-500 to-yellow-600",
        commands: [
            {
                trigger: "!rules",
                response_text: "📜 Chat Rules: 1. Be respectful 2. No spam 3. No self-promo 4. Keep it family-friendly 5. Have fun!",
                description: "Chat rules",
                cooldown_seconds: 60,
                moderator_only: false,
                is_enabled: true,
            },
            {
                trigger: "!warn",
                response_text: "⚠️ Please follow the chat rules. Further violations may result in a timeout.",
                description: "Warning message",
                cooldown_seconds: 5,
                moderator_only: true,
                is_enabled: true,
            },
            {
                trigger: "!chill",
                response_text: "❄️ Let's keep the chat chill and positive, everyone! Thanks!",
                description: "Calm down chat",
                cooldown_seconds: 30,
                moderator_only: true,
                is_enabled: true,
            },
        ],
    },
]

export default function CustomCommandsPage() {
    const [commands, setCommands] = useState<CustomCommand[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [accountsLoading, setAccountsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingCommand, setEditingCommand] = useState<CustomCommand | null>(null)
    const [saving, setSaving] = useState(false)
    const [previewTemplate, setPreviewTemplate] = useState<CommandTemplate | null>(null)
    const [applyingTemplate, setApplyingTemplate] = useState(false)
    const [selectedTemplateAccount, setSelectedTemplateAccount] = useState<string>("")

    // Form state - using backend field names
    const [formData, setFormData] = useState<CreateCustomCommandRequest>({
        account_id: "",
        trigger: "",
        response_text: "",
        description: "",
        response_type: "text",
        cooldown_seconds: 5,
        moderator_only: false,
        member_only: false,
        is_enabled: true,
    })

    // UI state for user level (mapped to moderator_only/member_only)
    const [userLevel, setUserLevel] = useState<"everyone" | "subscriber" | "moderator" | "owner">("everyone")

    // Load accounts on mount
    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                setAccountsLoading(true)
                const data = await accountsApi.getAccounts()
                console.log("[CustomCommands] Accounts loaded:", data)
                setAccounts(Array.isArray(data) ? data : [])
            } catch (error) {
                console.error("[CustomCommands] Failed to load accounts:", error)
                setAccounts([])
            } finally {
                setAccountsLoading(false)
            }
        }
        fetchAccounts()
    }, [])

    // Function to load commands
    const loadCommands = async () => {
        try {
            setLoading(true)
            const data = await moderationApi.getCustomCommands(
                accountFilter !== "all" ? accountFilter : undefined
            )
            setCommands(data)
        } catch (error) {
            console.error("[CustomCommands] Failed to load commands:", error)
        } finally {
            setLoading(false)
        }
    }

    // Load commands when account filter changes
    useEffect(() => {
        loadCommands()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountFilter])

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
            response_text: "",
            description: "",
            response_type: "text",
            cooldown_seconds: 5,
            moderator_only: false,
            member_only: false,
            is_enabled: true,
        })
        setUserLevel("everyone")
        setDialogOpen(true)
    }

    const openEditDialog = (command: CustomCommand) => {
        setEditingCommand(command)
        setFormData({
            account_id: command.account_id,
            trigger: command.trigger,
            response_text: command.response,
            description: command.description || "",
            response_type: "text",
            cooldown_seconds: command.cooldown,
            moderator_only: command.user_level === "moderator",
            member_only: command.user_level === "subscriber",
            is_enabled: command.enabled,
        })
        setUserLevel(command.user_level)
        setDialogOpen(true)
    }

    const handleUserLevelChange = (level: typeof userLevel) => {
        setUserLevel(level)
        setFormData({
            ...formData,
            moderator_only: level === "moderator",
            member_only: level === "subscriber",
        })
    }

    const handleSave = async () => {
        if (!formData.trigger || !formData.response_text || !formData.account_id) {
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

    const handleApplyTemplate = async (template: CommandTemplate) => {
        if (!selectedTemplateAccount) {
            alert("Please select an account to apply the template")
            return
        }

        try {
            setApplyingTemplate(true)
            for (const cmd of template.commands) {
                await moderationApi.createCustomCommand({
                    ...cmd,
                    account_id: selectedTemplateAccount,
                })
            }
            setPreviewTemplate(null)
            setSelectedTemplateAccount("")
            loadCommands()
            alert(`Successfully applied "${template.name}" template with ${template.commands.length} commands!`)
        } catch (error) {
            console.error("Failed to apply template:", error)
            alert("Failed to apply template. Some commands may have been created.")
        } finally {
            setApplyingTemplate(false)
        }
    }

    const getCategoryColor = (category: CommandTemplate["category"]) => {
        const colors = {
            info: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
            social: "bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400",
            fun: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
            moderation: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
        }
        return colors[category]
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
                                    <SelectValue placeholder={accountsLoading ? "Loading..." : "All Accounts"} />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Accounts</SelectItem>
                                    {accountsLoading ? (
                                        <SelectItem value="_loading" disabled>
                                            <span className="flex items-center gap-2">
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Loading accounts...
                                            </span>
                                        </SelectItem>
                                    ) : accounts.length === 0 ? (
                                        <SelectItem value="_empty" disabled>
                                            No accounts connected
                                        </SelectItem>
                                    ) : (
                                        accounts.map((account) => (
                                            <SelectItem key={account.id} value={account.id}>
                                                {account.channelTitle}
                                            </SelectItem>
                                        ))
                                    )}
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

                {/* Command Templates Section */}
                <div className="mt-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="h-5 w-5 text-yellow-500" />
                        <h2 className="text-xl font-semibold">Command Templates</h2>
                    </div>
                    <p className="text-muted-foreground mb-4">
                        Quickly add pre-configured commands to engage with your audience
                    </p>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {COMMAND_TEMPLATES.map((template) => {
                            const Icon = template.icon
                            return (
                                <Card key={template.id} className="border-0 shadow-lg hover:shadow-xl transition-shadow">
                                    <CardContent className="p-5">
                                        <div className="flex items-start gap-3">
                                            <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${template.color} text-white`}>
                                                <Icon className="h-5 w-5" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="font-semibold truncate">{template.name}</h3>
                                                    <Badge variant="outline" className={getCategoryColor(template.category)}>
                                                        {template.category}
                                                    </Badge>
                                                </div>
                                                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                                                    {template.description}
                                                </p>
                                                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                                                    <CheckCircle2 className="h-3 w-3" />
                                                    <span>{template.commands.length} commands included</span>
                                                </div>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => setPreviewTemplate(template)}
                                                    >
                                                        <Eye className="h-3 w-3 mr-1" />
                                                        Preview
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        className={`bg-gradient-to-r ${template.color} text-white`}
                                                        onClick={() => {
                                                            setPreviewTemplate(template)
                                                            setSelectedTemplateAccount(accounts[0]?.id || "")
                                                        }}
                                                    >
                                                        <Plus className="h-3 w-3 mr-1" />
                                                        Apply
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Template Preview Dialog */}
            <Dialog open={!!previewTemplate} onOpenChange={(open) => !open && setPreviewTemplate(null)}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    {previewTemplate && (
                        <>
                            <DialogHeader>
                                <div className="flex items-center gap-3">
                                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br ${previewTemplate.color} text-white`}>
                                        <previewTemplate.icon className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <DialogTitle>{previewTemplate.name}</DialogTitle>
                                        <DialogDescription>{previewTemplate.description}</DialogDescription>
                                    </div>
                                </div>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                {/* Account Selection */}
                                <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
                                    <Label>Apply to Account</Label>
                                    <Select
                                        value={selectedTemplateAccount}
                                        onValueChange={setSelectedTemplateAccount}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select account to apply template" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {accountsLoading ? (
                                                <SelectItem value="_loading" disabled>
                                                    <span className="flex items-center gap-2">
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                        Loading accounts...
                                                    </span>
                                                </SelectItem>
                                            ) : accounts.length === 0 ? (
                                                <SelectItem value="_empty" disabled>
                                                    No accounts connected
                                                </SelectItem>
                                            ) : (
                                                accounts.map((account) => (
                                                    <SelectItem key={account.id} value={account.id}>
                                                        {account.channelTitle}
                                                    </SelectItem>
                                                ))
                                            )}
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Commands Preview */}
                                <div>
                                    <h4 className="font-medium mb-3 flex items-center gap-2">
                                        <Terminal className="h-4 w-4" />
                                        Commands in this template ({previewTemplate.commands.length})
                                    </h4>
                                    <div className="space-y-3">
                                        {previewTemplate.commands.map((cmd, index) => (
                                            <div key={index} className="p-3 border rounded-lg bg-card">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <code className="font-semibold bg-muted px-2 py-0.5 rounded text-sm">
                                                        {cmd.trigger}
                                                    </code>
                                                    {cmd.moderator_only && (
                                                        <Badge variant="default" className="text-xs">Mod Only</Badge>
                                                    )}
                                                    {cmd.member_only && (
                                                        <Badge variant="secondary" className="text-xs">Members</Badge>
                                                    )}
                                                    {cmd.cooldown_seconds && cmd.cooldown_seconds > 0 && (
                                                        <Badge variant="outline" className="text-xs">
                                                            <Clock className="h-3 w-3 mr-1" />
                                                            {cmd.cooldown_seconds}s
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-muted-foreground mt-1">
                                                    {cmd.response_text}
                                                </p>
                                                {cmd.description && (
                                                    <p className="text-xs text-muted-foreground mt-1 italic">
                                                        {cmd.description}
                                                    </p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setPreviewTemplate(null)}>
                                    Cancel
                                </Button>
                                <Button
                                    onClick={() => handleApplyTemplate(previewTemplate)}
                                    disabled={applyingTemplate || !selectedTemplateAccount}
                                    className={`bg-gradient-to-r ${previewTemplate.color} text-white`}
                                >
                                    {applyingTemplate && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Apply {previewTemplate.commands.length} Commands
                                </Button>
                            </DialogFooter>
                        </>
                    )}
                </DialogContent>
            </Dialog>

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
                                    <SelectValue placeholder={accountsLoading ? "Loading..." : "Select account"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {accountsLoading ? (
                                        <SelectItem value="_loading" disabled>
                                            <span className="flex items-center gap-2">
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Loading accounts...
                                            </span>
                                        </SelectItem>
                                    ) : accounts.length === 0 ? (
                                        <SelectItem value="_empty" disabled>
                                            No accounts connected
                                        </SelectItem>
                                    ) : (
                                        accounts.map((account) => (
                                            <SelectItem key={account.id} value={account.id}>
                                                {account.channelTitle}
                                            </SelectItem>
                                        ))
                                    )}
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
                                value={formData.response_text}
                                onChange={(e) =>
                                    setFormData({ ...formData, response_text: e.target.value })
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
                                    value={userLevel}
                                    onValueChange={(value: typeof userLevel) => handleUserLevelChange(value)}
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
                                    value={String(formData.cooldown_seconds)}
                                    onValueChange={(value) =>
                                        setFormData({ ...formData, cooldown_seconds: parseInt(value) })
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
                                checked={formData.is_enabled}
                                onCheckedChange={(checked) =>
                                    setFormData({ ...formData, is_enabled: checked })
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
