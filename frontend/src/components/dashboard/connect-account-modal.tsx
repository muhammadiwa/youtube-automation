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
import { accountsApi } from "@/lib/api"
import { Youtube, Shield, CheckCircle } from "lucide-react"

interface ConnectAccountModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ConnectAccountModal({ open, onOpenChange }: ConnectAccountModalProps) {
    const [connecting, setConnecting] = useState(false)

    const handleConnect = async () => {
        try {
            setConnecting(true)
            const { url } = await accountsApi.initiateOAuth()
            window.location.href = url
        } catch (error) {
            console.error("Failed to initiate OAuth:", error)
            setConnecting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="rounded-full bg-red-500/10 p-2">
                            <Youtube className="h-6 w-6 text-red-500" />
                        </div>
                        <DialogTitle>Connect YouTube Account</DialogTitle>
                    </div>
                    <DialogDescription>
                        Connect your YouTube account to start managing your content, streams, and analytics.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-3">
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                            <div>
                                <p className="font-medium text-sm">Full Channel Access</p>
                                <p className="text-sm text-muted-foreground">
                                    Manage videos, streams, and channel settings
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                            <div>
                                <p className="font-medium text-sm">Analytics & Insights</p>
                                <p className="text-sm text-muted-foreground">
                                    Access detailed performance metrics and reports
                                </p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                            <div>
                                <p className="font-medium text-sm">Live Streaming</p>
                                <p className="text-sm text-muted-foreground">
                                    Create and manage live streams automatically
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-start gap-2 p-3 bg-muted rounded-md">
                        <Shield className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <p className="text-xs text-muted-foreground">
                            Your credentials are encrypted and stored securely. We never share your data with
                            third parties.
                        </p>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)} disabled={connecting}>
                        Cancel
                    </Button>
                    <Button onClick={handleConnect} disabled={connecting}>
                        {connecting ? "Connecting..." : "Connect with YouTube"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
