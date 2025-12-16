"use client"

import { useState, useEffect } from "react"
import {
    Plus,
    Search,
    Edit,
    Trash2,
    Shield,
    Link2,
    Type,
    Hash,
    MessageSquare,
    Loader2,
    Eye,
    Sparkles,
    AlertTriangle,
    Ban,
    Clock,
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
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
import { useToast } from "@/components/ui/toast"
import { moderationApi, type ModerationRule, type CreateModerationRuleRequest, type RuleType, type ActionType, type SeverityLevel } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

const RULE_TYPES: { value: RuleType; label: string; icon: typeof Type; description: string }[] = [
    { value: "keyword", label: "Keyword", icon: Type, description: "Block specific words or phrases" },
    { value: "regex", label: "Regex", icon: Hash, description: "Advanced pattern matching" },
    { value: "spam", label: "Spam", icon: MessageSquare, description: "Detect repetitive messages" },
    { value: "caps", label: "Caps Lock", icon: Type, description: "Limit excessive capitals" },
    { value: "links", label: "Links", icon: Link2, description: "Block URLs and links" },
]

const ACTIONS: { value: ActionType; label: string; description: string }[] = [
    { value: "hide", label: "Hide", description: "Hide from public view" },
    { value: "delete", label: "Delete", description: "Remove the message" },
    { value: "timeout", label: "Timeout", description: "Temporarily mute user" },
    { value: "warn", label: "Warn", description: "Send a warning" },
    { value: "ban", label: "Ban", description: "Permanently ban user" },
]

const SEVERITY_LEVELS: { value: SeverityLevel; label: string }[] = [
    { value: "low", label: "Low" },
    { value: "medium", label: "Medium" },
    { value: "high", label: "High" },
    { value: "critical", label: "Critical" },
]

// Moderation Rule Templates
interface RuleTemplate {
    id: string
    name: string
    description: string
    category: "spam" | "profanity" | "safety" | "engagement"
    icon: typeof Shield
    color: string
    rules: Omit<CreateModerationRuleRequest, "account_id">[]
}

const RULE_TEMPLATES: RuleTemplate[] = [
    {
        id: "anti-spam-basic",
        name: "Anti-Spam Basic",
        description: "Block repetitive messages, excessive caps, and common spam patterns",
        category: "spam",
        icon: MessageSquare,
        color: "from-blue-500 to-blue-600",
        rules: [
            {
                name: "Block Repeated Messages",
                description: "Detect and hide repetitive spam messages",
                rule_type: "spam",
                action_type: "hide",
                severity: "medium",
                is_enabled: true,
                priority: 10,
            },
            {
                name: "Excessive Caps Lock",
                description: "Warn users using too many capital letters",
                rule_type: "caps",
                action_type: "warn",
                severity: "low",
                is_enabled: true,
                priority: 5,
            },
        ],
    },
    {
        id: "anti-spam-strict",
        name: "Anti-Spam Strict",
        description: "Aggressive spam protection with timeouts for repeat offenders",
        category: "spam",
        icon: Ban,
        color: "from-orange-500 to-orange-600",
        rules: [
            {
                name: "Block Spam - Timeout",
                description: "Timeout users sending spam messages",
                rule_type: "spam",
                action_type: "timeout",
                severity: "high",
                timeout_duration_seconds: 300,
                is_enabled: true,
                priority: 15,
            },
            {
                name: "Block Excessive Caps",
                description: "Delete messages with excessive capitals",
                rule_type: "caps",
                action_type: "delete",
                severity: "medium",
                is_enabled: true,
                priority: 10,
            },
            {
                name: "Block All Links",
                description: "Remove all links from chat",
                rule_type: "links",
                action_type: "delete",
                severity: "medium",
                is_enabled: true,
                priority: 12,
            },
        ],
    },
    {
        id: "profanity-filter",
        name: "Profanity Filter",
        description: "Block common profanity and offensive words",
        category: "profanity",
        icon: AlertTriangle,
        color: "from-red-500 to-red-600",
        rules: [
            {
                name: "Block Profanity",
                description: "Hide messages containing profanity",
                rule_type: "keyword",
                keywords: ["fuck", "shit", "ass", "bitch", "damn", "crap", "bastard"],
                action_type: "hide",
                severity: "high",
                is_enabled: true,
                priority: 20,
            },
            {
                name: "Block Slurs",
                description: "Delete messages with slurs and timeout user",
                rule_type: "keyword",
                keywords: ["n-word", "f-word", "retard"],
                action_type: "timeout",
                severity: "critical",
                timeout_duration_seconds: 600,
                is_enabled: true,
                priority: 25,
            },
        ],
    },
    {
        id: "link-protection",
        name: "Link Protection",
        description: "Control and filter links shared in chat",
        category: "safety",
        icon: Link2,
        color: "from-purple-500 to-purple-600",
        rules: [
            {
                name: "Block Suspicious Links",
                description: "Hide messages with unknown links",
                rule_type: "links",
                action_type: "hide",
                severity: "medium",
                is_enabled: true,
                priority: 15,
            },
            {
                name: "Block Phishing Patterns",
                description: "Delete messages with phishing URL patterns",
                rule_type: "regex",
                pattern: "(free|win|claim|prize|gift|click).*(http|www|bit\\.ly|tinyurl)",
                action_type: "delete",
                severity: "high",
                is_enabled: true,
                priority: 18,
            },
        ],
    },
    {
        id: "self-promo-block",
        name: "Self-Promotion Blocker",
        description: "Prevent self-promotion and channel advertising",
        category: "engagement",
        icon: Ban,
        color: "from-yellow-500 to-yellow-600",
        rules: [
            {
                name: "Block Channel Promotion",
                description: "Hide messages promoting other channels",
                rule_type: "keyword",
                keywords: ["subscribe to my", "check out my channel", "follow me on", "my youtube", "my twitch"],
                action_type: "hide",
                severity: "medium",
                is_enabled: true,
                priority: 12,
            },
            {
                name: "Block Social Media Links",
                description: "Remove social media promotion links",
                rule_type: "regex",
                pattern: "(instagram|twitter|tiktok|facebook)\\.com\\/[a-zA-Z0-9_]+",
                action_type: "delete",
                severity: "low",
                is_enabled: true,
                priority: 10,
            },
        ],
    },
    {
        id: "family-friendly",
        name: "Family Friendly",
        description: "Comprehensive filter for family-friendly streams",
        category: "safety",
        icon: Shield,
        color: "from-green-500 to-green-600",
        rules: [
            {
                name: "Block Adult Content Keywords",
                description: "Hide messages with adult content references",
                rule_type: "keyword",
                keywords: ["porn", "xxx", "nsfw", "18+", "adult content", "onlyfans"],
                action_type: "delete",
                severity: "critical",
                is_enabled: true,
                priority: 30,
            },
            {
                name: "Block Violence Keywords",
                description: "Hide messages promoting violence",
                rule_type: "keyword",
                keywords: ["kill yourself", "kys", "die", "murder", "suicide"],
                action_type: "timeout",
                severity: "critical",
                timeout_duration_seconds: 3600,
                is_enabled: true,
                priority: 28,
            },
            {
                name: "Block Profanity",
                description: "Hide all profanity",
                rule_type: "keyword",
                keywords: ["fuck", "shit", "ass", "bitch", "damn"],
                action_type: "hide",
                severity: "high",
                is_enabled: true,
                priority: 20,
            },
        ],
    },
]

export default function ModerationSettingsPage() {
    const { addToast } = useToast()
    const [rules, setRules] = useState<ModerationRule[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [accountsLoading, setAccountsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingRule, setEditingRule] = useState<ModerationRule | null>(null)
    const [saving, setSaving] = useState(false)
    const [previewTemplate, setPreviewTemplate] = useState<RuleTemplate | null>(null)
    const [applyingTemplate, setApplyingTemplate] = useState(false)
    const [selectedTemplateAccount, setSelectedTemplateAccount] = useState<string>("")

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [totalItems, setTotalItems] = useState(0)
    const pageSize = 10

    // Form state
    const [formData, setFormData] = useState<CreateModerationRuleRequest>({
        account_id: "",
        name: "",
        description: "",
        rule_type: "keyword",
        pattern: "",
        keywords: [],
        action_type: "hide",
        severity: "medium",
        timeout_duration_seconds: 60,
        is_enabled: true,
        priority: 0,
    })

    // Load accounts and rules on mount
    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                setAccountsLoading(true)
                const data = await accountsApi.getAccounts()
                console.log("[ModerationSettings] Accounts loaded:", data)
                setAccounts(Array.isArray(data) ? data : [])
            } catch (error) {
                console.error("[ModerationSettings] Failed to load accounts:", error)
                setAccounts([])
            } finally {
                setAccountsLoading(false)
            }
        }
        fetchAccounts()
    }, [])

    // Function to load rules
    const loadRules = async (page: number = currentPage) => {
        try {
            setLoading(true)
            const data = await moderationApi.getRules({
                accountId: accountFilter !== "all" ? accountFilter : undefined,
                page,
                pageSize,
            })
            setRules(data.items)
            setTotalPages(data.total_pages)
            setTotalItems(data.total)
            setCurrentPage(data.page)
        } catch (error) {
            console.error("[ModerationSettings] Failed to load rules:", error)
        } finally {
            setLoading(false)
        }
    }

    // Load rules when account filter changes
    useEffect(() => {
        setCurrentPage(1)
        loadRules(1)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [accountFilter])

    // Handle page change
    const handlePageChange = (page: number) => {
        setCurrentPage(page)
        loadRules(page)
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
            description: "",
            rule_type: "keyword",
            pattern: "",
            keywords: [],
            action_type: "hide",
            severity: "medium",
            timeout_duration_seconds: 60,
            is_enabled: true,
            priority: 0,
        })
        setDialogOpen(true)
    }

    const openEditDialog = (rule: ModerationRule) => {
        setEditingRule(rule)
        // Parse keywords from pattern if it's a keyword rule
        const keywords = rule.type === "keyword" && rule.pattern
            ? rule.pattern.split(",").map(k => k.trim()).filter(Boolean)
            : []
        setFormData({
            account_id: rule.account_id,
            name: rule.name,
            description: rule.description || "",
            rule_type: rule.type,
            pattern: rule.type !== "keyword" ? rule.pattern : "",
            keywords: keywords,
            action_type: rule.action,
            severity: rule.severity || "medium",
            timeout_duration_seconds: rule.timeout_duration || 60,
            is_enabled: rule.enabled,
            priority: rule.priority || 0,
        })
        setDialogOpen(true)
    }

    const handleSave = async () => {
        if (!formData.name || !formData.account_id) {
            addToast({ type: "error", title: "Validation Error", description: "Please fill in all required fields" })
            return
        }

        // Validate pattern/keywords based on rule type
        if (formData.rule_type === "keyword" && (!formData.keywords || formData.keywords.length === 0)) {
            addToast({ type: "error", title: "Validation Error", description: "Please enter at least one keyword" })
            return
        }
        if (formData.rule_type === "regex" && !formData.pattern) {
            addToast({ type: "error", title: "Validation Error", description: "Please enter a regex pattern" })
            return
        }

        try {
            setSaving(true)
            if (editingRule) {
                await moderationApi.updateRule(editingRule.id, formData)
                addToast({ type: "success", title: "Rule Updated", description: `"${formData.name}" has been updated successfully.` })
            } else {
                await moderationApi.createRule(formData)
                addToast({ type: "success", title: "Rule Created", description: `"${formData.name}" has been created successfully.` })
            }
            setDialogOpen(false)
            loadRules()
        } catch (error) {
            console.error("Failed to save rule:", error)
            addToast({ type: "error", title: "Error", description: "Failed to save rule. Please try again." })
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (ruleId: string) => {
        if (!confirm("Are you sure you want to delete this rule?")) return
        try {
            await moderationApi.deleteRule(ruleId)
            loadRules()
            addToast({ type: "success", title: "Rule Deleted", description: "The rule has been deleted successfully." })
        } catch (error) {
            console.error("Failed to delete rule:", error)
            addToast({ type: "error", title: "Error", description: "Failed to delete rule. Please try again." })
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

    const getRuleTypeIcon = (type: RuleType) => {
        const ruleType = RULE_TYPES.find((t) => t.value === type)
        return ruleType?.icon || Shield
    }

    const getActionBadge = (action: ActionType) => {
        const variants: Record<ActionType, "default" | "secondary" | "destructive" | "outline"> = {
            delete: "destructive",
            ban: "destructive",
            timeout: "default",
            hide: "secondary",
            warn: "outline",
        }
        return <Badge variant={variants[action] || "default"}>{action}</Badge>
    }

    const getSeverityBadge = (severity: SeverityLevel) => {
        const variants: Record<SeverityLevel, "default" | "secondary" | "destructive" | "outline"> = {
            low: "outline",
            medium: "secondary",
            high: "default",
            critical: "destructive",
        }
        return <Badge variant={variants[severity]}>{severity}</Badge>
    }

    const handleApplyTemplate = async (template: RuleTemplate) => {
        if (!selectedTemplateAccount) {
            addToast({ type: "warning", title: "Select Account", description: "Please select an account to apply the template" })
            return
        }

        try {
            setApplyingTemplate(true)

            let createdCount = 0
            let skippedCount = 0

            // Try to create each rule - backend will reject duplicates with 409
            for (const rule of template.rules) {
                try {
                    await moderationApi.createRule({
                        ...rule,
                        account_id: selectedTemplateAccount,
                    })
                    createdCount++
                } catch (error: unknown) {
                    // Check if it's a 409 Conflict (duplicate)
                    const err = error as { status?: number }
                    if (err.status === 409) {
                        skippedCount++
                    } else {
                        throw error // Re-throw other errors
                    }
                }
            }

            setPreviewTemplate(null)
            setSelectedTemplateAccount("")
            loadRules(1)

            if (createdCount === 0) {
                addToast({
                    type: "warning",
                    title: "Template Already Applied",
                    description: `All ${template.rules.length} rules from "${template.name}" already exist for this account.`
                })
            } else if (skippedCount > 0) {
                addToast({
                    type: "success",
                    title: "Template Applied",
                    description: `Added ${createdCount} new rules. Skipped ${skippedCount} duplicate rules.`
                })
            } else {
                addToast({
                    type: "success",
                    title: "Template Applied",
                    description: `Successfully applied "${template.name}" template with ${createdCount} rules!`
                })
            }
        } catch (error) {
            console.error("Failed to apply template:", error)
            addToast({ type: "error", title: "Error", description: "Failed to apply template. Some rules may have been created." })
        } finally {
            setApplyingTemplate(false)
        }
    }

    const getCategoryColor = (category: RuleTemplate["category"]) => {
        const colors = {
            spam: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
            profanity: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
            safety: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
            engagement: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
        }
        return colors[category]
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
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <h3 className="font-semibold">{rule.name}</h3>
                                                    {getActionBadge(rule.action)}
                                                    {getSeverityBadge(rule.severity)}
                                                    {rule.action === "timeout" && rule.timeout_duration && (
                                                        <Badge variant="outline">
                                                            {rule.timeout_duration}s
                                                        </Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate">
                                                    {rule.type}: <code className="bg-muted px-1 rounded">{rule.pattern || "(no pattern)"}</code>
                                                </p>
                                                {rule.trigger_count > 0 && (
                                                    <p className="text-xs text-muted-foreground">
                                                        Triggered {rule.trigger_count} times
                                                    </p>
                                                )}
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

                {/* Pagination */}
                {!loading && totalPages > 1 && (
                    <div className="flex items-center justify-between mt-4">
                        <p className="text-sm text-muted-foreground">
                            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalItems)} of {totalItems} rules
                        </p>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage <= 1}
                            >
                                <ChevronLeft className="h-4 w-4" />
                                Previous
                            </Button>
                            <div className="flex items-center gap-1">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    let pageNum: number
                                    if (totalPages <= 5) {
                                        pageNum = i + 1
                                    } else if (currentPage <= 3) {
                                        pageNum = i + 1
                                    } else if (currentPage >= totalPages - 2) {
                                        pageNum = totalPages - 4 + i
                                    } else {
                                        pageNum = currentPage - 2 + i
                                    }
                                    return (
                                        <Button
                                            key={pageNum}
                                            variant={currentPage === pageNum ? "default" : "outline"}
                                            size="sm"
                                            className="w-8 h-8 p-0"
                                            onClick={() => handlePageChange(pageNum)}
                                        >
                                            {pageNum}
                                        </Button>
                                    )
                                })}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage >= totalPages}
                            >
                                Next
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                )}

                {/* Rule Templates Section */}
                <div className="mt-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="h-5 w-5 text-yellow-500" />
                        <h2 className="text-xl font-semibold">Quick Start Templates</h2>
                    </div>
                    <p className="text-muted-foreground mb-4">
                        Apply pre-configured moderation rules to quickly protect your chat
                    </p>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {RULE_TEMPLATES.map((template) => {
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
                                                    <span>{template.rules.length} rules included</span>
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

                                {/* Rules Preview */}
                                <div>
                                    <h4 className="font-medium mb-3 flex items-center gap-2">
                                        <Shield className="h-4 w-4" />
                                        Rules in this template ({previewTemplate.rules.length})
                                    </h4>
                                    <div className="space-y-3">
                                        {previewTemplate.rules.map((rule, index) => (
                                            <div key={index} className="p-3 border rounded-lg bg-card">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="font-medium">{rule.name}</span>
                                                    <Badge variant={
                                                        rule.action_type === "ban" || rule.action_type === "delete" ? "destructive" :
                                                            rule.action_type === "timeout" ? "default" :
                                                                rule.action_type === "warn" ? "outline" : "secondary"
                                                    }>
                                                        {rule.action_type}
                                                    </Badge>
                                                    <Badge variant={
                                                        rule.severity === "critical" ? "destructive" :
                                                            rule.severity === "high" ? "default" :
                                                                rule.severity === "medium" ? "secondary" : "outline"
                                                    }>
                                                        {rule.severity}
                                                    </Badge>
                                                </div>
                                                <p className="text-sm text-muted-foreground">{rule.description}</p>
                                                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                                                    <span className="px-2 py-0.5 bg-muted rounded">Type: {rule.rule_type}</span>
                                                    {rule.keywords && rule.keywords.length > 0 && (
                                                        <span className="px-2 py-0.5 bg-muted rounded">
                                                            Keywords: {rule.keywords.slice(0, 3).join(", ")}
                                                            {rule.keywords.length > 3 && ` +${rule.keywords.length - 3} more`}
                                                        </span>
                                                    )}
                                                    {rule.pattern && (
                                                        <span className="px-2 py-0.5 bg-muted rounded font-mono text-xs">
                                                            Pattern: {rule.pattern.slice(0, 30)}{rule.pattern.length > 30 && "..."}
                                                        </span>
                                                    )}
                                                    {rule.timeout_duration_seconds && (
                                                        <span className="px-2 py-0.5 bg-muted rounded flex items-center gap-1">
                                                            <Clock className="h-3 w-3" />
                                                            {rule.timeout_duration_seconds >= 3600
                                                                ? `${rule.timeout_duration_seconds / 3600}h`
                                                                : `${rule.timeout_duration_seconds / 60}m`} timeout
                                                        </span>
                                                    )}
                                                </div>
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
                                    Apply {previewTemplate.rules.length} Rules
                                </Button>
                            </DialogFooter>
                        </>
                    )}
                </DialogContent>
            </Dialog>

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
                            <Label>Rule Name</Label>
                            <Input
                                placeholder="e.g., Block spam links"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Description (optional)</Label>
                            <Input
                                placeholder="Brief description of this rule"
                                value={formData.description || ""}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Rule Type</Label>
                            <Select
                                value={formData.rule_type}
                                onValueChange={(value: RuleType) =>
                                    setFormData({ ...formData, rule_type: value })
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
                                {RULE_TYPES.find((t) => t.value === formData.rule_type)?.description}
                            </p>
                        </div>

                        {formData.rule_type === "keyword" ? (
                            <div className="space-y-2">
                                <Label>Keywords</Label>
                                <Textarea
                                    placeholder="Enter keywords (comma separated)..."
                                    value={formData.keywords?.join(", ") || ""}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        keywords: e.target.value.split(",").map(k => k.trim()).filter(Boolean)
                                    })}
                                    rows={3}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Separate multiple keywords with commas
                                </p>
                            </div>
                        ) : formData.rule_type === "regex" ? (
                            <div className="space-y-2">
                                <Label>Regex Pattern</Label>
                                <Textarea
                                    placeholder="Enter regex pattern..."
                                    value={formData.pattern || ""}
                                    onChange={(e) => setFormData({ ...formData, pattern: e.target.value })}
                                    rows={3}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Use standard regex syntax
                                </p>
                            </div>
                        ) : null}

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Action</Label>
                                <Select
                                    value={formData.action_type}
                                    onValueChange={(value: ActionType) =>
                                        setFormData({ ...formData, action_type: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {ACTIONS.map((action) => (
                                            <SelectItem key={action.value} value={action.value}>
                                                {action.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <Label>Severity</Label>
                                <Select
                                    value={formData.severity}
                                    onValueChange={(value: SeverityLevel) =>
                                        setFormData({ ...formData, severity: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {SEVERITY_LEVELS.map((level) => (
                                            <SelectItem key={level.value} value={level.value}>
                                                {level.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        {formData.action_type === "timeout" && (
                            <div className="space-y-2">
                                <Label>Timeout Duration</Label>
                                <Select
                                    value={String(formData.timeout_duration_seconds)}
                                    onValueChange={(value) =>
                                        setFormData({ ...formData, timeout_duration_seconds: parseInt(value) })
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
                                checked={formData.is_enabled}
                                onCheckedChange={(checked) => setFormData({ ...formData, is_enabled: checked })}
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
