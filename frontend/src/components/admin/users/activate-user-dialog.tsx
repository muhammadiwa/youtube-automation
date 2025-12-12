"use client"

import { useState } from "react"
import { Loader2, UserCheck, Info } from "lucide-react"
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

interface ActivateUserDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    user: UserDetail
    onSuccess: () => void
}

export function ActivateUserDialog({
    open,
    onOpenChange,
    user,
    onSuccess,
}: ActivateUserDialogProps) {
    const { addToast } = useToast()
    const [isLoading, setIsLoading] = useState(false)

    const handleActivate = async () => {
        setIsLoading(true)
        try {
            const result = await adminApi.activateUser(user.id)
            addToast({
                type: "success",
                title: "User activated",
                description: `${user.name} has been activated. ${result.jobs_resumed} jobs resumed.`,
            })
            onOpenChange(false)
            onSuccess()
        } catch (error) {
            console.error("Failed to activate user:", error)
            addToast({
                type: "error",
                title: "Failed to activate user",
                description: "An error occurred while activating the user. Please try again.",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-green-600">
                        <UserCheck className="h-5 w-5" />
                        Activate User
                    </DialogTitle>
                    <DialogDescription>
                        Activating this user will restore their access and resume paused jobs.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                        <Info className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div className="text-sm">
                            <p className="font-medium text-blue-700">Confirmation</p>
                            <p className="text-blue-600">
                                You are about to activate <strong>{user.name}</strong> ({user.email}).
                                All previously paused jobs will be resumed.
                            </p>
                        </div>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button onClick={handleActivate} disabled={isLoading} className="bg-green-600 hover:bg-green-700">
                        {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                        Activate User
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
