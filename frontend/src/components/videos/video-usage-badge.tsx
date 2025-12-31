/**
 * Video Usage Badge Component
 * 
 * Shows how a video is being used:
 * - 📺 VOD only (uploaded to YouTube)
 * - 🔴 Live only (used for streaming)
 * - 📺🔴 Both (uploaded AND streaming)
 * - 📍 Library only (not used yet)
 * 
 * Requirements: 4.2 (Usage Tracking)
 */

import { Badge } from "@/components/ui/badge"
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import type { Video } from "@/types"

interface VideoUsageBadgeProps {
    video: Video
    showLabel?: boolean
}

export function VideoUsageBadge({ video, showLabel = false }: VideoUsageBadgeProps) {
    const hasYouTubeUpload = !!video.youtubeId
    const hasStreaming = video.isUsedForStreaming || false
    const streamingCount = video.streamingCount || 0

    // Determine badge type
    let badgeType: "vod" | "live" | "both" | "library"
    let icon: string
    let label: string
    let description: string
    let variant: "default" | "secondary" | "destructive" | "outline" = "outline"

    if (hasYouTubeUpload && hasStreaming) {
        badgeType = "both"
        icon = "📺🔴"
        label = "VOD + Live"
        description = `Uploaded to YouTube and used for streaming (${streamingCount} session${streamingCount !== 1 ? 's' : ''})`
        variant = "default"
    } else if (hasYouTubeUpload) {
        badgeType = "vod"
        icon = "📺"
        label = "VOD"
        description = "Uploaded to YouTube as Video-on-Demand"
        variant = "outline"
    } else if (hasStreaming) {
        badgeType = "live"
        icon = "🔴"
        label = "Live"
        description = `Used for live streaming (${streamingCount} session${streamingCount !== 1 ? 's' : ''})`
        variant = "secondary"
    } else {
        badgeType = "library"
        icon = "📍"
        label = "Library"
        description = "In library only, not used yet"
        variant = "outline"
    }

    const badgeContent = (
        <Badge variant={variant} className="gap-1">
            <span>{icon}</span>
            {showLabel && <span className="text-xs">{label}</span>}
        </Badge>
    )

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    {badgeContent}
                </TooltipTrigger>
                <TooltipContent>
                    <div className="space-y-1">
                        <p className="font-semibold">{label}</p>
                        <p className="text-xs text-muted-foreground">{description}</p>
                        {hasYouTubeUpload && video.youtubeId && (
                            <p className="text-xs">
                                <span className="text-muted-foreground">YouTube ID:</span>{" "}
                                <span className="font-mono">{video.youtubeId}</span>
                            </p>
                        )}
                        {hasStreaming && streamingCount > 0 && (
                            <p className="text-xs">
                                <span className="text-muted-foreground">Streaming sessions:</span>{" "}
                                <span className="font-semibold">{streamingCount}</span>
                            </p>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}

/**
 * Compact version for use in lists
 */
export function VideoUsageBadgeCompact({ video }: { video: Video }) {
    return <VideoUsageBadge video={video} showLabel={false} />
}

/**
 * Full version with label for use in detail pages
 */
export function VideoUsageBadgeFull({ video }: { video: Video }) {
    return <VideoUsageBadge video={video} showLabel={true} />
}
