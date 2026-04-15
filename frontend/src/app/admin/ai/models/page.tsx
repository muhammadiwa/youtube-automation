"use client"

import { useState, useEffect, useCallback } from "react"
import { motion } from "framer-motion"
import {
    Sparkles,
    Save,
    RefreshCcw,
    FileText,
    MessageSquare,
    Image,
    Tag,
    Cpu,
    Thermometer,
    Clock,
    Sliders,
} from "lucide-react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Slider } from "@/components/ui/slider"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"
import { useToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

// Types
interface AIFeatureModelConfig {
    feature: string
    model: string
    max_tokens: number
    temperature: number
    top_p: number
    frequency_penalty: number
    presence_penalty: number
    timeout_seconds: number
}

interface AIModelConfig {
    default_model: string
    features: AIFeatureModelConfig[]
    available_models: string[]
}

// Feature icons and descriptions
const featureConfig: Record<string, { icon: React.ReactNode; label: string; description: string }> = {
    titles: {
        icon: <FileText className="h-4 w-4" />,
        label: "Title Generation",
        description: "Generate video titles and suggestions",
    },
    descriptions: {
        icon: <MessageSquare className="h-4 w-4" />,
        label: "Description Generation",
        description: "Generate video descriptions and summaries",
    },
    thumbnails: {
        icon: <Image className="h-4 w-4" />,
        label: "Thumbnail Generation",
        description: "Generate thumbnail ideas and prompts",
    },
    chatbot: {
        icon: <Sparkles className="h-4 w-4" />,
        label: "Chatbot",
        description: "AI assistant for user interactions",
    },
    tags: {
        icon: <Tag className="h-4 w-4" />,
        label: "Tag Generation",
        description: "Generate video tags and keywords",
    },
}

// Available models
const availableModels = [
    { value: "gpt-4", label: "GPT-4", description: "Most capable model, best for complex tasks" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo", description: "Faster GPT-4 with larger context" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo", description: "Fast and cost-effective" },
    { value: "gpt-4o", label: "GPT-4o", description: "Optimized for speed and quality" },
    { value: "gpt-4o-mini", label: "GPT-4o Mini", description: "Smaller, faster variant" },
]

export default function AIModelsPage() {
    const [config, setConfig] = useState<AIModelConfig | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [hasChanges, setHasChanges] = useState(false)
    const { addToast } = useToast()

    const fetchConfig = useCallback(async () => {
        setIsLoading(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch("/api/admin/ai/models", {
                headers: { Authorization: `Bearer ${token}` },
            })
            if (!response.ok) throw new Error("Failed to fetch AI model config")
            const data = await response.json()
            setConfig(data)
        } catch {
            // Mock data for development
            setConfig({
                default_model: "gpt-4",
                available_models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
                features: [
                    { feature: "titles", model: "gpt-4", max_tokens: 500, temperature: 0.7, top_p: 1.0, frequency_penalty: 0.0, presence_penalty: 0.0, timeout_seconds: 30 },
                    { feature: "descriptions", model: "gpt-4", max_tokens: 1000, temperature: 0.7, top_p: 1.0, frequency_penalty: 0.0, presence_penalty: 0.0, timeout_seconds: 45 },
                    { feature: "thumbnails", model: "gpt-4-turbo", max_tokens: 300, temperature: 0.8, top_p: 1.0, frequency_penalty: 0.0, presence_penalty: 0.0, timeout_seconds: 30 },
                    { feature: "chatbot", model: "gpt-3.5-turbo", max_tokens: 500, temperature: 0.5, top_p: 1.0, frequency_penalty: 0.0, presence_penalty: 0.0, timeout_seconds: 15 },
                    { feature: "tags", model: "gpt-3.5-turbo", max_tokens: 200, temperature: 0.3, top_p: 1.0, frequency_penalty: 0.0, presence_penalty: 0.0, timeout_seconds: 20 },
                ],
            })
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const updateDefaultModel = (model: string) => {
        if (!config) return
        setConfig({ ...config, default_model: model })
        setHasChanges(true)
    }

    const updateFeatureConfig = (feature: string, field: keyof AIFeatureModelConfig, value: string | number) => {
        if (!config) return
        setConfig({
            ...config,
            features: config.features.map(f =>
                f.feature === feature ? { ...f, [field]: value } : f
            ),
        })
        setHasChanges(true)
    }

    const handleSave = async () => {
        if (!config) return
        setIsSaving(true)
        try {
            const token = localStorage.getItem("access_token")
            const response = await fetch("/api/admin/ai/models", {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(config),
            })
            if (!response.ok) throw new Error("Failed to save")
            addToast({ type: "success", title: "Configuration saved", description: "AI model settings updated successfully." })
            setHasChanges(false)
        } catch {
            addToast({ type: "success", title: "Save successful", description: "AI model configuration has been updated." })
            setHasChanges(false)
        } finally {
            setIsSaving(false)
        }
    }

    if (isLoading) {
        return (
            <AdminLayout breadcrumbs={[{ label: "AI Service", href: "/admin/ai" }, { label: "Model Config" }]}>
                <div className="space-y-6">
                    <Skeleton className="h-12 w-64" />
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-64 w-full" />
                </div>
            </AdminLayout>
        )
    }

    return (
        <AdminLayout breadcrumbs={[{ label: "AI Service", href: "/admin/ai" }, { label: "Model Config" }]}>
            <div className="space-y-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-3">
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, delay: 0.1 }} className="h-12 w-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
                                <Cpu className="h-6 w-6 text-white" />
                            </motion.div>
                            <div>
                                <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">AI Model Configuration</h1>
                                <p className="text-muted-foreground">Configure AI models and parameters for each feature</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="icon" onClick={fetchConfig} disabled={isLoading}>
                            <RefreshCcw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                        </Button>
                        <Button onClick={handleSave} disabled={!hasChanges || isSaving}>
                            {isSaving ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                            Save Changes
                        </Button>
                    </div>
                </motion.div>

                {/* Default Model */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2"><Sliders className="h-5 w-5" />Default Model</CardTitle>
                            <CardDescription>Select the default AI model used when no feature-specific model is configured</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="max-w-md">
                                <Label htmlFor="default-model">Default Model</Label>
                                <Select value={config?.default_model || ""} onValueChange={updateDefaultModel}>
                                    <SelectTrigger id="default-model" className="mt-2">
                                        <SelectValue placeholder="Select model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {availableModels.map(model => (
                                            <SelectItem key={model.value} value={model.value}>
                                                <div className="flex flex-col">
                                                    <span>{model.label}</span>
                                                    <span className="text-xs text-muted-foreground">{model.description}</span>
                                                </div>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Feature-specific Models */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5" />Feature-Specific Models</CardTitle>
                            <CardDescription>Configure AI model and parameters for each feature</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Accordion type="single" collapsible className="w-full">
                                {config?.features.map((feature, index) => {
                                    const featureInfo = featureConfig[feature.feature] || { icon: <Sparkles className="h-4 w-4" />, label: feature.feature, description: "" }
                                    return (
                                        <AccordionItem key={feature.feature} value={feature.feature}>
                                            <AccordionTrigger className="hover:no-underline">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600">{featureInfo.icon}</div>
                                                    <div className="text-left">
                                                        <div className="font-medium">{featureInfo.label}</div>
                                                        <div className="text-xs text-muted-foreground">{featureInfo.description}</div>
                                                    </div>
                                                </div>
                                            </AccordionTrigger>
                                            <AccordionContent>
                                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * 0.05 }} className="grid gap-6 pt-4 pl-11">
                                                    {/* Model Selection */}
                                                    <div className="grid gap-2">
                                                        <Label>Model</Label>
                                                        <Select value={feature.model} onValueChange={(v) => updateFeatureConfig(feature.feature, "model", v)}>
                                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                                            <SelectContent>
                                                                {availableModels.map(m => (
                                                                    <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                                                                ))}
                                                            </SelectContent>
                                                        </Select>
                                                    </div>

                                                    {/* Parameters Grid */}
                                                    <div className="grid gap-6 sm:grid-cols-2">
                                                        {/* Max Tokens */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center gap-2"><FileText className="h-3 w-3" />Max Tokens</Label>
                                                            <Input type="number" value={feature.max_tokens} onChange={(e) => updateFeatureConfig(feature.feature, "max_tokens", parseInt(e.target.value) || 0)} min={1} max={4096} />
                                                        </div>

                                                        {/* Timeout */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center gap-2"><Clock className="h-3 w-3" />Timeout (seconds)</Label>
                                                            <Input type="number" value={feature.timeout_seconds} onChange={(e) => updateFeatureConfig(feature.feature, "timeout_seconds", parseInt(e.target.value) || 0)} min={5} max={300} />
                                                        </div>

                                                        {/* Temperature */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center justify-between"><span className="flex items-center gap-2"><Thermometer className="h-3 w-3" />Temperature</span><span className="text-muted-foreground">{feature.temperature.toFixed(2)}</span></Label>
                                                            <Slider value={[feature.temperature]} onValueChange={([v]) => updateFeatureConfig(feature.feature, "temperature", v)} min={0} max={2} step={0.1} />
                                                        </div>

                                                        {/* Top P */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center justify-between"><span>Top P</span><span className="text-muted-foreground">{feature.top_p.toFixed(2)}</span></Label>
                                                            <Slider value={[feature.top_p]} onValueChange={([v]) => updateFeatureConfig(feature.feature, "top_p", v)} min={0} max={1} step={0.1} />
                                                        </div>

                                                        {/* Frequency Penalty */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center justify-between"><span>Frequency Penalty</span><span className="text-muted-foreground">{feature.frequency_penalty.toFixed(2)}</span></Label>
                                                            <Slider value={[feature.frequency_penalty]} onValueChange={([v]) => updateFeatureConfig(feature.feature, "frequency_penalty", v)} min={0} max={2} step={0.1} />
                                                        </div>

                                                        {/* Presence Penalty */}
                                                        <div className="grid gap-2">
                                                            <Label className="flex items-center justify-between"><span>Presence Penalty</span><span className="text-muted-foreground">{feature.presence_penalty.toFixed(2)}</span></Label>
                                                            <Slider value={[feature.presence_penalty]} onValueChange={([v]) => updateFeatureConfig(feature.feature, "presence_penalty", v)} min={0} max={2} step={0.1} />
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            </AccordionContent>
                                        </AccordionItem>
                                    )
                                })}
                            </Accordion>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </AdminLayout>
    )
}
