"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Lightbulb,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    Sparkles,
    Target,
    ArrowRight,
    X,
    RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { aiInsightsApi, AIInsight } from "@/lib/api/analytics";
import { cn } from "@/lib/utils";

interface AIInsightsPanelProps {
    accountId?: string;
    limit?: number;
    className?: string;
}

export function AIInsightsPanel({ accountId, limit = 5, className }: AIInsightsPanelProps) {
    const [insights, setInsights] = useState<AIInsight[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        loadInsights();
    }, [accountId]);

    const loadInsights = async () => {
        setLoading(true);
        try {
            const data = await aiInsightsApi.getInsights({
                account_id: accountId,
                limit,
            });
            setInsights(data);
        } catch (error) {
            console.error("Failed to load AI insights:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadInsights();
        setRefreshing(false);
    };

    const handleDismiss = async (insightId: string) => {
        try {
            await aiInsightsApi.dismissInsight(insightId);
            setInsights(prev => prev.filter(i => i.id !== insightId));
        } catch (error) {
            // Still remove from UI even if API fails
            setInsights(prev => prev.filter(i => i.id !== insightId));
        }
    };

    const getInsightIcon = (type: AIInsight["type"]) => {
        switch (type) {
            case "growth":
                return TrendingUp;
            case "optimization":
                return Target;
            case "warning":
                return AlertTriangle;
            case "trend":
                return Sparkles;
            case "recommendation":
                return Lightbulb;
            default:
                return Lightbulb;
        }
    };

    const getInsightColor = (type: AIInsight["type"]) => {
        switch (type) {
            case "growth":
                return "text-green-500 bg-green-500/10";
            case "optimization":
                return "text-blue-500 bg-blue-500/10";
            case "warning":
                return "text-amber-500 bg-amber-500/10";
            case "trend":
                return "text-purple-500 bg-purple-500/10";
            case "recommendation":
                return "text-cyan-500 bg-cyan-500/10";
            default:
                return "text-gray-500 bg-gray-500/10";
        }
    };

    const getPriorityBadge = (priority: AIInsight["priority"]) => {
        switch (priority) {
            case "high":
                return "bg-red-500/10 text-red-500 border-red-500/20";
            case "medium":
                return "bg-amber-500/10 text-amber-500 border-amber-500/20";
            case "low":
                return "bg-green-500/10 text-green-500 border-green-500/20";
            default:
                return "bg-gray-500/10 text-gray-500 border-gray-500/20";
        }
    };

    if (loading) {
        return (
            <Card className={cn("border-0 bg-card shadow-lg", className)}>
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5 text-amber-500" />
                        <CardTitle className="text-lg">AI Insights</CardTitle>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="p-4 rounded-xl border animate-pulse">
                                <div className="h-4 bg-muted rounded w-1/3 mb-2" />
                                <div className="h-3 bg-muted rounded w-full mb-1" />
                                <div className="h-3 bg-muted rounded w-2/3" />
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className={cn("border-0 bg-gradient-to-br from-purple-500/5 via-blue-500/5 to-cyan-500/5 shadow-lg", className)}>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5 text-amber-500" />
                        <CardTitle className="text-lg">AI Insights</CardTitle>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                {insights.length === 0 ? (
                    <div className="text-center py-8">
                        <Sparkles className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                        <p className="text-sm text-muted-foreground">
                            No insights available at the moment
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                            Check back later for AI-powered recommendations
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {insights.map((insight) => {
                            const Icon = getInsightIcon(insight.type);
                            const colorClass = getInsightColor(insight.type);
                            const priorityClass = getPriorityBadge(insight.priority);

                            return (
                                <div
                                    key={insight.id}
                                    className="p-4 bg-card rounded-xl border hover:shadow-md transition-all group"
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={cn("p-2 rounded-lg shrink-0", colorClass)}>
                                            <Icon className="h-4 w-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h4 className="text-sm font-semibold">{insight.title}</h4>
                                                <span className={cn(
                                                    "px-1.5 py-0.5 text-[10px] font-medium rounded border",
                                                    priorityClass
                                                )}>
                                                    {insight.priority}
                                                </span>
                                                {insight.change_percentage !== undefined && (
                                                    <span className={cn(
                                                        "flex items-center gap-0.5 text-xs font-medium",
                                                        insight.change_percentage >= 0 ? "text-green-500" : "text-red-500"
                                                    )}>
                                                        {insight.change_percentage >= 0 ? (
                                                            <TrendingUp className="h-3 w-3" />
                                                        ) : (
                                                            <TrendingDown className="h-3 w-3" />
                                                        )}
                                                        {Math.abs(insight.change_percentage)}%
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-muted-foreground mb-3">
                                                {insight.description}
                                            </p>
                                            <div className="flex items-center gap-2">
                                                {insight.action_url && insight.action_label && (
                                                    <Link href={insight.action_url}>
                                                        <Button size="sm" variant="outline" className="h-7 text-xs">
                                                            {insight.action_label}
                                                            <ArrowRight className="h-3 w-3 ml-1" />
                                                        </Button>
                                                    </Link>
                                                )}
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    className="h-7 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                                                    onClick={() => handleDismiss(insight.id)}
                                                >
                                                    <X className="h-3 w-3 mr-1" />
                                                    Dismiss
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
