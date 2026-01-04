"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Radio, Eye, MessageSquare, Clock, ExternalLink } from "lucide-react"
import { formatDuration } from "@/lib/utils/datetime"
import type { LiveStreamInfo } from "@/lib/api/monitoring"

interface LiveStreamCardProps {
    stream: LiveStreamInfo
}

function formatNumber(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
}

export function LiveStreamCard({ stream }: LiveStreamCardProps) {
    const handleViewOnYouTube = () => {
        if (stream.youtube_broadcast_id) {
            window.open(`https://youtube.com/watch?v=${stream.youtube_broadcast_id}`, "_blank")
        } else {
            window.open(`https://youtube.com/channel/${stream.channel_id}/live`, "_blank")
        }
    }

    return (
        <Card className="border-red-200 dark:border-red-900 bg-gradient-to-br from-red-50 to-white dark:from-red-950/30 dark:to-background">
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start gap-3 mb-3">
                    <Avatar className="h-10 w-10 ring-2 ring-red-500">
                        <AvatarImage src={stream.channel_thumbnail || ""} />
                        <AvatarFallback className="bg-red-100 text-red-600 text-xs">
                            {stream.channel_title.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-sm truncate">{stream.channel_title}</h3>
                            <Badge className="bg-red-500 text-white animate-pulse text-xs">
                                <Radio className="h-3 w-3 mr-1" />
                                LIVE
                            </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground truncate mt-0.5">
                            {stream.title}
                        </p>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="flex items-center gap-1.5 text-sm">
                        <Eye className="h-4 w-4 text-red-500" />
                        <span className="font-medium">{formatNumber(stream.viewer_count)}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <MessageSquare className="h-4 w-4" />
                        <span>{formatNumber(stream.chat_messages)}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span>{formatDuration(stream.duration_seconds)}</span>
                    </div>
                </div>

                {/* Peak viewers */}
                <div className="text-xs text-muted-foreground mb-3">
                    Peak: {formatNumber(stream.peak_viewers)} viewers
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 text-xs"
                        onClick={handleViewOnYouTube}
                    >
                        <ExternalLink className="h-3.5 w-3.5 mr-1" />
                        Watch on YouTube
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export default LiveStreamCard
