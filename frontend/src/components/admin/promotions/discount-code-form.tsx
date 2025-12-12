"use client"

import { useState, useEffect } from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, Percent, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { cn } from "@/lib/utils"
import adminApi from "@/lib/api/admin"
import type { DiscountCode, DiscountType } from "@/types/admin"

interface DiscountCodeFormProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    editingCode: DiscountCode | null
    onSuccess: () => void
}

const PLAN_OPTIONS = [
    { value: "free", label: "Free" },
    { value: "basic", label: "Basic" },
    { value: "pro", label: "Pro" },
    { value: "enterprise", label: "Enterprise" },
]

export function DiscountCodeForm({
    open,
    onOpenChange,
    editingCode,
    onSuccess,
}: DiscountCodeFormProps) {
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Form state
    const [code, setCode] = useState("")
    const [discountType, setDiscountType] = useState<DiscountType>("percentage")
    const [discountValue, setDiscountValue] = useState("")
    const [validFrom, setValidFrom] = useState<Date | undefined>(new Date())
    const [validUntil, setValidUntil] = useState<Date | undefined>()
    const [usageLimit, setUsageLimit] = useState("")
    const [applicablePlans, setApplicablePlans] = useState<string[]>([])
    const [isActive, setIsActive] = useState(true)


    // Reset form when dialog opens/closes or editing code changes
    useEffect(() => {
        if (open) {
            if (editingCode) {
                setCode(editingCode.code)
                setDiscountType(editingCode.discount_type)
                setDiscountValue(editingCode.discount_value.toString())
                setValidFrom(new Date(editingCode.valid_from))
                setValidUntil(new Date(editingCode.valid_until))
                setUsageLimit(editingCode.usage_limit?.toString() || "")
                setApplicablePlans(editingCode.applicable_plans || [])
                setIsActive(editingCode.is_active)
            } else {
                // Reset to defaults for new code
                setCode("")
                setDiscountType("percentage")
                setDiscountValue("")
                setValidFrom(new Date())
                setValidUntil(undefined)
                setUsageLimit("")
                setApplicablePlans([])
                setIsActive(true)
            }
            setError(null)
        }
    }, [open, editingCode])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)

        // Validation
        if (!code.trim()) {
            setError("Code is required")
            return
        }
        if (!discountValue || parseFloat(discountValue) <= 0) {
            setError("Discount value must be greater than 0")
            return
        }
        if (discountType === "percentage" && parseFloat(discountValue) > 100) {
            setError("Percentage discount cannot exceed 100%")
            return
        }
        if (!validFrom) {
            setError("Start date is required")
            return
        }
        if (!validUntil) {
            setError("End date is required")
            return
        }
        if (validUntil <= validFrom) {
            setError("End date must be after start date")
            return
        }

        setIsSubmitting(true)

        try {
            if (editingCode) {
                await adminApi.updateDiscountCode(editingCode.id, {
                    discount_type: discountType,
                    discount_value: parseFloat(discountValue),
                    valid_from: validFrom.toISOString(),
                    valid_until: validUntil.toISOString(),
                    usage_limit: usageLimit ? parseInt(usageLimit) : null,
                    applicable_plans: applicablePlans.length > 0 ? applicablePlans : undefined,
                    is_active: isActive,
                })
            } else {
                await adminApi.createDiscountCode({
                    code: code.toUpperCase().trim(),
                    discount_type: discountType,
                    discount_value: parseFloat(discountValue),
                    valid_from: validFrom.toISOString(),
                    valid_until: validUntil.toISOString(),
                    usage_limit: usageLimit ? parseInt(usageLimit) : undefined,
                    applicable_plans: applicablePlans.length > 0 ? applicablePlans : undefined,
                })
            }
            onSuccess()
        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : "Failed to save discount code"
            setError(errorMessage)
        } finally {
            setIsSubmitting(false)
        }
    }

    const togglePlan = (plan: string) => {
        setApplicablePlans(prev =>
            prev.includes(plan)
                ? prev.filter(p => p !== plan)
                : [...prev, plan]
        )
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>
                        {editingCode ? "Edit Discount Code" : "Create Discount Code"}
                    </DialogTitle>
                    <DialogDescription>
                        {editingCode
                            ? "Update the discount code settings"
                            : "Create a new discount code for promotional campaigns"}
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Code */}
                    <div className="space-y-2">
                        <Label htmlFor="code">Code</Label>
                        <Input
                            id="code"
                            value={code}
                            onChange={(e) => setCode(e.target.value.toUpperCase())}
                            placeholder="e.g., SUMMER2024"
                            disabled={!!editingCode}
                            className="font-mono"
                        />
                        {editingCode && (
                            <p className="text-xs text-muted-foreground">Code cannot be changed after creation</p>
                        )}
                    </div>

                    {/* Discount Type & Value */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Discount Type</Label>
                            <Select value={discountType} onValueChange={(v) => setDiscountType(v as DiscountType)}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="percentage">
                                        <div className="flex items-center gap-2">
                                            <Percent className="h-4 w-4" />
                                            Percentage
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="fixed">
                                        <div className="flex items-center gap-2">
                                            <DollarSign className="h-4 w-4" />
                                            Fixed Amount
                                        </div>
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="value">Value</Label>
                            <div className="relative">
                                <Input
                                    id="value"
                                    type="number"
                                    min="0"
                                    max={discountType === "percentage" ? "100" : undefined}
                                    step="0.01"
                                    value={discountValue}
                                    onChange={(e) => setDiscountValue(e.target.value)}
                                    placeholder={discountType === "percentage" ? "10" : "5.00"}
                                    className="pr-8"
                                />
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                    {discountType === "percentage" ? "%" : "$"}
                                </span>
                            </div>
                        </div>
                    </div>


                    {/* Validity Period */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Valid From</Label>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant="outline"
                                        className={cn(
                                            "w-full justify-start text-left font-normal",
                                            !validFrom && "text-muted-foreground"
                                        )}
                                    >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {validFrom ? format(validFrom, "PPP") : "Pick a date"}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                    <Calendar
                                        mode="single"
                                        selected={validFrom}
                                        onSelect={setValidFrom}
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                        <div className="space-y-2">
                            <Label>Valid Until</Label>
                            <Popover>
                                <PopoverTrigger asChild>
                                    <Button
                                        variant="outline"
                                        className={cn(
                                            "w-full justify-start text-left font-normal",
                                            !validUntil && "text-muted-foreground"
                                        )}
                                    >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {validUntil ? format(validUntil, "PPP") : "Pick a date"}
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-auto p-0" align="start">
                                    <Calendar
                                        mode="single"
                                        selected={validUntil}
                                        onSelect={setValidUntil}
                                        disabled={(date) => validFrom ? date < validFrom : false}
                                    />
                                </PopoverContent>
                            </Popover>
                        </div>
                    </div>

                    {/* Usage Limit */}
                    <div className="space-y-2">
                        <Label htmlFor="usageLimit">Usage Limit (optional)</Label>
                        <Input
                            id="usageLimit"
                            type="number"
                            min="1"
                            value={usageLimit}
                            onChange={(e) => setUsageLimit(e.target.value)}
                            placeholder="Leave empty for unlimited"
                        />
                    </div>

                    {/* Applicable Plans */}
                    <div className="space-y-2">
                        <Label>Applicable Plans (optional)</Label>
                        <p className="text-xs text-muted-foreground mb-2">
                            Leave empty to apply to all plans
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {PLAN_OPTIONS.map((plan) => (
                                <Button
                                    key={plan.value}
                                    type="button"
                                    variant={applicablePlans.includes(plan.value) ? "default" : "outline"}
                                    size="sm"
                                    onClick={() => togglePlan(plan.value)}
                                    className="rounded-full"
                                >
                                    {plan.label}
                                </Button>
                            ))}
                        </div>
                    </div>

                    {/* Active Status (only for editing) */}
                    {editingCode && (
                        <div className="flex items-center justify-between rounded-lg border p-3">
                            <div className="space-y-0.5">
                                <Label>Active Status</Label>
                                <p className="text-xs text-muted-foreground">
                                    Disable to prevent code from being used
                                </p>
                            </div>
                            <Switch
                                checked={isActive}
                                onCheckedChange={setIsActive}
                            />
                        </div>
                    )}

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting
                                ? (editingCode ? "Updating..." : "Creating...")
                                : (editingCode ? "Update Code" : "Create Code")}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
