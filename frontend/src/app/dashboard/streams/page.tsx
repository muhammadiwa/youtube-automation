"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
    Search,
    Plus,
    Play,
    Video,
    BarChart3,
    History,
} from "lucide-react"
import { DashboardLayout, PausedStreamsIndicator } from "@/components/dashboard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { accountsApi } from "@/lib/api/accounts"
import { VideoToLiveList, ResourceDashboardCard } from "@/components/streams"
import type { YouTubeAccount } from "@/types"

export default function StreamsPage() {
    const router = useRouter()
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([])
    const [searchQuery, setSearchQuery] = useState("")
    const [accountFilter, setAccountFilter] = useState<string>("all")

    useEffect(() => {
        loadAccounts()
    }, [])

    const loadAccounts = async () => {
        try {
            const data = await accountsApi.getAccounts()
            setAccounts(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Failed to load accounts:", error)
            setAccounts([])
        }
    }

    return (
        <DashboardLayout
            breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Streams" }]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Video-to-Live Streams</h1>
                        <p className="text-muted-foreground">
                            Stream your videos to YouTube 24/7 automatically
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            onClick={() => router.push("/dashboard/streams/history")}
                        >
                            <History className="mr-2 h-4 w-4" />
                            History
                        </Button>
                        <Button
                            variant="outline"
                            onClick={() => router.push("/dashboard/streams/analytics")}
                        >
                            <BarChart3 className="mr-2 h-4 w-4" />
                            Analytics
                        </Button>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
                                >
                                    <Plus className="mr-2 h-4 w-4" />
                                    New Stream
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => router.push("/dashboard/streams/create-video-live")}>
                                    <Video className="mr-2 h-4 w-4" />
                                    Video-to-Live (24/7)
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => router.push("/dashboard/streams/create-playlist")}>
                                    <Play className="mr-2 h-4 w-4" />
                                    Playlist Stream
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                {/* Paused Streams Warning */}
                <PausedStreamsIndicator />

                {/* Filters */}
                <Card className="border-0 shadow-lg">
                    <CardContent className="pt-6">
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                            <div className="flex flex-1 gap-2">
                                <div className="relative flex-1 max-w-md">
                                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        placeholder="Search streams..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="pl-9"
                                    />
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2">
                                <Select
                                    value={accountFilter}
                                    onValueChange={setAccountFilter}
                                >
                                    <SelectTrigger className="w-[180px]">
                                        <SelectValue placeholder="All Accounts" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Accounts</SelectItem>
                                        {accounts.map((account) => (
                                            <SelectItem key={account.id} value={account.id}>
                                                {account.channelTitle}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Resource Dashboard */}
                <ResourceDashboardCard />

                {/* Video-to-Live List */}
                <VideoToLiveList
                    accountId={accountFilter !== "all" ? accountFilter : undefined}
                    showResourceDashboard={false}
                />
            </div>
        </DashboardLayout>
    )
}
