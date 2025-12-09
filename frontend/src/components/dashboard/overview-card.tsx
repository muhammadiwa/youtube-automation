"use client";

import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface OverviewCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    description?: string;
    gradient?: string;
}

export function OverviewCard({
    title,
    value,
    icon: Icon,
    trend,
    description,
    gradient = "from-red-500 to-red-600",
}: OverviewCardProps) {
    return (
        <Card className="group relative overflow-hidden bg-card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardContent className="p-6">
                <div className="flex items-start justify-between">
                    <div className="space-y-3">
                        <p className="text-sm font-medium text-muted-foreground">
                            {title}
                        </p>
                        <p className="text-3xl font-bold tracking-tight">{value}</p>
                        {trend && (
                            <div className="flex items-center gap-1.5">
                                <div className={cn(
                                    "flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full",
                                    trend.isPositive
                                        ? "bg-green-500/10 text-green-600"
                                        : "bg-red-500/10 text-red-600"
                                )}>
                                    {trend.isPositive ? (
                                        <TrendingUp className="h-3 w-3" />
                                    ) : (
                                        <TrendingDown className="h-3 w-3" />
                                    )}
                                    <span>
                                        {trend.isPositive ? "+" : ""}
                                        {trend.value}%
                                    </span>
                                </div>
                                <span className="text-xs text-muted-foreground">
                                    vs last month
                                </span>
                            </div>
                        )}
                        {description && (
                            <p className="text-xs text-muted-foreground">{description}</p>
                        )}
                    </div>
                    <div className={cn(
                        "flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg transition-transform duration-300 group-hover:scale-110",
                        gradient
                    )}>
                        <Icon className="h-6 w-6 text-white" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
