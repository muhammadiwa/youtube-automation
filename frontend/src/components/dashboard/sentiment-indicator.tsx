"use client"

import { ThumbsUp, ThumbsDown, Minus, AlertCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export type Sentiment = "positive" | "neutral" | "negative"

interface SentimentIndicatorProps {
    sentiment: Sentiment
    showLabel?: boolean
    size?: "sm" | "md" | "lg"
    className?: string
}

const sentimentConfig = {
    positive: {
        icon: ThumbsUp,
        label: "Positive",
        badgeClassName: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800",
        iconClassName: "text-green-600 dark:text-green-400",
        dotClassName: "bg-green-500",
    },
    neutral: {
        icon: Minus,
        label: "Neutral",
        badgeClassName: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400 border-gray-200 dark:border-gray-700",
        iconClassName: "text-gray-500 dark:text-gray-400",
        dotClassName: "bg-gray-400",
    },
    negative: {
        icon: ThumbsDown,
        label: "Negative",
        badgeClassName: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800",
        iconClassName: "text-red-600 dark:text-red-400",
        dotClassName: "bg-red-500",
    },
}

const sizeConfig = {
    sm: {
        iconSize: "h-3 w-3",
        textSize: "text-xs",
        dotSize: "h-2 w-2",
    },
    md: {
        iconSize: "h-4 w-4",
        textSize: "text-sm",
        dotSize: "h-2.5 w-2.5",
    },
    lg: {
        iconSize: "h-5 w-5",
        textSize: "text-base",
        dotSize: "h-3 w-3",
    },
}

/**
 * SentimentBadge - A badge-style sentiment indicator with icon and label
 */
export function SentimentBadge({
    sentiment,
    showLabel = true,
    size = "md",
    className,
}: SentimentIndicatorProps) {
    const config = sentimentConfig[sentiment]
    const sizes = sizeConfig[size]
    const Icon = config.icon

    return (
        <Badge
            variant="outline"
            className={cn(config.badgeClassName, className)}
        >
            <Icon className={cn(sizes.iconSize, showLabel && "mr-1")} />
            {showLabel && <span className={sizes.textSize}>{config.label}</span>}
        </Badge>
    )
}

/**
 * SentimentIcon - Just the icon with appropriate color
 */
export function SentimentIcon({
    sentiment,
    size = "md",
    className,
}: Omit<SentimentIndicatorProps, "showLabel">) {
    const config = sentimentConfig[sentiment]
    const sizes = sizeConfig[size]
    const Icon = config.icon

    return <Icon className={cn(sizes.iconSize, config.iconClassName, className)} />
}

/**
 * SentimentDot - A simple colored dot indicator
 */
export function SentimentDot({
    sentiment,
    size = "md",
    className,
}: Omit<SentimentIndicatorProps, "showLabel">) {
    const config = sentimentConfig[sentiment]
    const sizes = sizeConfig[size]

    return (
        <span
            className={cn(
                "rounded-full inline-block",
                sizes.dotSize,
                config.dotClassName,
                className
            )}
        />
    )
}

/**
 * AttentionIndicator - Shows when a comment needs attention (negative sentiment)
 */
interface AttentionIndicatorProps {
    sentiment: Sentiment
    className?: string
}

export function AttentionIndicator({ sentiment, className }: AttentionIndicatorProps) {
    if (sentiment !== "negative") return null

    return (
        <div
            className={cn(
                "flex items-center gap-1 text-red-600 dark:text-red-400",
                className
            )}
        >
            <AlertCircle className="h-4 w-4" />
            <span className="text-xs font-medium">Needs Attention</span>
        </div>
    )
}

/**
 * SentimentSummary - Shows a summary of sentiment distribution
 */
interface SentimentSummaryProps {
    positive: number
    neutral: number
    negative: number
    className?: string
}

export function SentimentSummary({
    positive,
    neutral,
    negative,
    className,
}: SentimentSummaryProps) {
    const total = positive + neutral + negative
    if (total === 0) return null

    const positivePercent = Math.round((positive / total) * 100)
    const neutralPercent = Math.round((neutral / total) * 100)
    const negativePercent = Math.round((negative / total) * 100)

    return (
        <div className={cn("space-y-2", className)}>
            <div className="flex h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                {positivePercent > 0 && (
                    <div
                        className="bg-green-500"
                        style={{ width: `${positivePercent}%` }}
                    />
                )}
                {neutralPercent > 0 && (
                    <div
                        className="bg-gray-400"
                        style={{ width: `${neutralPercent}%` }}
                    />
                )}
                {negativePercent > 0 && (
                    <div
                        className="bg-red-500"
                        style={{ width: `${negativePercent}%` }}
                    />
                )}
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                    <SentimentDot sentiment="positive" size="sm" />
                    {positive} ({positivePercent}%)
                </span>
                <span className="flex items-center gap-1">
                    <SentimentDot sentiment="neutral" size="sm" />
                    {neutral} ({neutralPercent}%)
                </span>
                <span className="flex items-center gap-1">
                    <SentimentDot sentiment="negative" size="sm" />
                    {negative} ({negativePercent}%)
                </span>
            </div>
        </div>
    )
}

export default SentimentBadge
