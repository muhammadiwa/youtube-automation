"use client"

import { useState, useEffect } from "react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    AlertTriangle,
    CreditCard,
    Wallet,
    Building2,
    QrCode,
    Loader2,
    RefreshCw,
} from "lucide-react"
import billingApi, { GatewayPublicInfo, GatewayProvider } from "@/lib/api/billing"
import { cn } from "@/lib/utils"

interface PaymentRetryModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    paymentId: string
    failedGateway: GatewayProvider
    errorMessage: string
    onRetrySuccess: () => void
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

export function PaymentRetryModal({
    open,
    onOpenChange,
    paymentId,
    failedGateway,
    errorMessage,
    onRetrySuccess,
}: PaymentRetryModalProps) {
    const [gateways, setGateways] = useState<GatewayPublicInfo[]>([])
    const [selectedGateway, setSelectedGateway] = useState<GatewayProvider | null>(null)
    const [loading, setLoading] = useState(true)
    const [retrying, setRetrying] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (open) {
            loadAlternativeGateways()
        }
    }, [open, paymentId, failedGateway])

    const loadAlternativeGateways = async () => {
        setLoading(true)
        try {
            // Try to get alternatives from the payment API first
            let alternatives: GatewayPublicInfo[] = []
            try {
                alternatives = await billingApi.getAlternativeGateways(paymentId)
            } catch {
                // Fallback to getting all enabled gateways and filtering
                const allGateways = await billingApi.getEnabledGateways()
                alternatives = allGateways.filter(g => g.provider !== failedGateway)
            }
            setGateways(alternatives)
            // Auto-select first alternative
            if (alternatives.length > 0) {
                setSelectedGateway(alternatives[0].provider)
            }
        } catch (error) {
            console.error("Failed to load gateways:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleRetry = async () => {
        if (!selectedGateway) return

        setRetrying(true)
        setError(null)

        try {
            const session = await billingApi.retryPaymentWithGateway(paymentId, selectedGateway)
            if (session.checkout_url) {
                window.location.href = session.checkout_url
            }
            onRetrySuccess()
        } catch (err: any) {
            setError(err.message || "Failed to retry payment")
        } finally {
            setRetrying(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        Payment Failed
                    </DialogTitle>
                    <DialogDescription>
                        Your payment with {failedGateway} could not be processed. Try a different payment method.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Error Message */}
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <p className="text-sm text-red-600 dark:text-red-400">
                            {errorMessage}
                        </p>
                    </div>

                    {/* Alternative Gateways */}
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : gateways.length > 0 ? (
                        <div className="space-y-3">
                            <p className="text-sm font-medium">Select alternative payment method:</p>
                            {gateways.map((gateway) => {
                                const Icon = gatewayIcons[gateway.provider]
                                const isSelected = selectedGateway === gateway.provider
                                const gradient = gatewayColors[gateway.provider]

                                return (
                                    <Card
                                        key={gateway.id}
                                        className={cn(
                                            "border cursor-pointer transition-all duration-200",
                                            isSelected
                                                ? "ring-2 ring-primary border-primary"
                                                : "hover:border-primary/50"
                                        )}
                                        onClick={() => setSelectedGateway(gateway.provider)}
                                    >
                                        <CardContent className="p-3">
                                            <div className="flex items-center gap-3">
                                                <div className={cn(
                                                    "flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br",
                                                    gradient
                                                )}>
                                                    <Icon className="h-4 w-4 text-white" />
                                                </div>
                                                <div className="flex-1">
                                                    <span className="font-medium text-sm">
                                                        {gateway.display_name}
                                                    </span>
                                                </div>
                                                <div className={cn(
                                                    "h-4 w-4 rounded-full border-2 flex items-center justify-center",
                                                    isSelected
                                                        ? "border-primary bg-primary"
                                                        : "border-muted-foreground/30"
                                                )}>
                                                    {isSelected && (
                                                        <div className="h-1.5 w-1.5 rounded-full bg-white" />
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-4 text-muted-foreground">
                            No alternative payment methods available
                        </div>
                    )}

                    {/* Retry Error */}
                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleRetry}
                        disabled={!selectedGateway || retrying || gateways.length === 0}
                    >
                        {retrying ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Retrying...
                            </>
                        ) : (
                            <>
                                <RefreshCw className="h-4 w-4 mr-2" />
                                Retry Payment
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default PaymentRetryModal
