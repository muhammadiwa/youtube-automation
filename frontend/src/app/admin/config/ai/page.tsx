"use client"

import { useState, useEffect, useCallback } from "react"
import { Brain, Sparkles, DollarSign, MessageSquare, Image } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { configApi, type AIConfig } from "@/lib/api/admin"

const defaultConfig: AIConfig = {
    openai_model: "gpt-4",
    openai_max_tokens: 1000,
    title_suggestions_count: 5,
    thumbnail_variations_count: 3,
    thumbnail_width: 1280,
    thumbnail_height: 720,
    chatbot_response_timeout_seconds: 3,
    chatbot_max_response_length: 500,
    sentiment_analysis_enabled: true,
    ai_monthly_budget_usd: 1000.0,
    enable_content_moderation_ai: true,
}

const modelOptions = [
    { value: "gpt-4", label: "GPT-4", description: "Most capable model, best for complex tasks" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo", description: "Faster GPT-4 with lower cost" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo", description: "Fast and cost-effective" },
    { value: "gpt-4o", label: "GPT-4o", description: "Optimized for speed and quality" },
    { value: "gpt-4o-mini", label: "GPT-4o Mini", description: "Smaller, faster, cheaper" },
]

export default function AIConfigPage() {
    const [config, setConfig] = useState<AIConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<AIConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getAIConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch AI config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])


    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateAIConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof AIConfig>(key: K, value: AIConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    return (
        <ConfigFormWrapper
            title="AI Service Configuration"
            description="Configure AI model settings, generation parameters, and budget controls."
            icon={<Brain className="h-5 w-5 text-purple-600 dark:text-purple-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Model Selection */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Model Selection</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="openai_model">OpenAI Model</Label>
                                <Select
                                    value={config.openai_model}
                                    onValueChange={(value) => updateConfig("openai_model", value)}
                                >
                                    <SelectTrigger id="openai_model">
                                        <SelectValue placeholder="Select model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {modelOptions.map((option) => (
                                            <SelectItem key={option.value} value={option.value}>
                                                <div className="flex flex-col">
                                                    <span>{option.label}</span>
                                                    <span className="text-xs text-slate-500">{option.description}</span>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-slate-500">Model used for AI features</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="openai_max_tokens">Max Tokens</Label>
                                <Input
                                    id="openai_max_tokens"
                                    type="number"
                                    min={100}
                                    max={8000}
                                    value={config.openai_max_tokens}
                                    onChange={(e) =>
                                        updateConfig("openai_max_tokens", parseInt(e.target.value) || 1000)
                                    }
                                />
                                <p className="text-xs text-slate-500">100-8000 tokens per request</p>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Generation Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Image className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Generation Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="title_suggestions_count">Title Suggestions Count</Label>
                                <Input
                                    id="title_suggestions_count"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.title_suggestions_count}
                                    onChange={(e) =>
                                        updateConfig("title_suggestions_count", parseInt(e.target.value) || 5)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-10 suggestions per request</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="thumbnail_variations_count">Thumbnail Variations</Label>
                                <Input
                                    id="thumbnail_variations_count"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.thumbnail_variations_count}
                                    onChange={(e) =>
                                        updateConfig("thumbnail_variations_count", parseInt(e.target.value) || 3)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-10 variations per generation</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="thumbnail_width">Thumbnail Width (px)</Label>
                                <Input
                                    id="thumbnail_width"
                                    type="number"
                                    min={640}
                                    max={1920}
                                    value={config.thumbnail_width}
                                    onChange={(e) =>
                                        updateConfig("thumbnail_width", parseInt(e.target.value) || 1280)
                                    }
                                />
                                <p className="text-xs text-slate-500">640-1920 pixels</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="thumbnail_height">Thumbnail Height (px)</Label>
                                <Input
                                    id="thumbnail_height"
                                    type="number"
                                    min={360}
                                    max={1080}
                                    value={config.thumbnail_height}
                                    onChange={(e) =>
                                        updateConfig("thumbnail_height", parseInt(e.target.value) || 720)
                                    }
                                />
                                <p className="text-xs text-slate-500">360-1080 pixels</p>
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="sentiment_analysis_enabled">Sentiment Analysis</Label>
                                <p className="text-xs text-slate-500">
                                    Enable AI-powered sentiment analysis for comments
                                </p>
                            </div>
                            <Switch
                                id="sentiment_analysis_enabled"
                                checked={config.sentiment_analysis_enabled}
                                onCheckedChange={(checked) =>
                                    updateConfig("sentiment_analysis_enabled", checked)
                                }
                            />
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <Label htmlFor="enable_content_moderation_ai">AI Content Moderation</Label>
                                <p className="text-xs text-slate-500">
                                    Use AI to automatically moderate content
                                </p>
                            </div>
                            <Switch
                                id="enable_content_moderation_ai"
                                checked={config.enable_content_moderation_ai}
                                onCheckedChange={(checked) =>
                                    updateConfig("enable_content_moderation_ai", checked)
                                }
                            />
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Chatbot Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Chatbot Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="chatbot_response_timeout_seconds">
                                    Response Timeout (seconds)
                                </Label>
                                <Input
                                    id="chatbot_response_timeout_seconds"
                                    type="number"
                                    min={1}
                                    max={30}
                                    value={config.chatbot_response_timeout_seconds}
                                    onChange={(e) =>
                                        updateConfig("chatbot_response_timeout_seconds", parseInt(e.target.value) || 3)
                                    }
                                />
                                <p className="text-xs text-slate-500">1-30 seconds timeout</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="chatbot_max_response_length">
                                    Max Response Length (chars)
                                </Label>
                                <Input
                                    id="chatbot_max_response_length"
                                    type="number"
                                    min={100}
                                    max={2000}
                                    value={config.chatbot_max_response_length}
                                    onChange={(e) =>
                                        updateConfig("chatbot_max_response_length", parseInt(e.target.value) || 500)
                                    }
                                />
                                <p className="text-xs text-slate-500">100-2000 characters</p>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Budget Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <DollarSign className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Budget Settings</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="ai_monthly_budget_usd">Monthly Budget (USD)</Label>
                            <Input
                                id="ai_monthly_budget_usd"
                                type="number"
                                min={0}
                                max={100000}
                                step={0.01}
                                value={config.ai_monthly_budget_usd}
                                onChange={(e) =>
                                    updateConfig("ai_monthly_budget_usd", parseFloat(e.target.value) || 1000)
                                }
                                className="max-w-[200px]"
                            />
                            <p className="text-xs text-slate-500">
                                Maximum monthly spending on AI services
                            </p>
                        </div>

                        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                            <div className="flex items-start gap-2">
                                <DollarSign className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
                                        Budget Alert
                                    </p>
                                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                                        When AI costs exceed the monthly budget, AI features will be disabled
                                        and an alert will be sent to administrators.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
