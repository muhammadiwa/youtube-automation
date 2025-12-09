"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, Radio, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";

export function QuickActions() {
    const router = useRouter();

    const actions = [
        {
            label: "Upload Video",
            icon: Upload,
            onClick: () => router.push("/dashboard/videos/upload"),
            variant: "default" as const,
        },
        {
            label: "Start Stream",
            icon: Radio,
            onClick: () => router.push("/dashboard/streams/create"),
            variant: "default" as const,
        },
        {
            label: "Connect Account",
            icon: UserPlus,
            onClick: () => router.push("/dashboard/accounts"),
            variant: "outline" as const,
        },
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
                {actions.map((action) => (
                    <Button
                        key={action.label}
                        variant={action.variant}
                        onClick={action.onClick}
                        className="flex-1 min-w-[150px]"
                    >
                        <action.icon className="mr-2 h-4 w-4" />
                        {action.label}
                    </Button>
                ))}
            </CardContent>
        </Card>
    );
}
