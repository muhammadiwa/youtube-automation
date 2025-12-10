"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

// Redirect to main billing page with history tab
export default function HistoryPage() {
    const router = useRouter()

    useEffect(() => {
        router.replace("/dashboard/billing?tab=history")
    }, [router])

    return null
}
