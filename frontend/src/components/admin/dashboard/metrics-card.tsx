"use client"

import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import type { PeriodComparison } from "@/types/admin"

interface MetricsCardProps {
    title: string
    value: string | number
    icon: LucideIcon
    iconColor?: string
    comparison?: PeriodComparison | null
    isLoading?: boolean
    format?: "number" | "currency" | "percent"
}

function formatValue(value: string | number, format?: "number" | "currency" | "percent"): string {
    if (typeof value === "string") return value

    switch (format) {
        case "currency":
            return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(value)
        case "percent":
            return `${value.toFixed(1)}%`
        case "number":
        default:
            return new Intl.NumberFormat("en-US").format(value)
    }
}

function TrendIndicator({ comparison }: { comparison: PeriodComparison }) {
    const { trend, change_percent } = comparison

    const trendConfig = {
        up: { icon: TrendingUp, color: "text-green-500", bgColor: "bg-green-500/10" },
        down: { icon: TrendingDown, color: "text-red-500", bgColor: "bg-red-500/10" },
        stable: { icon: Minus, color: "text-gray-500", bgColor: "bg-gray-500/10" },
    }

    const config = trendConfig[trend]
    const Icon = config.icon

    return (
        <div className={cn("flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", config.bgColor, config.color)}>
            <Icon className="h-3 w-3" />
            <span>{Math.abs(change_percent).toFixed(1)}%</span>
        </div>
    )
}

export function MetricsCard({
    title,
    value,
    icon: Icon,
    iconColor = "text-blue-500",
    comparison,
    isLoading = false,
    format = "number",
}: MetricsCardProps) {
    if (isLoading) {
        return (
            <Card className="border-0 shadow-md">
                <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                        <div className="space-y-2">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-8 w-32" />
                        </div>
                        <Skeleton className="h-11 w-11 rounded-xl" />
                    </div>
                    <Skeleton className="h-5 w-20 mt-3" />
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className="border-0 shadow-md hover:shadow-lg transition-shadow">
            <CardContent className="p-5">
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{formatValue(value, format)}</p>
                    </div>
                    <div className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-muted", iconColor)}>
                        <Icon className="h-5 w-5" />
                    </div>
                </div>
                {comparison && (
                    <div className="mt-3 flex items-center gap-2">
                        <TrendIndicator comparison={comparison} />
                        <span className="text-xs text-muted-foreground">vs previous period</span>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
