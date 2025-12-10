"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { CreditCard, Wallet, Building2, QrCode, Loader2 } from "lucide-react"
import billingApi, { GatewayProvider, GatewayPublicInfo } from "@/lib/api/billing"
import { cn } from "@/lib/utils"

interface PaymentGatewaySelectorProps {
    selectedGateway: GatewayProvider | null
    onSelect: (gateway: GatewayProvider) => void
    rememberPreference: boolean
    onRememberChange: (remember: boolean) => void
    className?: string
    currency?: string
}

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

const gatewayDescriptions: Record<GatewayProvider, string> = {
    stripe: "Pay securely with credit or debit card",
    paypal: "Pay with your PayPal account",
    midtrans: "Indonesian payment methods (GoPay, OVO, DANA)",
    xendit: "Southeast Asian payment methods",
}

export function PaymentGatewaySelector({
    selectedGateway,
    onSelect,
    rememberPreference,
    onRememberChange,
    className,
    currency = "USD",
}: PaymentGatewaySelectorProps) {
    const [gateways, setGateways] = useState<GatewayPublicInfo[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadGateways()
    }, [currency])

    const loadGateways = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await billingApi.getEnabledGateways(currency)
            setGateways(data)
            // Auto-select first gateway if none selected
            if (!selectedGateway && data.length > 0) {
                onSelect(data[0].provider)
            }
        } catch (err) {
            console.error("Failed to load gateways:", err)
            setError("Failed to load payment methods")
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="grid gap-3 sm:grid-cols-2">
                    {[1, 2].map((i) => (
                        <Card key={i} className="border-0 shadow-md animate-pulse">
                            <CardContent className="p-4">
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-muted" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-4 w-20 bg-muted rounded" />
                                        <div className="h-3 w-32 bg-muted rounded" />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={cn("text-center py-8", className)}>
                <p className="text-red-500">{error}</p>
                <button
                    onClick={loadGateways}
                    className="mt-2 text-sm text-primary hover:underline"
                >
                    Try again
                </button>
            </div>
        )
    }

    if (gateways.length === 0) {
        return (
            <div className={cn("text-center py-8 text-muted-foreground", className)}>
                <CreditCard className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No payment methods available</p>
                <p className="text-sm">Please contact support</p>
            </div>
        )
    }

    return (
        <div className={cn("space-y-4", className)}>
            <Label className="text-base font-semibold">Select Payment Method</Label>

            <div className="grid gap-3 sm:grid-cols-2">
                {gateways.map((gateway) => {
                    const Icon = gatewayIcons[gateway.provider] || CreditCard
                    const isSelected = selectedGateway === gateway.provider
                    const gradient = gatewayColors[gateway.provider] || "from-slate-500 to-slate-600"

                    return (
                        <Card
                            key={gateway.provider}
                            className={cn(
                                "border-0 shadow-md cursor-pointer transition-all duration-200",
                                isSelected
                                    ? "ring-2 ring-primary shadow-lg"
                                    : "hover:shadow-lg hover:scale-[1.02]"
                            )}
                            onClick={() => onSelect(gateway.provider)}
                        >
                            <CardContent className="p-4">
                                <div className="flex items-start gap-3">
                                    <div className={cn(
                                        "flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br shadow-md",
                                        gradient
                                    )}>
                                        <Icon className="h-5 w-5 text-white" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="font-semibold">{gateway.display_name}</span>
                                        </div>
                                        <p className="text-sm text-muted-foreground mt-0.5">
                                            {gatewayDescriptions[gateway.provider] || "Secure payment"}
                                        </p>
                                        {gateway.min_amount > 0 && (
                                            <p className="text-xs text-muted-foreground mt-1">
                                                Min: ${gateway.min_amount.toFixed(2)}
                                            </p>
                                        )}
                                    </div>
                                    <div className={cn(
                                        "h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors",
                                        isSelected
                                            ? "border-primary bg-primary"
                                            : "border-muted-foreground/30"
                                    )}>
                                        {isSelected && (
                                            <div className="h-2 w-2 rounded-full bg-white" />
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>

            <div className="flex items-center space-x-2">
                <Checkbox
                    id="remember"
                    checked={rememberPreference}
                    onCheckedChange={(checked) => onRememberChange(checked as boolean)}
                />
                <Label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">
                    Remember my preferred payment method
                </Label>
            </div>
        </div>
    )
}

export default PaymentGatewaySelector
