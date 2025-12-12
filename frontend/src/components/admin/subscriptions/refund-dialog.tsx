"use client"

import { useState } from "react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { AlertTriangle, DollarSign, Loader2, RefreshCcw } from "lucide-react"
import adminApi from "@/lib/api/admin"
import { useToast } from "@/components/ui/toast"

interface RefundDialogProps {
    paymentId: string
    paymentAmount: number
    currency: string
    isOpen: boolean
    onClose: () => void
    onRefunded: () => void
}

export function RefundDialog({
    paymentId,
    paymentAmount,
    currency,
    isOpen,
    onClose,
    onRefunded,
}: RefundDialogProps) {
    const { addToast } = useToast()
    const [isLoading, setIsLoading] = useState(false)
    const [isPartialRefund, setIsPartialRefund] = useState(false)
    const [refundAmount, setRefundAmount] = useState("")
    const [reason, setReason] = useState("")

    const handleRefund = async () => {
        if (!reason.trim()) {
            addToast({
                type: "error",
                title: "Reason required",
                description: "Please provide a reason for the refund",
            })
            return
        }

        if (isPartialRefund) {
            const amount = parseFloat(refundAmount)
            if (isNaN(amount) || amount <= 0) {
                addToast({
                    type: "error",
                    title: "Invalid amount",
                    description: "Please enter a valid refund amount",
                })
                return
            }
            if (amount > paymentAmount) {
                addToast({
                    type: "error",
                    title: "Invalid amount",
                    description: "Refund amount cannot exceed the payment amount",
                })
                return
            }
        }

        setIsLoading(true)
        try {
            await adminApi.processRefund(paymentId, {
                amount: isPartialRefund ? parseFloat(refundAmount) : undefined,
                reason: reason.trim(),
            })
            addToast({
                type: "success",
                title: "Refund processed",
                description: "The refund has been processed successfully",
            })
            onRefunded()
            handleClose()
        } catch (err) {
            console.error("Failed to process refund:", err)
            addToast({
                type: "error",
                title: "Refund failed",
                description: "Failed to process refund. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleClose = () => {
        setIsPartialRefund(false)
        setRefundAmount("")
        setReason("")
        onClose()
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: currency.toUpperCase(),
        }).format(amount)
    }

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <RefreshCcw className="h-5 w-5 text-amber-500" />
                        Process Refund
                    </DialogTitle>
                    <DialogDescription>
                        Process a refund for this payment. This action cannot be undone.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Payment Info */}
                    <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">Payment Amount</span>
                            <span className="text-lg font-semibold">{formatCurrency(paymentAmount)}</span>
                        </div>
                    </div>

                    {/* Partial Refund Toggle */}
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label htmlFor="partial-refund">Partial Refund</Label>
                            <p className="text-xs text-muted-foreground">
                                Refund only a portion of the payment
                            </p>
                        </div>
                        <Switch
                            id="partial-refund"
                            checked={isPartialRefund}
                            onCheckedChange={setIsPartialRefund}
                        />
                    </div>

                    {/* Refund Amount (for partial refunds) */}
                    {isPartialRefund && (
                        <div className="space-y-2">
                            <Label htmlFor="refund-amount">Refund Amount</Label>
                            <div className="relative">
                                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="refund-amount"
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    max={paymentAmount}
                                    placeholder="0.00"
                                    value={refundAmount}
                                    onChange={(e) => setRefundAmount(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Maximum: {formatCurrency(paymentAmount)}
                            </p>
                        </div>
                    )}

                    {/* Reason */}
                    <div className="space-y-2">
                        <Label htmlFor="refund-reason">Reason *</Label>
                        <Textarea
                            id="refund-reason"
                            placeholder="Enter the reason for this refund..."
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={3}
                            className="resize-none"
                        />
                    </div>

                    {/* Warning */}
                    <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                        <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-amber-700 dark:text-amber-300">
                            <p className="font-medium">This action cannot be undone</p>
                            <p className="mt-1">
                                The refund will be processed through the original payment gateway.
                                {isPartialRefund
                                    ? ` ${formatCurrency(parseFloat(refundAmount) || 0)} will be refunded.`
                                    : ` The full amount of ${formatCurrency(paymentAmount)} will be refunded.`}
                            </p>
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={handleClose} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleRefund}
                        disabled={isLoading || !reason.trim()}
                        className="bg-amber-600 hover:bg-amber-700"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <RefreshCcw className="h-4 w-4 mr-2" />
                                Process Refund
                            </>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
