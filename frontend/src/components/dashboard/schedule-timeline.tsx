"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Calendar, Clock, Play, Edit, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatCountdown, formatTime, formatSmartDate, isWithinHours } from "@/lib/utils/datetime"
import type { ScheduledStreamInfo } from "@/lib/api/monitoring"
import Link from "next/link"

interface ScheduleTimelineProps {
    streams: ScheduledStreamInfo[]
    maxItems?: number
}

function isStartingSoon(seconds: number): boolean {
    return seconds <= 3600 // Within 1 hour
}

export function ScheduleTimeline({ streams, maxItems = 5 }: ScheduleTimelineProps) {
    const displayStreams = streams.slice(0, maxItems)

    if (displayStreams.length === 0) {
        return (
            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-blue-500" />
                        Upcoming Streams
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                        <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p>No scheduled streams</p>
                        <Link href="/dashboard/streams/create">
                            <Button variant="outline" size="sm" className="mt-3">
                                Schedule a Stream
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-blue-500" />
                        Upcoming Streams
                    </CardTitle>
                    <Badge variant="secondary" className="text-xs">
                        {streams.length} scheduled
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <div className="divide-y">
                    {displayStreams.map((stream, index) => (
                        <div
                            key={stream.stream_id}
                            className={cn(
                                "p-4 hover:bg-muted/50 transition-colors",
                                isStartingSoon(stream.starts_in_seconds) && "bg-blue-50/50 dark:bg-blue-950/20"
                            )}
                        >
                            <div className="flex items-start gap-3">
                                {/* Timeline indicator */}
                                <div className="flex flex-col items-center">
                                    <div className={cn(
                                        "w-3 h-3 rounded-full border-2",
                                        isStartingSoon(stream.starts_in_seconds)
                                            ? "bg-blue-500 border-blue-500"
                                            : "bg-background border-muted-foreground/30"
                                    )} />
                                    {index < displayStreams.length - 1 && (
                                        <div className="w-0.5 h-full bg-muted-foreground/20 mt-1" />
                                    )}
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Avatar className="h-5 w-5">
                                                    <AvatarImage src={stream.channel_thumbnail || ""} />
                                                    <AvatarFallback className="text-[8px]">
                                                        {stream.channel_title.substring(0, 2).toUpperCase()}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <span className="text-xs text-muted-foreground truncate">
                                                    {stream.channel_title}
                                                </span>
                                            </div>
                                            <h4 className="font-medium text-sm truncate">
                                                {stream.title}
                                            </h4>
                                        </div>

                                        {/* Countdown badge */}
                                        <Badge
                                            variant={isStartingSoon(stream.starts_in_seconds) ? "default" : "secondary"}
                                            className={cn(
                                                "text-xs whitespace-nowrap",
                                                isStartingSoon(stream.starts_in_seconds) && "bg-blue-500"
                                            )}
                                        >
                                            {formatCountdown(stream.starts_in_seconds)}
                                        </Badge>
                                    </div>

                                    {/* Time info */}
                                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                                        <span className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {formatSmartDate(stream.scheduled_start_at)}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Clock className="h-3 w-3" />
                                            {formatTime(stream.scheduled_start_at)}
                                        </span>
                                    </div>

                                    {/* Actions for starting soon */}
                                    {isStartingSoon(stream.starts_in_seconds) && (
                                        <div className="flex gap-2 mt-2">
                                            <Link href={`/dashboard/streams/${stream.stream_id}`}>
                                                <Button variant="default" size="sm" className="h-7 text-xs bg-blue-500 hover:bg-blue-600">
                                                    <Play className="h-3 w-3 mr-1" />
                                                    Go Live
                                                </Button>
                                            </Link>
                                            <Link href={`/dashboard/streams/${stream.stream_id}/edit`}>
                                                <Button variant="outline" size="sm" className="h-7 text-xs">
                                                    <Edit className="h-3 w-3 mr-1" />
                                                    Edit
                                                </Button>
                                            </Link>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* View all link */}
                {streams.length > maxItems && (
                    <div className="p-3 border-t">
                        <Link href="/dashboard/streams?status=scheduled">
                            <Button variant="ghost" size="sm" className="w-full text-xs">
                                View all {streams.length} scheduled streams
                            </Button>
                        </Link>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

export default ScheduleTimeline
