"use client"

import { useState, useEffect } from "react"
import {
    Plus,
    Search,
    Edit,
    Trash2,
    Bot,
    Loader2,
    Play,
    Hash,
    MessageSquare,
    CheckCircle,
    XCircle,
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
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { moderationApi, type AutoReplyRule } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

interface CreateAutoReplyRuleData {
    account_id: string
    name: string
    trigger_pattern: string
    reply_template: string
    enabled: boolean
}

export default function AutoReplyRulesPage() {
    const [rules, setRules] = useState<AutoReplyRule[]>([])
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editingRule, setEditingRule] = useState<AutoReplyRule | null>(null)
    const [saving, setSaving] = useState(false)

    // Test dialog state
    const [testDialogOpen, setTestDialogOpen] = useState(false)
    const [testingRule, setTestingRule] = useState<AutoReplyRule | null>(null)
    const [testInput, setTestInput] = useState("")
    const [testResult, setTestResult] = useState<{ matches: boolean; reply: string } | null>(null)
    const [testing, setTesting] = useState(false)

    // Form state
    const [formData, setFormData] = useState<CreateAutoReplyRuleData>({
        account_id: "",
        name: "",
        trigger_pattern: "",
        reply_template: "",
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
            const data = await moderationApi.getAutoReplyRules(
                accountFilter !== "all" ? accountFilter : undefined
            )
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
            rule.trigger_pattern.toLowerCase().includes(query) ||
            rule.reply_template.toLowerCase().includes(query)
        )
    })

    const openCreateDialog = () => {
        setEditingRule(null)
        setFormData({
            account_id: accounts[0]?.id || "",
            name: "",
            trigger_pattern: "",
            reply_template: "",
            enabled: true,
        })
        setDialogOpen(true)
    }

    const openEditDialog = (rule: AutoReplyRule) => {
        setEditingRule(rule)
        setFormData({
            account_id: rule.account_id,
            name: rule.name,
            trigger_pattern: rule.trigger_pattern,
            reply_template: rule.reply_template,
            enabled: rule.enabled,
        })
        setDialogOpen(true)
    }

    const handleSave = async () => {
        if (!formData.name || !formData.trigger_pattern || !formData.reply_template || !formData.account_id) {
            alert("Please fill in all required fields")
            return
        }

        try {
            setSaving(true)
            if (editingRule) {
                await moderationApi.updateAutoReplyRule(editingRule.id, {
                    name: formData.name,
                    trigger_pattern: formData.trigger_pattern,
                    reply_template: formData.reply_template,
                    enabled: formData.enabled,
                })
            } else {
                await moderationApi.createAutoReplyRule(formData)
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
        if (!confirm("Are you sure you want to delete this auto-reply rule?")) return
        try {
            await moderationApi.deleteAutoReplyRule(ruleId)
            loadRules()
        } catch (error) {
            console.error("Failed to delete rule:", error)
        }
    }

    const handleToggle = async (rule: AutoReplyRule, enabled: boolean) => {
        try {
            await moderationApi.updateAutoReplyRule(rule.id, { enabled })
            setRules((prev) =>
                prev.map((r) => (r.id === rule.id ? { ...r, enabled } : r))
            )
        } catch (error) {
            console.error("Failed to toggle rule:", error)
        }
    }

    const openTestDialog = (rule: AutoReplyRule) => {
        setTestingRule(rule)
        setTestInput("")
        setTestResult(null)
        setTestDialogOpen(true)
    }

    const handleTestRule = async () => {
        if (!testingRule || !testInput.trim()) return

        setTesting(true)
        // Simulate testing the rule locally
        try {
            // Check if the input matches the trigger pattern
            const pattern = new RegExp(testingRule.trigger_pattern, "i")
            const matches = pattern.test(testInput)

            setTestResult({
                matches,
                reply: matches ? testingRule.reply_template : "",
            })
        } catch (error) {
            // If regex is invalid, try simple string matching
            const matches = testInput.toLowerCase().includes(testingRule.trigger_pattern.toLowerCase())
            setTestResult({
                matches,
                reply: matches ? testingRule.reply_template : "",
            })
        } finally {
            setTesting(false)
        }
    }

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        })
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Comments", href: "/dashboard/comments" },
                { label: "Auto-Reply Rules" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Bot className="h-8 w-8" />
                            Auto-Reply Rules
                        </h1>
                        <p className="text-muted-foreground">
                            Configure automatic replies to comments matching specific patterns
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

                {/* Rules Table */}
                <Card className="border-0 shadow-lg">
                    <CardHeader>
                        <CardTitle>Rules</CardTitle>
                        <CardDescription>
                            {filteredRules.length} rule{filteredRules.length !== 1 ? "s" : ""} configured
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="space-y-4">
                                {[...Array(3)].map((_, i) => (
                                    <div key={i} className="flex items-center gap-4">
                                        <Skeleton className="h-4 w-32" />
                                        <Skeleton className="h-4 w-48" />
                                        <Skeleton className="h-4 w-24" />
                                    </div>
                                ))}
                            </div>
                        ) : filteredRules.length === 0 ? (
                            <div className="py-12 text-center">
                                <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="text-lg font-semibold mb-2">No auto-reply rules</h3>
                                <p className="text-muted-foreground mb-4">
                                    {searchQuery
                                        ? "No rules match your search"
                                        : "Create your first auto-reply rule to automatically respond to comments"}
                                </p>
                                <Button onClick={openCreateDialog}>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Add Rule
                                </Button>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Trigger Pattern</TableHead>
                                        <TableHead>Reply Template</TableHead>
                                        <TableHead>Account</TableHead>
                                        <TableHead>Matches</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredRules.map((rule) => (
                                        <TableRow key={rule.id}>
                                            <TableCell className="font-medium">{rule.name}</TableCell>
                                            <TableCell>
                                                <code className="bg-muted px-2 py-1 rounded text-xs">
                                                    {rule.trigger_pattern.length > 30
                                                        ? `${rule.trigger_pattern.substring(0, 30)}...`
                                                        : rule.trigger_pattern}
                                                </code>
                                            </TableCell>
                                            <TableCell className="max-w-[200px] truncate">
                                                {rule.reply_template}
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline">
                                                    {getAccountName(rule.account_id)}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="secondary">
                                                    <Hash className="mr-1 h-3 w-3" />
                                                    {rule.match_count}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Switch
                                                    checked={rule.enabled}
                                                    onCheckedChange={(checked) => handleToggle(rule, checked)}
                                                />
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-1">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => openTestDialog(rule)}
                                                        title="Test Rule"
                                                    >
                                                        <Play className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => openEditDialog(rule)}
                                                        title="Edit Rule"
                                                    >
                                                        <Edit className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleDelete(rule.id)}
                                                        title="Delete Rule"
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Add/Edit Rule Dialog */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>
                            {editingRule ? "Edit Auto-Reply Rule" : "Create Auto-Reply Rule"}
                        </DialogTitle>
                        <DialogDescription>
                            Configure a rule to automatically reply to comments matching a pattern.
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
                                placeholder="e.g., Thank you reply"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Trigger Pattern</Label>
                            <Textarea
                                placeholder="Enter keywords or regex pattern..."
                                value={formData.trigger_pattern}
                                onChange={(e) => setFormData({ ...formData, trigger_pattern: e.target.value })}
                                rows={2}
                            />
                            <p className="text-xs text-muted-foreground">
                                Use simple keywords or regex patterns. Examples: "thank you", "great video", "how to.*"
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label>Reply Template</Label>
                            <Textarea
                                placeholder="Enter the automatic reply message..."
                                value={formData.reply_template}
                                onChange={(e) => setFormData({ ...formData, reply_template: e.target.value })}
                                rows={4}
                            />
                            <p className="text-xs text-muted-foreground">
                                This message will be posted as a reply when a comment matches the trigger pattern.
                            </p>
                        </div>

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

            {/* Test Rule Dialog */}
            <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Test Auto-Reply Rule</DialogTitle>
                        <DialogDescription>
                            Test if a comment would trigger this rule: <strong>{testingRule?.name}</strong>
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Test Comment</Label>
                            <Textarea
                                placeholder="Enter a sample comment to test..."
                                value={testInput}
                                onChange={(e) => {
                                    setTestInput(e.target.value)
                                    setTestResult(null)
                                }}
                                rows={3}
                            />
                        </div>

                        {testResult && (
                            <Card className={testResult.matches ? "border-green-500" : "border-red-500"}>
                                <CardContent className="pt-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        {testResult.matches ? (
                                            <>
                                                <CheckCircle className="h-5 w-5 text-green-500" />
                                                <span className="font-medium text-green-700 dark:text-green-400">
                                                    Match Found!
                                                </span>
                                            </>
                                        ) : (
                                            <>
                                                <XCircle className="h-5 w-5 text-red-500" />
                                                <span className="font-medium text-red-700 dark:text-red-400">
                                                    No Match
                                                </span>
                                            </>
                                        )}
                                    </div>
                                    {testResult.matches && (
                                        <div className="mt-3">
                                            <Label className="text-xs text-muted-foreground">Auto-Reply:</Label>
                                            <p className="mt-1 p-2 bg-muted rounded text-sm">
                                                {testResult.reply}
                                            </p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        <div className="p-3 bg-muted/50 rounded-lg">
                            <Label className="text-xs text-muted-foreground">Trigger Pattern:</Label>
                            <code className="block mt-1 text-sm">{testingRule?.trigger_pattern}</code>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setTestDialogOpen(false)}>
                            Close
                        </Button>
                        <Button onClick={handleTestRule} disabled={testing || !testInput.trim()}>
                            {testing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            <Play className="mr-2 h-4 w-4" />
                            Test Rule
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
