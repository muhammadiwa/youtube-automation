"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { accountsApi } from "@/lib/api"
import { YouTubeAccount } from "@/types"
import { CheckCircle, XCircle, Youtube } from "lucide-react"

export default function OAuthCallbackPage() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
    const [account, setAccount] = useState<YouTubeAccount | null>(null)
    const [error, setError] = useState<string>("")

    useEffect(() => {
        handleCallback()
    }, [])

    const handleCallback = async () => {
        const code = searchParams.get("code")
        const state = searchParams.get("state")
        const errorParam = searchParams.get("error")

        if (errorParam) {
            setStatus("error")
            setError(errorParam === "access_denied" ? "Access was denied" : "An error occurred during authentication")
            return
        }

        if (!code || !state) {
            setStatus("error")
            setError("Missing required parameters")
            return
        }

        try {
            const accountData = await accountsApi.handleOAuthCallback(code, state)
            setAccount(accountData)
            setStatus("success")

            // Redirect to account detail page after 2 seconds
            setTimeout(() => {
                router.push(`/dashboard/accounts/${accountData.id}`)
            }, 2000)
        } catch (err: any) {
            setStatus("error")
            setError(err.message || "Failed to connect account")
        }
    }

    const handleRetry = () => {
        router.push("/dashboard/accounts")
    }

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
                        {status === "loading" && (
                            <div className="text-center space-y-4">
                                <div className="flex justify-center">
                                    <Spinner className="h-12 w-12" />
                                </div>
                                <h2 className="text-2xl font-bold">Connecting Account</h2>
                                <p className="text-muted-foreground">
                                    Please wait while we connect your YouTube account...
                                </p>
                            </div>
                        )}

                        {status === "success" && account && (
                            <div className="text-center space-y-4">
                                <div className="flex justify-center">
                                    <div className="rounded-full bg-green-500/10 p-3">
                                        <CheckCircle className="h-12 w-12 text-green-500" />
                                    </div>
                                </div>
                                <h2 className="text-2xl font-bold">Account Connected!</h2>
                                <div className="space-y-2">
                                    <p className="text-muted-foreground">
                                        Successfully connected:
                                    </p>
                                    <div className="flex items-center justify-center gap-2 p-3 bg-muted rounded-md">
                                        <Youtube className="h-5 w-5 text-red-500" />
                                        <span className="font-semibold">{account.channelTitle}</span>
                                    </div>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    Redirecting to account details...
                                </p>
                            </div>
                        )}

                        {status === "error" && (
                            <div className="text-center space-y-4">
                                <div className="flex justify-center">
                                    <div className="rounded-full bg-red-500/10 p-3">
                                        <XCircle className="h-12 w-12 text-red-500" />
                                    </div>
                                </div>
                                <h2 className="text-2xl font-bold">Connection Failed</h2>
                                <p className="text-muted-foreground">{error}</p>
                                <div className="flex gap-2 justify-center">
                                    <Button variant="outline" onClick={() => router.push("/dashboard/accounts")}>
                                        Back to Accounts
                                    </Button>
                                    <Button onClick={handleRetry}>
                                        Try Again
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    )
}
