"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
    AlertTriangle,
    AlertCircle,
    Info,
    Bell,
    Key,
    Gauge,
    Radio,
    ShieldAlert,
    XCircle,
    CheckCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { formatTimeAgo } from "@/lib/utils/datetime"
import type { Alert, AlertSeverity, AlertType } from "@/lib/api/monitoring"

interface AlertCenterProps {
    alerts: Alert[]
    maxItems?: number
}

const severityConfig: Record<AlertSeverity, { icon: typeof AlertTriangle; color: string; bgColor: string }> = {
    critical: {
        icon: XCircle,
        color: "text-red-600 dark:text-red-400",
        bgColor: "bg-red-50 dark:bg-red-950/30",
    },
    warning: {
        icon: AlertTriangle,
        color: "text-yellow-600 dark:text-yellow-400",
        bgColor: "bg-yellow-50 dark:bg-yellow-950/30",
    },
    info: {
        icon: Info,
        color: "text-blue-600 dark:text-blue-400",
        bgColor: "bg-blue-50 dark:bg-blue-950/30",
    },
}

const typeConfig: Record<AlertType, { icon: typeof Key; label: string }> = {
    token_expired: { icon: Key, label: "Token Expired" },
    token_expiring: { icon: Key, label: "Token Expiring" },
    quota_high: { icon: Gauge, label: "High Quota" },
    quota_critical: { icon: Gauge, label: "Critical Quota" },
    stream_dropped: { icon: Radio, label: "Stream Dropped" },
    strike_detected: { icon: ShieldAlert, label: "Strike" },
    account_error: { icon: AlertCircle, label: "Account Error" },
    viewer_drop: { icon: AlertTriangle, label: "Viewer Drop" },
    peak_viewers: { icon: CheckCircle, label: "Peak Viewers" },
}

export function AlertCenter({ alerts, maxItems = 10 }: AlertCenterProps) {
    const displayAlerts = alerts.slice(0, maxItems)
    const criticalCount = alerts.filter(a => a.severity === "critical").length
    const warningCount = alerts.filter(a => a.severity === "warning").length

    if (alerts.length === 0) {
        return (
            <Card>
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Bell className="h-5 w-5 text-muted-foreground" />
                        Alerts
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-center py-8 text-muted-foreground">
                        <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500 opacity-50" />
                        <p className="font-medium text-green-600 dark:text-green-400">All Clear</p>
                        <p className="text-sm mt-1">No active alerts</p>
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
                        <Bell className="h-5 w-5 text-orange-500" />
                        Alerts
                    </CardTitle>
                    <div className="flex gap-1.5">
                        {criticalCount > 0 && (
                            <Badge variant="destructive" className="text-xs">
                                {criticalCount} critical
                            </Badge>
                        )}
                        {warningCount > 0 && (
                            <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300">
                                {warningCount} warning
                            </Badge>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                <ScrollArea className="h-[300px]">
                    <div className="divide-y">
                        {displayAlerts.map((alert) => {
                            const severity = severityConfig[alert.severity]
                            const type = typeConfig[alert.type]
                            const SeverityIcon = severity.icon
                            const TypeIcon = type?.icon || AlertCircle

                            return (
                                <div
                                    key={alert.id}
                                    className={cn(
                                        "p-3 hover:bg-muted/50 transition-colors",
                                        severity.bgColor
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={cn("mt-0.5", severity.color)}>
                                            <SeverityIcon className="h-4 w-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-0.5">
                                                <span className="font-medium text-sm truncate">
                                                    {alert.channel_title}
                                                </span>
                                                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                                                    <TypeIcon className="h-2.5 w-2.5 mr-1" />
                                                    {type?.label || alert.type}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-foreground">
                                                {alert.message}
                                            </p>
                                            {alert.details && (
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {alert.details}
                                                </p>
                                            )}
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {formatTimeAgo(alert.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </ScrollArea>

                {alerts.length > maxItems && (
                    <div className="p-3 border-t">
                        <Button variant="ghost" size="sm" className="w-full text-xs">
                            View all {alerts.length} alerts
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

export default AlertCenter
