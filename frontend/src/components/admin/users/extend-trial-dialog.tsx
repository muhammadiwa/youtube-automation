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
import { Calendar, Loader2 } from "lucide-react"
import adminApi from "@/lib/api/admin"
import type { UserDetail } from "@/types/admin"
import { useToast } from "@/components/ui/toast"

interface ExtendTrialDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    user: UserDetail
    onSuccess?: () => void
}

export function ExtendTrialDialog({
    open,
    onOpenChange,
    user,
    onSuccess,
}: ExtendTrialDialogProps) {
    const { addToast } = useToast()
    const [days, setDays] = useState(7)
    const [reason, setReason] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    const handleExtend = async () => {
        if (days < 1 || days > 365) {
            addToast({
                type: "error",
                title: "Invalid days",
                description: "Days must be between 1 and 365.",
            })
            return
        }

        setIsLoading(true)
        try {
            const response = await adminApi.extendUserTrial(user.id, {
                days,
                reason: reason || undefined,
            })
            addToast({
                type: "success",
                title: "Trial extended",
                description: `Trial extended by ${response.days_extended} days.`,
            })
            onOpenChange(false)
            setDays(7)
            setReason("")
            onSuccess?.()
        } catch (err) {
            console.error("Failed to extend trial:", err)
            addToast({
                type: "error",
                title: "Failed to extend trial",
                description: "An error occurred while extending the trial.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-blue-500" />
                        Extend Trial Period
                    </DialogTitle>
                    <DialogDescription>
                        Extend the trial period for {user.name}. This will add days to their current trial.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="days">Days to Add</Label>
                        <Input
                            id="days"
                            type="number"
                            value={days}
                            onChange={(e) => setDays(parseInt(e.target.value) || 0)}
                            min={1}
                            max={365}
                            placeholder="7"
                        />
                        <p className="text-xs text-muted-foreground">
                            Enter the number of days to add (1-365)
                        </p>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="reason">Reason (Optional)</Label>
                        <Textarea
                            id="reason"
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            placeholder="Enter reason for trial extension..."
                            rows={3}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleExtend} disabled={isLoading || days < 1}>
                        {isLoading ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Extending...
                            </>
                        ) : (
                            <>Extend Trial</>
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
