"use client"

import { useState } from "react"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { accountsApi } from "@/lib/api"
import { Youtube, Shield, CheckCircle, Loader2, ExternalLink } from "lucide-react"

interface ConnectAccountModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

const features = [
    {
        title: "Full Channel Access",
        description: "Manage videos, streams, and channel settings",
    },
    {
        title: "Analytics & Insights",
        description: "Access detailed performance metrics",
    },
    {
        title: "Live Streaming",
        description: "Create and manage live streams",
    },
]

export function ConnectAccountModal({ open, onOpenChange }: ConnectAccountModalProps) {
    const [connecting, setConnecting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleConnect = async () => {
        try {
            setConnecting(true)
            setError(null)
            const response = await accountsApi.initiateOAuth()
            if (response?.url) {
                window.location.href = response.url
            } else {
                throw new Error("Failed to get OAuth URL")
            }
        } catch (err: any) {
            console.error("Failed to initiate OAuth:", err)
            setError(err?.message || "Failed to connect. Please try again.")
            setConnecting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md p-0 overflow-hidden">
                {/* Header with gradient */}
                <div className="bg-gradient-to-br from-red-500 to-red-600 p-6 text-white">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
                            <Youtube className="h-7 w-7" />
                        </div>
                        <div>
                            <DialogTitle className="text-white text-xl">Connect YouTube</DialogTitle>
                            <DialogDescription className="text-white/80 text-sm">
                                Link your channel to get started
                            </DialogDescription>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-5">
                    {/* Features */}
                    <div className="space-y-3">
                        {features.map((feature, index) => (
                            <div
                                key={index}
                                className="flex items-start gap-3 p-3 rounded-xl bg-muted/50 transition-colors hover:bg-muted"
                            >
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-green-500/10">
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                </div>
                                <div>
                                    <p className="font-medium text-sm">{feature.title}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {feature.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Security note */}
                    <div className="flex items-start gap-3 p-3 rounded-xl border border-border/50 bg-background">
                        <Shield className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            Your credentials are encrypted and stored securely. We use OAuth 2.0
                            and never store your Google password.
                        </p>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                            <p className="text-sm text-red-500">{error}</p>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                        <Button
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={connecting}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleConnect}
                            disabled={connecting}
                            className="flex-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                        >
                            {connecting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Connecting...
                                </>
                            ) : (
                                <>
                                    Connect
                                    <ExternalLink className="ml-2 h-4 w-4" />
                                </>
                            )}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}
