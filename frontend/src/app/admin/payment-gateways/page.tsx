"use client"

import { useState, useEffect, useCallback } from "react"
import { AdminLayout } from "@/components/admin"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    CreditCard,
    Wallet,
    Building2,
    QrCode,
    Star,
    Edit,
    BarChart3,
    Loader2,
    Eye,
    EyeOff,
    RefreshCw,
} from "lucide-react"
import adminApi from "@/lib/api/admin"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { useToast } from "@/components/ui/toast"

// Types for payment gateway admin - must match backend response exactly
interface PaymentGateway {
    id: string
    provider: string
    display_name: string
    is_enabled: boolean
    is_default: boolean
    sandbox_mode: boolean
    has_credentials: boolean
    supported_currencies: string[]
    supported_payment_methods: string[]
    transaction_fee_percent: number
    fixed_fee: number
    min_amount: number
    max_amount: number | null
    created_at: string
    updated_at: string
}

interface GatewayCredentials {
    api_key: string
    api_secret: string
    webhook_secret?: string
    sandbox_mode: boolean
}

const gatewayIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    stripe: CreditCard,
    paypal: Wallet,
    midtrans: QrCode,
    xendit: Building2,
}

const gatewayColors: Record<string, string> = {
    stripe: "from-indigo-500 to-indigo-600",
    paypal: "from-blue-500 to-blue-600",
    midtrans: "from-teal-500 to-teal-600",
    xendit: "from-cyan-500 to-cyan-600",
}

const defaultGatewayIcon = CreditCard
const defaultGatewayColor = "from-gray-500 to-gray-600"

// Format amount with appropriate currency symbol based on gateway's primary currency
const formatAmount = (amount: number, currencies: string[]): string => {
    const primaryCurrency = currencies[0] || "USD"

    // Currency formatting based on primary supported currency
    const currencyFormats: Record<string, { symbol: string; locale: string; decimals: number }> = {
        USD: { symbol: "$", locale: "en-US", decimals: 2 },
        EUR: { symbol: "€", locale: "de-DE", decimals: 2 },
        GBP: { symbol: "£", locale: "en-GB", decimals: 2 },
        IDR: { symbol: "Rp", locale: "id-ID", decimals: 0 },
        JPY: { symbol: "¥", locale: "ja-JP", decimals: 0 },
        SGD: { symbol: "S$", locale: "en-SG", decimals: 2 },
        AUD: { symbol: "A$", locale: "en-AU", decimals: 2 },
        CAD: { symbol: "C$", locale: "en-CA", decimals: 2 },
        PHP: { symbol: "₱", locale: "en-PH", decimals: 2 },
        VND: { symbol: "₫", locale: "vi-VN", decimals: 0 },
        THB: { symbol: "฿", locale: "th-TH", decimals: 2 },
        MYR: { symbol: "RM", locale: "ms-MY", decimals: 2 },
    }

    const format = currencyFormats[primaryCurrency] || currencyFormats.USD
    const formattedNumber = amount.toLocaleString(format.locale, {
        minimumFractionDigits: format.decimals,
        maximumFractionDigits: format.decimals,
    })

    return `${format.symbol}${formattedNumber}`
}

export default function PaymentGatewaysAdminPage() {
    const [gateways, setGateways] = useState<PaymentGateway[]>([])
    const [loading, setLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [editingGateway, setEditingGateway] = useState<PaymentGateway | null>(null)
    const [credentials, setCredentials] = useState<GatewayCredentials>({
        api_key: "",
        api_secret: "",
        webhook_secret: "",
        sandbox_mode: true,
    })
    const [showSecrets, setShowSecrets] = useState(false)
    const [saving, setSaving] = useState(false)
    const [togglingGateway, setTogglingGateway] = useState<string | null>(null)
    const { addToast } = useToast()

    const loadGateways = useCallback(async () => {
        try {
            // Backend returns array directly
            const gateways = await adminApi.getPaymentGateways()
            if (Array.isArray(gateways)) {
                setGateways(gateways)
            } else {
                console.error("Invalid response - expected array:", gateways)
                setGateways([])
            }
        } catch (error) {
            console.error("Failed to load gateways:", error)
            setGateways([])
            addToast({
                type: "error",
                title: "Failed to load gateways",
                description: error instanceof Error ? error.message : "Please try again later",
            })
        } finally {
            setLoading(false)
            setIsRefreshing(false)
        }
    }, [addToast])

    useEffect(() => {
        loadGateways()
    }, [loadGateways])

    const handleRefresh = () => {
        setIsRefreshing(true)
        loadGateways()
    }

    const handleToggleEnabled = async (gateway: PaymentGateway) => {
        setTogglingGateway(gateway.provider)
        try {
            await adminApi.updateGatewayStatus(gateway.provider, {
                is_enabled: !gateway.is_enabled,
            })
            addToast({
                type: "success",
                title: gateway.is_enabled ? "Gateway disabled" : "Gateway enabled",
                description: `${gateway.display_name} has been ${gateway.is_enabled ? "disabled" : "enabled"}`,
            })
            await loadGateways()
        } catch (error) {
            console.error("Failed to toggle gateway:", error)
            addToast({
                type: "error",
                title: "Failed to update gateway",
                description: "Please try again later",
            })
        } finally {
            setTogglingGateway(null)
        }
    }

    const handleEditCredentials = (gateway: PaymentGateway) => {
        setEditingGateway(gateway)
        setCredentials({
            api_key: "",
            api_secret: "",
            webhook_secret: "",
            sandbox_mode: gateway.sandbox_mode,
        })
    }

    const handleSaveCredentials = async () => {
        if (!editingGateway) return
        setSaving(true)
        try {
            await adminApi.updateGatewayCredentials(editingGateway.provider, credentials)
            addToast({
                type: "success",
                title: "Credentials updated",
                description: `${editingGateway.display_name} credentials have been updated`,
            })
            await loadGateways()
            setEditingGateway(null)
        } catch (error) {
            console.error("Failed to save credentials:", error)
            addToast({
                type: "error",
                title: "Failed to save credentials",
                description: "Please check your credentials and try again",
            })
        } finally {
            setSaving(false)
        }
    }

    const handleSetDefault = async (provider: string) => {
        try {
            await adminApi.setDefaultGateway(provider)
            addToast({
                type: "success",
                title: "Default gateway updated",
                description: `${provider} is now the default payment gateway`,
            })
            await loadGateways()
        } catch (error) {
            console.error("Failed to set default gateway:", error)
            addToast({
                type: "error",
                title: "Failed to set default gateway",
                description: "Please try again later",
            })
        }
    }

    return (
        <AdminLayout
            breadcrumbs={[
                { label: "Billing", href: "/admin/payment-gateways" },
                { label: "Payment Gateways" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                            <CreditCard className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                                Payment Gateways
                            </h1>
                            <p className="text-sm text-slate-500 dark:text-slate-400">
                                Configure and manage payment gateway integrations
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
                            Refresh
                        </Button>
                        <Link href="/admin/payment-gateways/stats">
                            <Button variant="outline">
                                <BarChart3 className="h-4 w-4 mr-2" />
                                View Statistics
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Gateways Grid */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : gateways.length === 0 ? (
                    <Card className="border-0 shadow-lg">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <CreditCard className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No Payment Gateways</h3>
                            <p className="text-sm text-muted-foreground text-center max-w-md">
                                No payment gateways have been configured yet.
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2">
                        {gateways.map((gateway) => {
                            const Icon = gatewayIcons[gateway.provider] || defaultGatewayIcon
                            const gradient = gatewayColors[gateway.provider] || defaultGatewayColor

                            return (
                                <Card key={gateway.id} className="border-0 shadow-lg">
                                    <CardContent className="p-6">
                                        <div className="flex items-start justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div className={cn(
                                                    "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg",
                                                    gradient
                                                )}>
                                                    <Icon className="h-6 w-6 text-white" />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="font-semibold">{gateway.display_name}</h3>
                                                        {gateway.is_default && (
                                                            <Badge className="bg-amber-500">
                                                                <Star className="h-3 w-3 mr-1" />
                                                                Default
                                                            </Badge>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-muted-foreground capitalize">
                                                        {gateway.provider}
                                                    </p>
                                                </div>
                                            </div>
                                            {togglingGateway === gateway.provider ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Switch
                                                    checked={gateway.is_enabled}
                                                    onCheckedChange={() => handleToggleEnabled(gateway)}
                                                />
                                            )}
                                        </div>

                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Mode</span>
                                                <Badge variant={gateway.sandbox_mode ? "secondary" : "default"}>
                                                    {gateway.sandbox_mode ? "Sandbox" : "Production"}
                                                </Badge>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Transaction Fee</span>
                                                <span>
                                                    {gateway.transaction_fee_percent}%
                                                    {gateway.fixed_fee > 0 && ` + ${formatAmount(gateway.fixed_fee, gateway.supported_currencies)}`}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Currencies</span>
                                                <span>{gateway.supported_currencies.join(", ")}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Min Amount</span>
                                                <span>{formatAmount(gateway.min_amount, gateway.supported_currencies)}</span>
                                            </div>
                                        </div>

                                        <div className="flex gap-2 mt-4 pt-4 border-t">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="flex-1"
                                                onClick={() => handleEditCredentials(gateway)}
                                            >
                                                <Edit className="h-4 w-4 mr-2" />
                                                Edit Credentials
                                            </Button>
                                            {!gateway.is_default && gateway.is_enabled && (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleSetDefault(gateway.provider)}
                                                >
                                                    <Star className="h-4 w-4 mr-2" />
                                                    Set Default
                                                </Button>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>
                )}

                {/* Edit Credentials Dialog */}
                <Dialog open={!!editingGateway} onOpenChange={() => setEditingGateway(null)}>
                    <DialogContent className="sm:max-w-md">
                        <DialogHeader>
                            <DialogTitle>
                                Edit {editingGateway?.display_name} Credentials
                            </DialogTitle>
                            <DialogDescription>
                                Update API credentials for this payment gateway
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="api_key">API Key</Label>
                                <div className="relative">
                                    <Input
                                        id="api_key"
                                        type={showSecrets ? "text" : "password"}
                                        placeholder="Enter API key"
                                        value={credentials.api_key}
                                        onChange={(e) => setCredentials({ ...credentials, api_key: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="api_secret">API Secret</Label>
                                <div className="relative">
                                    <Input
                                        id="api_secret"
                                        type={showSecrets ? "text" : "password"}
                                        placeholder="Enter API secret"
                                        value={credentials.api_secret}
                                        onChange={(e) => setCredentials({ ...credentials, api_secret: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="webhook_secret">Webhook Secret (Optional)</Label>
                                <Input
                                    id="webhook_secret"
                                    type={showSecrets ? "text" : "password"}
                                    placeholder="Enter webhook secret"
                                    value={credentials.webhook_secret || ""}
                                    onChange={(e) => setCredentials({ ...credentials, webhook_secret: e.target.value })}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowSecrets(!showSecrets)}
                                >
                                    {showSecrets ? (
                                        <>
                                            <EyeOff className="h-4 w-4 mr-2" />
                                            Hide Secrets
                                        </>
                                    ) : (
                                        <>
                                            <Eye className="h-4 w-4 mr-2" />
                                            Show Secrets
                                        </>
                                    )}
                                </Button>
                                <div className="flex items-center gap-2">
                                    <Label htmlFor="sandbox_mode" className="text-sm">Sandbox Mode</Label>
                                    <Switch
                                        id="sandbox_mode"
                                        checked={credentials.sandbox_mode}
                                        onCheckedChange={(checked) => setCredentials({ ...credentials, sandbox_mode: checked })}
                                    />
                                </div>
                            </div>

                        </div>

                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => setEditingGateway(null)}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleSaveCredentials}
                                disabled={saving || !credentials.api_key || !credentials.api_secret}
                            >
                                {saving ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    "Save Credentials"
                                )}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </AdminLayout>
    )
}
