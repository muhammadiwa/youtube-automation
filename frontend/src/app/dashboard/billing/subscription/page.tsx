"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

// Redirect to main billing page with subscription tab
export default function SubscriptionPage() {
    const router = useRouter()

    useEffect(() => {
        router.replace("/dashboard/billing?tab=subscription")
    }, [router])

    return null
}
