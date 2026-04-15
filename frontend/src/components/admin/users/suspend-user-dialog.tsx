"use client"

import { useState } from "react"
import { Loader2, UserX, AlertTriangle } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/toast"
import adminApi from "@/lib/api/admin"
import type { UserDetail } from "@/types/admin"

interface SuspendUserDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    user: UserDetail
    onSuccess: () => void
}

export function SuspendUserDialog({
    open,
    onOpenChange,
    user,
    onSuccess,
}: SuspendUserDialogProps) {
    const { addToast } = useToast()
    const [reason, setReason] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    const handleSuspend = async () => {
        if (!reason.trim()) {
            addToast({
                type: "error",
                title: "Reason required",
                description: "Please provide a reason for suspending this user.",
            })
            return
        }

        setIsLoading(true)
        try {
            const result = await adminApi.suspendUser(user.id, { reason: reason.trim() })
            addToast({
                type: "success",
                title: "User suspended",
                description: `${user.name} has been suspended. ${result.jobs_paused} jobs paused.`,
            })
            setReason("")
            onOpenChange(false)
            onSuccess()
        } catch (error) {
            console.error("Failed to suspend user:", error)
            addToast({
                type: "error",
                title: "Failed to suspend user",
                description: "An error occurred while suspending the user. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-red-600">
                        <UserX className="h-5 w-5" />
                        Suspend User
                    </DialogTitle>
                    <DialogDescription>
                        Suspending this user will pause all their scheduled jobs and restrict access.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        <div className="text-sm">
                            <p className="font-medium text-yellow-700">Warning</p>
                            <p className="text-yellow-600">
                                You are about to suspend <strong>{user.name}</strong> ({user.email}).
                                This action will be logged.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="reason">Suspension Reason *</Label>
                        <Textarea
                            id="reason"
                            placeholder="Enter the reason for suspension..."
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={4}
                        />
                        <p className="text-xs text-muted-foreground">
                            This reason will be recorded in the audit log and may be shared with the user.
                        </p>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button variant="destructive" onClick={handleSuspend} disabled={isLoading}>
                        {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                        Suspend User
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
