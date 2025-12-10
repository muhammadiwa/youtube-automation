"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

// Redirect to main billing page with usage tab
export default function UsagePage() {
    const router = useRouter()

    useEffect(() => {
        router.replace("/dashboard/billing?tab=usage")
    }, [router])

    return null
}
