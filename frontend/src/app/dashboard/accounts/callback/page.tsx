"use client"

import { useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { XCircle } from "lucide-react"

/**
 * OAuth Callback Page
 * 
 * This page handles the OAuth callback from Google/YouTube.
 * Note: The actual OAuth callback is handled by the backend at /api/v1/accounts/oauth/callback
 * which then redirects to the frontend with success/error status.
 * 
 * This page is kept as a fallback in case the frontend callback URL is used directly,
 * or for handling errors that occur during the OAuth flow.
 */
export default function OAuthCallbackPage() {
    const router = useRouter()
    const searchParams = useSearchParams()

    useEffect(() => {
        // Check for error from OAuth flow
        const errorParam = searchParams.get("error")
        const code = searchParams.get("code")
        const state = searchParams.get("state")

        if (errorParam) {
            // Error occurred, stay on this page to show error
            return
        }

        // If we have code and state, the backend should have handled this
        // This means the redirect URI might be misconfigured
        if (code && state) {
            // Redirect to accounts page with error
            router.push("/dashboard/accounts?error=OAuth%20callback%20misconfigured.%20Please%20contact%20support.")
            return
        }

        // No parameters, redirect to accounts page
        router.push("/dashboard/accounts")
    }, [searchParams, router])

    const errorParam = searchParams.get("error")
    const errorMessage = errorParam === "access_denied"
        ? "Access was denied. You need to grant permission to connect your YouTube account."
        : errorParam || "An error occurred during authentication"

    // Only show error UI if there's an error
    if (!errorParam) {
        return (
            <DashboardLayout
                breadcrumbs={[
                    { label: "Dashboard", href: "/dashboard" },
                    { label: "Accounts", href: "/dashboard/accounts" },
                    { label: "Connecting..." },
                ]}
            >
                <div className="flex items-center justify-center min-h-[60vh]">
                    <Card className="w-full max-w-md">
                        <CardContent className="p-8">
                            <div className="text-center space-y-4">
                                <div className="flex justify-center">
                                    <Spinner className="h-12 w-12" />
                                </div>
                                <h2 className="text-2xl font-bold">Processing...</h2>
                                <p className="text-muted-foreground">
                                    Please wait while we process your request...
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </DashboardLayout>
        )
    }

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Accounts", href: "/dashboard/accounts" },
                { label: "Connection Failed" },
            ]}
        >
            <div className="flex items-center justify-center min-h-[60vh]">
                <Card className="w-full max-w-md">
                    <CardContent className="p-8">
                        <div className="text-center space-y-4">
                            <div className="flex justify-center">
                                <div className="rounded-full bg-red-500/10 p-3">
                                    <XCircle className="h-12 w-12 text-red-500" />
                                </div>
                            </div>
                            <h2 className="text-2xl font-bold">Connection Failed</h2>
                            <p className="text-muted-foreground">{errorMessage}</p>
                            <div className="flex gap-2 justify-center">
                                <Button variant="outline" onClick={() => router.push("/dashboard/accounts")}>
                                    Back to Accounts
                                </Button>
                                <Button onClick={() => router.push("/dashboard/accounts")}>
                                    Try Again
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
