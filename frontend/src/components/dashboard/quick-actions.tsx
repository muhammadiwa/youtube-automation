"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, Radio, UserPlus, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export function QuickActions() {
    const router = useRouter();

    const actions = [
        {
            label: "Upload Video",
            description: "Upload new content",
            icon: Upload,
            onClick: () => router.push("/dashboard/videos/upload"),
            gradient: "from-blue-500 to-blue-600",
            shadowColor: "shadow-blue-500/25",
        },
        {
            label: "Start Stream",
            description: "Go live now",
            icon: Radio,
            onClick: () => router.push("/dashboard/streams/create"),
            gradient: "from-red-500 to-red-600",
            shadowColor: "shadow-red-500/25",
        },
        {
            label: "Connect Account",
            description: "Add YouTube channel",
            icon: UserPlus,
            onClick: () => router.push("/dashboard/accounts"),
            gradient: "from-green-500 to-green-600",
            shadowColor: "shadow-green-500/25",
        },
    ];

    return (
        <Card className="border-0 bg-card shadow-lg">
            <CardHeader className="pb-4">
                <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-yellow-500" />
                    <CardTitle className="text-lg">Quick Actions</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4 sm:grid-cols-3">
                    {actions.map((action) => (
                        <button
                            key={action.label}
                            onClick={action.onClick}
                            className={cn(
                                "group relative flex flex-col items-center gap-3 p-6 rounded-2xl",
                                "bg-gradient-to-br transition-all duration-300",
                                "hover:scale-[1.02] hover:shadow-xl",
                                action.gradient,
                                action.shadowColor
                            )}
                        >
                            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm transition-transform duration-300 group-hover:scale-110">
                                <action.icon className="h-7 w-7 text-white" />
                            </div>
                            <div className="text-center">
                                <p className="font-semibold text-white">{action.label}</p>
                                <p className="text-xs text-white/70 mt-0.5">{action.description}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
