"use client"

import { useState, useEffect } from "react"
import {
    Bot,
    Save,
    TestTube,
    Loader2,
    Sparkles,
    MessageSquare,
    Settings2,
    Zap,
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
import { moderationApi, type ChatbotConfig } from "@/lib/api/moderation"
import { accountsApi } from "@/lib/api/accounts"
import type { YouTubeAccount } from "@/types"

const PERSONALITIES = [
    {
        value: "friendly",
        label: "Friendly",
        description: "Warm, welcoming, and casual tone",
        emoji: "😊",
    },
    {
        value: "professional",
        label: "Professional",
        description: "Formal and informative responses",
        emoji: "💼",
    },
    {
        value: "funny",
        label: "Funny",
        description: "Humorous and entertaining style",
        emoji: "😄",
    },
    {
        value: "custom",
        label: "Custom",
        description: "Define your own personality",
        emoji: "✨",
    },
] as const

const RESPONSE_STYLES = [
    { value: "brief", label: "Brief", description: "Short, concise responses" },
    { value: "detailed", label: "Detailed", description: "Comprehensive explanations" },
    { value: "conversational", label: "Conversational", description: "Natural, flowing dialogue" },
] as const

export default function ChatbotConfigPage() {
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [selectedAccount, setSelectedAccount] = useState<string>("")
    const [config, setConfig] = useState<ChatbotConfig | null>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [testDialogOpen, setTestDialogOpen] = useState(false)
    const [testMessage, setTestMessage] = useState("")
    const [testResponse, setTestResponse] = useState("")
    const [testing, setTesting] = useState(false)

    // Form state
    const [formData, setFormData] = useState<Partial<ChatbotConfig>>({
        enabled: false,
        personality: "friendly",
        custom_personality: "",
        response_style: "conversational",
        triggers: [],
        greeting_enabled: false,
        greeting_message: "",
        farewell_enabled: false,
        farewell_message: "",
    })
    const [triggerInput, setTriggerInput] = useState("")

    useEffect(() => {
        loadAccounts()
    }, [])

    useEffect(() => {
        if (selectedAccount) {
            loadConfig()
        }
    }, [selectedAccount])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            const accountList = Array.isArray(data) ? data : []
            setAccounts(accountList)
            if (accountList.length > 0) {
                setSelectedAccount(accountList[0].id)
            }
        } catch (error) {
            console.error("Failed to load accounts:", error)
        }
    }

    const loadConfig = async () => {
        try {
            setLoading(true)
            const data = await moderationApi.getChatbotConfig(selectedAccount)
            if (data) {
                setConfig(data)
                setFormData({
                    enabled: data.enabled,
                    personality: data.personality,
                    custom_personality: data.custom_personality || "",
                    response_style: data.response_style,
                    triggers: data.triggers || [],
                    greeting_enabled: data.greeting_enabled,
                    greeting_message: data.greeting_message || "",
                    farewell_enabled: data.farewell_enabled,
                    farewell_message: data.farewell_message || "",
                })
            } else {
                // Default config for new setup
                setConfig(null)
                setFormData({
                    enabled: false,
                    personality: "friendly",
                    custom_personality: "",
                    response_style: "conversational",
                    triggers: ["@bot", "!ask"],
                    greeting_enabled: false,
                    greeting_message: "Welcome to the stream! 👋",
                    farewell_enabled: false,
                    farewell_message: "Thanks for watching! See you next time! 👋",
                })
            }
        } catch (error) {
            console.error("Failed to load chatbot config:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        try {
            setSaving(true)
            await moderationApi.updateChatbotConfig(selectedAccount, formData)
            await loadConfig()
        } catch (error) {
            console.error("Failed to save config:", error)
            alert("Failed to save configuration")
        } finally {
            setSaving(false)
        }
    }

    const handleTest = async () => {
        if (!testMessage.trim()) return
        try {
            setTesting(true)
            const result = await moderationApi.testChatbot(selectedAccount, testMessage)
            setTestResponse(result.response)
        } catch (error) {
            console.error("Failed to test chatbot:", error)
            setTestResponse("Error: Failed to get response from chatbot")
        } finally {
            setTesting(false)
        }
    }

    const addTrigger = () => {
        if (!triggerInput.trim()) return
        const trigger = triggerInput.trim()
        if (!formData.triggers?.includes(trigger)) {
            setFormData({
                ...formData,
                triggers: [...(formData.triggers || []), trigger],
            })
        }
        setTriggerInput("")
    }

    const removeTrigger = (trigger: string) => {
        setFormData({
            ...formData,
            triggers: formData.triggers?.filter((t) => t !== trigger) || [],
        })
    }

    const getAccountName = (accountId: string) => {
        const account = accounts.find((a) => a.id === accountId)
        return account?.channelTitle || "Unknown Channel"
    }

    if (accounts.length === 0 && !loading) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Moderation" },
                    { label: "Chatbot" },
                ]}
            >
                <Card className="border-0 shadow-lg">
                    <CardContent className="py-12 text-center">
                        <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No accounts connected</h3>
                        <p className="text-muted-foreground mb-4">
                            Connect a YouTube account to configure the chatbot
                        </p>
                        <Button onClick={() => window.location.href = "/dashboard/accounts"}>
                            Connect Account
                        </Button>
                    </CardContent>
                </Card>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Moderation" },
                { label: "Chatbot" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Bot className="h-8 w-8" />
                            AI Chatbot Configuration
                        </h1>
                        <p className="text-muted-foreground">
                            Configure your AI-powered chat assistant for live streams
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={() => setTestDialogOpen(true)}>
                            <TestTube className="mr-2 h-4 w-4" />
                            Test Chatbot
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                        >
                            {saving ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <Save className="mr-2 h-4 w-4" />
                            )}
                            Save Changes
                        </Button>
                    </div>
                </div>

                {/* Account Selector */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <Label className="min-w-fit">Select Account</Label>
                            <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                                <SelectTrigger className="w-[300px]">
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
                    </CardContent>
                </Card>

                {loading ? (
                    <div className="space-y-6">
                        <Skeleton className="h-48 w-full" />
                        <Skeleton className="h-48 w-full" />
                    </div>
                ) : (
                    <div className="grid gap-6 md:grid-cols-2">
                        {/* Enable/Disable Card */}
                        <Card className="border-0 shadow-lg md:col-span-2">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                            <Zap className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <CardTitle>Chatbot Status</CardTitle>
                                            <CardDescription>
                                                Enable or disable the AI chatbot for this channel
                                            </CardDescription>
                                        </div>
                                    </div>
                                    <Switch
                                        checked={formData.enabled}
                                        onCheckedChange={(checked) =>
                                            setFormData({ ...formData, enabled: checked })
                                        }
                                    />
                                </div>
                            </CardHeader>
                        </Card>

                        {/* Personality Settings */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                                        <Sparkles className="h-5 w-5 text-purple-500" />
                                    </div>
                                    <div>
                                        <CardTitle>Personality</CardTitle>
                                        <CardDescription>
                                            Choose how the chatbot should interact
                                        </CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-2">
                                    {PERSONALITIES.map((p) => (
                                        <button
                                            key={p.value}
                                            onClick={() =>
                                                setFormData({ ...formData, personality: p.value })
                                            }
                                            className={`p-3 rounded-lg border text-left transition-all ${formData.personality === p.value
                                                    ? "border-primary bg-primary/5"
                                                    : "border-border hover:border-primary/50"
                                                }`}
                                        >
                                            <div className="flex items-center gap-2">
                                                <span className="text-xl">{p.emoji}</span>
                                                <span className="font-medium">{p.label}</span>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {p.description}
                                            </p>
                                        </button>
                                    ))}
                                </div>

                                {formData.personality === "custom" && (
                                    <div className="space-y-2">
                                        <Label>Custom Personality Description</Label>
                                        <Textarea
                                            placeholder="Describe how you want the chatbot to behave..."
                                            value={formData.custom_personality || ""}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    custom_personality: e.target.value,
                                                })
                                            }
                                            rows={3}
                                        />
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Response Style */}
                        <Card className="border-0 shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                                        <MessageSquare className="h-5 w-5 text-blue-500" />
                                    </div>
                                    <div>
                                        <CardTitle>Response Style</CardTitle>
                                        <CardDescription>
                                            How detailed should responses be
                                        </CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <Select
                                    value={formData.response_style}
                                    onValueChange={(value: ChatbotConfig["response_style"]) =>
                                        setFormData({ ...formData, response_style: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {RESPONSE_STYLES.map((style) => (
                                            <SelectItem key={style.value} value={style.value}>
                                                <div>
                                                    <span className="font-medium">{style.label}</span>
                                                    <span className="text-xs text-muted-foreground ml-2">
                                                        - {style.description}
                                                    </span>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>

                                <div className="space-y-2">
                                    <Label>Trigger Keywords</Label>
                                    <div className="flex gap-2">
                                        <Input
                                            placeholder="Add trigger (e.g., @bot, !ask)"
                                            value={triggerInput}
                                            onChange={(e) => setTriggerInput(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && addTrigger()}
                                        />
                                        <Button variant="outline" onClick={addTrigger}>
                                            Add
                                        </Button>
                                    </div>
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {formData.triggers?.map((trigger) => (
                                            <Badge
                                                key={trigger}
                                                variant="secondary"
                                                className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                                                onClick={() => removeTrigger(trigger)}
                                            >
                                                {trigger} ×
                                            </Badge>
                                        ))}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Click a trigger to remove it
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Greeting & Farewell */}
                        <Card className="border-0 shadow-lg md:col-span-2">
                            <CardHeader>
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                                        <Settings2 className="h-5 w-5 text-green-500" />
                                    </div>
                                    <div>
                                        <CardTitle>Automated Messages</CardTitle>
                                        <CardDescription>
                                            Configure greeting and farewell messages
                                        </CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-6 md:grid-cols-2">
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <Label>Greeting Message</Label>
                                            <Switch
                                                checked={formData.greeting_enabled}
                                                onCheckedChange={(checked) =>
                                                    setFormData({ ...formData, greeting_enabled: checked })
                                                }
                                            />
                                        </div>
                                        <Textarea
                                            placeholder="Welcome message when stream starts..."
                                            value={formData.greeting_message || ""}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    greeting_message: e.target.value,
                                                })
                                            }
                                            disabled={!formData.greeting_enabled}
                                            rows={2}
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <Label>Farewell Message</Label>
                                            <Switch
                                                checked={formData.farewell_enabled}
                                                onCheckedChange={(checked) =>
                                                    setFormData({ ...formData, farewell_enabled: checked })
                                                }
                                            />
                                        </div>
                                        <Textarea
                                            placeholder="Goodbye message when stream ends..."
                                            value={formData.farewell_message || ""}
                                            onChange={(e) =>
                                                setFormData({
                                                    ...formData,
                                                    farewell_message: e.target.value,
                                                })
                                            }
                                            disabled={!formData.farewell_enabled}
                                            rows={2}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>

            {/* Test Dialog */}
            <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Test Chatbot</DialogTitle>
                        <DialogDescription>
                            Send a test message to see how the chatbot responds
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Test Message</Label>
                            <Input
                                placeholder="Type a message to test..."
                                value={testMessage}
                                onChange={(e) => setTestMessage(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleTest()}
                            />
                        </div>

                        {testResponse && (
                            <div className="space-y-2">
                                <Label>Chatbot Response</Label>
                                <div className="p-4 bg-muted rounded-lg">
                                    <div className="flex items-start gap-3">
                                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                                            <Bot className="h-4 w-4 text-primary" />
                                        </div>
                                        <p className="text-sm flex-1">{testResponse}</p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setTestDialogOpen(false)}>
                            Close
                        </Button>
                        <Button onClick={handleTest} disabled={testing || !testMessage.trim()}>
                            {testing ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <TestTube className="mr-2 h-4 w-4" />
                            )}
                            Test
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </DashboardLayout>
    )
}
