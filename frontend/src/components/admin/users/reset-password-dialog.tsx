"use client"

import { useState } from "react"
import { Loader2, KeyRound, Mail, CheckCircle } from "lucide-react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/toast"
import adminApi from "@/lib/api/admin"
import type { UserDetail } from "@/types/admin"

interface ResetPasswordDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    user: UserDetail
    onSuccess: () => void
}

export function ResetPasswordDialog({
    open,
    onOpenChange,
    user,
    onSuccess,
}: ResetPasswordDialogProps) {
    const { addToast } = useToast()
    const [isLoading, setIsLoading] = useState(false)
    const [isSuccess, setIsSuccess] = useState(false)

    const handleResetPassword = async () => {
        setIsLoading(true)
        try {
            const result = await adminApi.resetUserPassword(user.id)
            if (result.reset_link_sent) {
                setIsSuccess(true)
                addToast({
                    type: "success",
                    title: "Password reset email sent",
                    description: `A password reset link has been sent to ${user.email}.`,
                })
                onSuccess()
            } else {
                addToast({
                    type: "error",
                    title: "Failed to send reset email",
                    description: "The password reset email could not be sent. Please try again.",
                })
            }
        } catch (error) {
            console.error("Failed to reset password:", error)
            addToast({
                type: "error",
                title: "Failed to reset password",
                description: "An error occurred while resetting the password. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleClose = () => {
        setIsSuccess(false)
        onOpenChange(false)
    }

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <KeyRound className="h-5 w-5 text-blue-500" />
                        Reset Password
                    </DialogTitle>
                    <DialogDescription>
                        Send a password reset link to the user&apos;s email address.
                    </DialogDescription>
                </DialogHeader>

                {isSuccess ? (
                    <div className="py-6">
                        <div className="flex flex-col items-center text-center gap-4">
                            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/10">
                                <CheckCircle className="h-8 w-8 text-green-600" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-lg">Email Sent!</h3>
                                <p className="text-muted-foreground mt-1">
                                    A password reset link has been sent to:
                                </p>
                                <p className="font-medium mt-2">{user.email}</p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4 py-4">
                        <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                            <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium">Password reset for:</p>
                                <p className="text-muted-foreground">{user.name}</p>
                                <p className="text-muted-foreground">{user.email}</p>
                            </div>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            This will send a secure password reset link to the user&apos;s email address.
                            The link will expire after 24 hours.
                        </p>
                    </div>
                )}

                <DialogFooter>
                    {isSuccess ? (
                        <Button onClick={handleClose}>Done</Button>
                    ) : (
                        <>
                            <Button variant="outline" onClick={handleClose} disabled={isLoading}>
                                Cancel
                            </Button>
                            <Button onClick={handleResetPassword} disabled={isLoading}>
                                {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                Send Reset Link
                            </Button>
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
