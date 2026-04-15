"use client"

import { useState } from "react"
import { Loader2, UserCog, AlertTriangle, ExternalLink } from "lucide-react"
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

interface ImpersonateUserDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    user: UserDetail
}

export function ImpersonateUserDialog({
    open,
    onOpenChange,
    user,
}: ImpersonateUserDialogProps) {
    const { addToast } = useToast()
    const [reason, setReason] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    const handleImpersonate = async () => {
        setIsLoading(true)
        try {
            const result = await adminApi.impersonateUser(user.id, {
                reason: reason.trim() || undefined,
            })

            // Store impersonation session info
            localStorage.setItem("impersonation_session", JSON.stringify({
                sessionId: result.session.session_id,
                userId: result.session.user_id,
                userName: user.name,
                userEmail: user.email,
                expiresAt: result.session.expires_at,
            }))

            // Store the impersonation access token
            localStorage.setItem("impersonation_token", result.session.access_token)

            addToast({
                type: "success",
                title: "Impersonation started",
                description: `You are now viewing the platform as ${user.name}.`,
            })

            // Open user dashboard in new tab
            window.open("/dashboard", "_blank")

            setReason("")
            onOpenChange(false)
        } catch (error) {
            console.error("Failed to impersonate user:", error)
            addToast({
                type: "error",
                title: "Failed to impersonate",
                description: "An error occurred while starting impersonation. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <UserCog className="h-5 w-5 text-purple-500" />
                        Impersonate User
                    </DialogTitle>
                    <DialogDescription>
                        View the platform as this user to troubleshoot issues or verify settings.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                        <div className="text-sm">
                            <p className="font-medium text-yellow-700">Important</p>
                            <p className="text-yellow-600">
                                All actions during impersonation will be logged for audit purposes.
                                You will be viewing the platform as <strong>{user.name}</strong>.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="impersonate-reason">Reason (optional)</Label>
                        <Textarea
                            id="impersonate-reason"
                            placeholder="Enter the reason for impersonation..."
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            rows={3}
                        />
                        <p className="text-xs text-muted-foreground">
                            Providing a reason helps with audit trail documentation.
                        </p>
                    </div>

                    <div className="p-3 rounded-lg bg-muted/50 text-sm">
                        <p className="font-medium mb-1">What happens next:</p>
                        <ul className="list-disc list-inside text-muted-foreground space-y-1">
                            <li>A new tab will open with the user&apos;s dashboard</li>
                            <li>An impersonation banner will be visible</li>
                            <li>Click &quot;Exit Impersonation&quot; to return to admin</li>
                        </ul>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleImpersonate} disabled={isLoading} className="bg-purple-600 hover:bg-purple-700">
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                            <ExternalLink className="h-4 w-4 mr-2" />
                        )}
                        Start Impersonation
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
