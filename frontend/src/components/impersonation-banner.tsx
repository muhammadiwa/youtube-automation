"use client"

import { useState, useEffect } from "react"
import { UserCog, X, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ImpersonationSession {
    sessionId: string
    userId: string
    userName: string
    userEmail: string
    expiresAt: string
}

export function ImpersonationBanner() {
    const [session, setSession] = useState<ImpersonationSession | null>(null)

    useEffect(() => {
        const stored = localStorage.getItem("impersonation_session")
        if (stored) {
            try {
                const parsed = JSON.parse(stored) as ImpersonationSession
                // Check if session is expired
                if (new Date(parsed.expiresAt) > new Date()) {
                    setSession(parsed)
                } else {
                    // Clean up expired session
                    localStorage.removeItem("impersonation_session")
                    localStorage.removeItem("impersonation_token")
                }
            } catch {
                localStorage.removeItem("impersonation_session")
                localStorage.removeItem("impersonation_token")
            }
        }
    }, [])

    const handleExitImpersonation = () => {
        localStorage.removeItem("impersonation_session")
        localStorage.removeItem("impersonation_token")
        setSession(null)
        // Close this tab and return to admin
        window.close()
    }

    const handleReturnToAdmin = () => {
        window.open("/admin/users", "_blank")
    }

    if (!session) return null

    return (
        <div className="fixed top-0 left-0 right-0 z-50 bg-purple-600 text-white px-4 py-2">
            <div className="container mx-auto flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <UserCog className="h-5 w-5" />
                    <span className="font-medium">
                        Impersonating: {session.userName} ({session.userEmail})
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-purple-700"
                        onClick={handleReturnToAdmin}
                    >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Return to Admin
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-purple-700"
                        onClick={handleExitImpersonation}
                    >
                        <X className="h-4 w-4 mr-2" />
                        Exit Impersonation
                    </Button>
                </div>
            </div>
        </div>
    )
}
