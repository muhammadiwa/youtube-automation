"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Settings, Loader2 } from "lucide-react"

export default function ConfigPage() {
    const router = useRouter()

    useEffect(() => {
        // Redirect to auth config by default
        router.replace("/admin/config/auth")
    }, [router])

    return (
        <div className="flex items-center justify-center h-full">
            <div className="text-center">
                <Settings className="h-12 w-12 text-slate-400 mx-auto mb-4 animate-pulse" />
                <div className="flex items-center gap-2 text-slate-500">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Loading configuration...</span>
                </div>
            </div>
        </div>
    )
}
