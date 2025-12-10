"use client"

import { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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
    Settings,
    Star,
    Edit,
    BarChart3,
    CheckCircle2,
    XCircle,
    Loader2,
    Eye,
    EyeOff,
} from "lucide-react"
import billingApi, { PaymentGateway, GatewayProvider, GatewayCredentials } from "@/lib/api/billing"
import Link from "next/link"
import { cn } from "@/lib/utils"

const gatewayIcons: Record<GatewayProvider, React.ComponentType<{ className?: string }>> = {
    stripe: CreditCard,
    paypal: Wallet,
    midtrans: QrCode,
    xendit: Building2,
}

const gatewayColors: Record<GatewayProvider, string> = {
    stripe: "from-indigo-500 to-indigo-600",
    paypal: "from-blue-500 to-blue-600",
    midtrans: "from-teal-500 to-teal-600",
    xendit: "from-cyan-500 to-cyan-600",
}

export default function PaymentGatewaysAdminPage() {
    const [gateways, setGateways] = useState<PaymentGateway[]>([])
    const [loading, setLoading] = useState(true)
    const [editingGateway, setEditingGateway] = useState<PaymentGateway | null>(null)
    const [credentials, setCredentials] = useState<GatewayCredentials>({
        api_key: "",
        api_secret: "",
        webhook_secret: "",
        sandbox_mode: true,
    })
    const [showSecrets, setShowSecrets] = useState(false)
    const [saving, setSaving] = useState(false)
    const [validating, setValidating] = useState(false)
    const [validationResult, setValidationResult] = useState<{ valid: boolean; message?: string } | null>(null)

    useEffect(() => {
        loadGateways()
    }, [])

    const loadGateways = async () => {
        setLoading(true)
        try {
            const data = await billingApi.getAllGateways()
            setGateways(data)
        } catch (error) {
            console.error("Failed to load gateways:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleToggleEnabled = async (gateway: PaymentGateway) => {
        try {
            if (gateway.is_enabled) {
                await billingApi.disableGateway(gateway.provider)
            } else {
                await billingApi.enableGateway(gateway.provider)
            }
            await loadGateways()
        } catch (error) {
            console.error("Failed to toggle gateway:", error)
        }
    }

    const handleSetDefault = async (provider: GatewayProvider) => {
        try {
            await billingApi.setDefaultGateway(provider)
            await loadGateways()
        } catch (error) {
            console.error("Failed to set default gateway:", error)
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
        setValidationResult(null)
    }

    const handleValidateCredentials = async () => {
        if (!editingGateway) return
        setValidating(true)
        setValidationResult(null)
        try {
            // First save credentials, then validate
            await billingApi.configureGateway(editingGateway.provider, credentials)
            const result = await billingApi.validateGatewayCredentials(editingGateway.provider)
            setValidationResult(result)
        } catch (error: any) {
            setValidationResult({ valid: false, message: error.message || "Validation failed" })
        } finally {
            setValidating(false)
        }
    }

    const handleSaveCredentials = async () => {
        if (!editingGateway) return
        setSaving(true)
        try {
            await billingApi.configureGateway(editingGateway.provider, credentials)
            await loadGateways()
            setEditingGateway(null)
        } catch (error) {
            console.error("Failed to save credentials:", error)
        } finally {
            setSaving(false)
        }
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Admin", href: "/admin" },
                { label: "Payment Gateways" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                            <Settings className="h-7 w-7" />
                            Payment Gateways
                        </h1>
                        <p className="text-muted-foreground">
                            Configure and manage payment gateway integrations
                        </p>
                    </div>
                    <Link href="/admin/payment-gateways/stats">
                        <Button variant="outline">
                            <BarChart3 className="h-4 w-4 mr-2" />
                            View Statistics
                        </Button>
                    </Link>
                </div>

                {/* Gateways Grid */}
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2">
                        {gateways.map((gateway) => {
                            const Icon = gatewayIcons[gateway.provider]
                            const gradient = gatewayColors[gateway.provider]

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
                                            <Switch
                                                checked={gateway.is_enabled}
                                                onCheckedChange={() => handleToggleEnabled(gateway)}
                                            />
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
                                                    {gateway.fixed_fee > 0 && ` + $${gateway.fixed_fee.toFixed(2)}`}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Currencies</span>
                                                <span>{gateway.supported_currencies.join(", ")}</span>
                                            </div>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">Min Amount</span>
                                                <span>${gateway.min_amount.toFixed(2)}</span>
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

                            {/* Validation Result */}
                            {validationResult && (
                                <div className={cn(
                                    "p-3 rounded-lg flex items-center gap-2",
                                    validationResult.valid
                                        ? "bg-green-500/10 border border-green-500/20"
                                        : "bg-red-500/10 border border-red-500/20"
                                )}>
                                    {validationResult.valid ? (
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                    ) : (
                                        <XCircle className="h-5 w-5 text-red-500" />
                                    )}
                                    <span className={cn(
                                        "text-sm",
                                        validationResult.valid ? "text-green-600" : "text-red-600"
                                    )}>
                                        {validationResult.valid ? "Credentials are valid" : validationResult.message}
                                    </span>
                                </div>
                            )}
                        </div>

                        <DialogFooter className="flex-col sm:flex-row gap-2">
                            <Button
                                variant="outline"
                                onClick={handleValidateCredentials}
                                disabled={validating || !credentials.api_key || !credentials.api_secret}
                            >
                                {validating ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Validating...
                                    </>
                                ) : (
                                    "Validate Credentials"
                                )}
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
        </DashboardLayout>
    )
}
