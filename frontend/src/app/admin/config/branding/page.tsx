"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import {
    Palette,
    Type,
    Image as ImageIcon,
    Link as LinkIcon,
    AlertTriangle,
    Upload,
    X,
    ExternalLink,
    Twitter,
    Facebook,
    Instagram,
    Youtube,
    Linkedin,
    Github,
} from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { configApi, type BrandingConfig } from "@/lib/api/admin"
import { useToast } from "@/components/ui/toast"

const defaultConfig: BrandingConfig = {
    platform_name: "YouTube Automation",
    tagline: "Automate Your YouTube Success",
    logo_url: null,
    favicon_url: null,
    primary_color: "#EF4444",
    secondary_color: "#1F2937",
    accent_color: "#10B981",
    support_email: "support@example.com",
    support_url: null,
    documentation_url: null,
    terms_of_service_url: null,
    privacy_policy_url: null,
    social_links: {},
    footer_text: "© 2024 YouTube Automation. All rights reserved.",
    maintenance_mode: false,
    maintenance_message: null,
}

// Social media platforms with icons
const socialPlatforms = [
    { key: "twitter", label: "Twitter / X", icon: Twitter, placeholder: "https://twitter.com/yourhandle" },
    { key: "facebook", label: "Facebook", icon: Facebook, placeholder: "https://facebook.com/yourpage" },
    { key: "instagram", label: "Instagram", icon: Instagram, placeholder: "https://instagram.com/yourhandle" },
    { key: "youtube", label: "YouTube", icon: Youtube, placeholder: "https://youtube.com/@yourchannel" },
    { key: "linkedin", label: "LinkedIn", icon: Linkedin, placeholder: "https://linkedin.com/company/yourcompany" },
    { key: "github", label: "GitHub", icon: Github, placeholder: "https://github.com/yourorg" },
]

export default function BrandingConfigPage() {
    const [config, setConfig] = useState<BrandingConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<BrandingConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)
    const [isUploadingLogo, setIsUploadingLogo] = useState(false)
    const logoInputRef = useRef<HTMLInputElement>(null)
    const { addToast } = useToast()

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getBrandingConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch branding config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateBrandingConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof BrandingConfig>(key: K, value: BrandingConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    const updateSocialLink = (platform: string, url: string) => {
        setConfig((prev) => ({
            ...prev,
            social_links: {
                ...prev.social_links,
                [platform]: url,
            },
        }))
    }

    const removeSocialLink = (platform: string) => {
        setConfig((prev) => {
            const newLinks = { ...prev.social_links }
            delete newLinks[platform]
            return { ...prev, social_links: newLinks }
        })
    }

    const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0]
        if (!file) return

        // Validate file type
        if (!file.type.startsWith("image/")) {
            addToast({
                type: "error",
                title: "Invalid file type",
                description: "Please upload an image file (PNG, JPG, SVG).",
            })
            return
        }

        // Validate file size (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            addToast({
                type: "error",
                title: "File too large",
                description: "Logo file must be less than 2MB.",
            })
            return
        }

        setIsUploadingLogo(true)
        try {
            const response = await configApi.uploadLogo(file)
            // Update the logo URL from the response
            if (response.new_value && typeof response.new_value === "object" && "logo_url" in response.new_value) {
                updateConfig("logo_url", response.new_value.logo_url as string)
            }
            addToast({
                type: "success",
                title: "Logo uploaded",
                description: "Your logo has been uploaded successfully.",
            })
        } catch (error) {
            console.error("Failed to upload logo:", error)
            addToast({
                type: "error",
                title: "Upload failed",
                description: "Failed to upload logo. Please try again.",
            })
        } finally {
            setIsUploadingLogo(false)
            // Reset the input
            if (logoInputRef.current) {
                logoInputRef.current.value = ""
            }
        }
    }

    const removeLogo = () => {
        updateConfig("logo_url", null)
    }

    return (
        <ConfigFormWrapper
            title="Platform Branding"
            description="Customize your platform's appearance, branding, and public-facing information."
            icon={<Palette className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Platform Identity */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Type className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Platform Identity</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="platform_name">Platform Name</Label>
                            <Input
                                id="platform_name"
                                value={config.platform_name}
                                onChange={(e) => updateConfig("platform_name", e.target.value)}
                                placeholder="Your Platform Name"
                            />
                            <p className="text-xs text-slate-500">Displayed in header and emails</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="tagline">Tagline</Label>
                            <Input
                                id="tagline"
                                value={config.tagline}
                                onChange={(e) => updateConfig("tagline", e.target.value)}
                                placeholder="Your catchy tagline"
                            />
                            <p className="text-xs text-slate-500">Short description of your platform</p>
                        </div>
                    </div>
                    <div className="mt-4 space-y-2">
                        <Label htmlFor="footer_text">Footer Text</Label>
                        <Input
                            id="footer_text"
                            value={config.footer_text}
                            onChange={(e) => updateConfig("footer_text", e.target.value)}
                            placeholder="© 2024 Your Company. All rights reserved."
                        />
                        <p className="text-xs text-slate-500">Copyright and legal text shown in footer</p>
                    </div>
                </div>

                <Separator />

                {/* Logo Upload */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <ImageIcon className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Logo</h3>
                    </div>
                    <div className="flex items-start gap-6">
                        {/* Logo Preview */}
                        <div className="flex-shrink-0">
                            <div className="w-32 h-32 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg flex items-center justify-center bg-slate-50 dark:bg-slate-800/50 overflow-hidden">
                                {config.logo_url ? (
                                    <img
                                        src={config.logo_url}
                                        alt="Platform Logo"
                                        className="max-w-full max-h-full object-contain"
                                    />
                                ) : (
                                    <div className="text-center text-slate-400">
                                        <ImageIcon className="h-8 w-8 mx-auto mb-1" />
                                        <span className="text-xs">No logo</span>
                                    </div>
                                )}
                            </div>
                        </div>
                        {/* Upload Controls */}
                        <div className="flex-1 space-y-3">
                            <div className="flex items-center gap-2">
                                <input
                                    ref={logoInputRef}
                                    type="file"
                                    accept="image/*"
                                    onChange={handleLogoUpload}
                                    className="hidden"
                                    id="logo-upload"
                                />
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => logoInputRef.current?.click()}
                                    disabled={isUploadingLogo}
                                >
                                    <Upload className="h-4 w-4 mr-2" />
                                    {isUploadingLogo ? "Uploading..." : "Upload Logo"}
                                </Button>
                                {config.logo_url && (
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={removeLogo}
                                        className="text-red-600 hover:text-red-700"
                                    >
                                        <X className="h-4 w-4 mr-2" />
                                        Remove
                                    </Button>
                                )}
                            </div>
                            <p className="text-xs text-slate-500">
                                Recommended: PNG or SVG, max 2MB. Ideal size: 200x50 pixels.
                            </p>
                            <div className="space-y-2">
                                <Label htmlFor="logo_url">Or enter logo URL</Label>
                                <Input
                                    id="logo_url"
                                    value={config.logo_url || ""}
                                    onChange={(e) => updateConfig("logo_url", e.target.value || null)}
                                    placeholder="https://example.com/logo.png"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Brand Colors */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Palette className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Brand Colors</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="primary_color">Primary Color</Label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="color"
                                    id="primary_color"
                                    value={config.primary_color}
                                    onChange={(e) => updateConfig("primary_color", e.target.value)}
                                    className="w-10 h-10 rounded border border-slate-300 dark:border-slate-600 cursor-pointer"
                                />
                                <Input
                                    value={config.primary_color}
                                    onChange={(e) => updateConfig("primary_color", e.target.value)}
                                    placeholder="#EF4444"
                                    className="flex-1"
                                />
                            </div>
                            <p className="text-xs text-slate-500">Main brand color for buttons and accents</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="secondary_color">Secondary Color</Label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="color"
                                    id="secondary_color"
                                    value={config.secondary_color}
                                    onChange={(e) => updateConfig("secondary_color", e.target.value)}
                                    className="w-10 h-10 rounded border border-slate-300 dark:border-slate-600 cursor-pointer"
                                />
                                <Input
                                    value={config.secondary_color}
                                    onChange={(e) => updateConfig("secondary_color", e.target.value)}
                                    placeholder="#1F2937"
                                    className="flex-1"
                                />
                            </div>
                            <p className="text-xs text-slate-500">Used for text and backgrounds</p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="accent_color">Accent Color</Label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="color"
                                    id="accent_color"
                                    value={config.accent_color}
                                    onChange={(e) => updateConfig("accent_color", e.target.value)}
                                    className="w-10 h-10 rounded border border-slate-300 dark:border-slate-600 cursor-pointer"
                                />
                                <Input
                                    value={config.accent_color}
                                    onChange={(e) => updateConfig("accent_color", e.target.value)}
                                    placeholder="#10B981"
                                    className="flex-1"
                                />
                            </div>
                            <p className="text-xs text-slate-500">Highlights and success states</p>
                        </div>
                    </div>
                    {/* Color Preview */}
                    <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">Preview</p>
                        <div className="flex items-center gap-3">
                            <div
                                className="w-16 h-8 rounded flex items-center justify-center text-white text-xs font-medium"
                                style={{ backgroundColor: config.primary_color }}
                            >
                                Primary
                            </div>
                            <div
                                className="w-16 h-8 rounded flex items-center justify-center text-white text-xs font-medium"
                                style={{ backgroundColor: config.secondary_color }}
                            >
                                Secondary
                            </div>
                            <div
                                className="w-16 h-8 rounded flex items-center justify-center text-white text-xs font-medium"
                                style={{ backgroundColor: config.accent_color }}
                            >
                                Accent
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Important Links */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <LinkIcon className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Important Links</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="support_email">Support Email</Label>
                            <Input
                                id="support_email"
                                type="email"
                                value={config.support_email}
                                onChange={(e) => updateConfig("support_email", e.target.value)}
                                placeholder="support@example.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="support_url">Support URL</Label>
                            <Input
                                id="support_url"
                                type="url"
                                value={config.support_url || ""}
                                onChange={(e) => updateConfig("support_url", e.target.value || null)}
                                placeholder="https://support.example.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="documentation_url">Documentation URL</Label>
                            <Input
                                id="documentation_url"
                                type="url"
                                value={config.documentation_url || ""}
                                onChange={(e) => updateConfig("documentation_url", e.target.value || null)}
                                placeholder="https://docs.example.com"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="terms_of_service_url">Terms of Service URL</Label>
                            <Input
                                id="terms_of_service_url"
                                type="url"
                                value={config.terms_of_service_url || ""}
                                onChange={(e) => updateConfig("terms_of_service_url", e.target.value || null)}
                                placeholder="https://example.com/terms"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="privacy_policy_url">Privacy Policy URL</Label>
                            <Input
                                id="privacy_policy_url"
                                type="url"
                                value={config.privacy_policy_url || ""}
                                onChange={(e) => updateConfig("privacy_policy_url", e.target.value || null)}
                                placeholder="https://example.com/privacy"
                            />
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Social Links */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <ExternalLink className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Social Media Links</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {socialPlatforms.map((platform) => {
                            const Icon = platform.icon
                            const value = config.social_links[platform.key] || ""
                            return (
                                <div key={platform.key} className="space-y-2">
                                    <Label htmlFor={`social_${platform.key}`} className="flex items-center gap-2">
                                        <Icon className="h-4 w-4" />
                                        {platform.label}
                                    </Label>
                                    <div className="flex items-center gap-2">
                                        <Input
                                            id={`social_${platform.key}`}
                                            type="url"
                                            value={value}
                                            onChange={(e) => updateSocialLink(platform.key, e.target.value)}
                                            placeholder={platform.placeholder}
                                            className="flex-1"
                                        />
                                        {value && (
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => removeSocialLink(platform.key)}
                                                className="text-slate-400 hover:text-red-500"
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                <Separator />

                {/* Maintenance Mode */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="h-4 w-4 text-amber-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Maintenance Mode</h3>
                    </div>
                    <div className="space-y-4">
                        <div className={`flex items-center justify-between p-4 rounded-lg border ${config.maintenance_mode
                                ? "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800/50"
                                : "bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700"
                            }`}>
                            <div>
                                <Label htmlFor="maintenance_mode" className="text-base">
                                    Enable Maintenance Mode
                                </Label>
                                <p className={`text-sm ${config.maintenance_mode
                                        ? "text-amber-600 dark:text-amber-400"
                                        : "text-slate-500"
                                    }`}>
                                    {config.maintenance_mode
                                        ? "⚠️ Platform is currently in maintenance mode. Users will see the maintenance message."
                                        : "When enabled, users will see a maintenance message instead of the normal interface."
                                    }
                                </p>
                            </div>
                            <Switch
                                id="maintenance_mode"
                                checked={config.maintenance_mode}
                                onCheckedChange={(checked) => updateConfig("maintenance_mode", checked)}
                            />
                        </div>
                        {config.maintenance_mode && (
                            <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">
                                Maintenance Mode Active
                            </Badge>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="maintenance_message">Maintenance Message</Label>
                            <Textarea
                                id="maintenance_message"
                                value={config.maintenance_message || ""}
                                onChange={(e) => updateConfig("maintenance_message", e.target.value || null)}
                                placeholder="We're currently performing scheduled maintenance. We'll be back shortly!"
                                rows={3}
                            />
                            <p className="text-xs text-slate-500">
                                Message displayed to users when maintenance mode is enabled
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
