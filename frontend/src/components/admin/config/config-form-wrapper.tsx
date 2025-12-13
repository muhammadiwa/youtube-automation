"use client"

import * as React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import { Save, Loader2, RotateCcw, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/components/ui/toast"

interface ConfigFormWrapperProps {
    title: string
    description: string
    icon: React.ReactNode
    children: React.ReactNode
    onSave: () => Promise<void>
    onReset: () => void
    isDirty: boolean
    isLoading?: boolean
}

export function ConfigFormWrapper({
    title,
    description,
    icon,
    children,
    onSave,
    onReset,
    isDirty,
    isLoading = false,
}: ConfigFormWrapperProps) {
    const [isSaving, setIsSaving] = useState(false)
    const [saveSuccess, setSaveSuccess] = useState(false)
    const { addToast } = useToast()

    const handleSave = async () => {
        setIsSaving(true)
        setSaveSuccess(false)
        try {
            await onSave()
            setSaveSuccess(true)
            addToast({
                type: "success",
                title: "Configuration saved",
                description: "Your changes have been saved successfully.",
            })
            setTimeout(() => setSaveSuccess(false), 2000)
        } catch (error) {
            console.error("Failed to save configuration:", error)
            addToast({
                type: "error",
                title: "Failed to save",
                description: "An error occurred while saving the configuration.",
            })
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="p-6"
        >
            <Card className="border border-slate-200/60 dark:border-slate-700/60">
                <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                {icon}
                            </div>
                            <div>
                                <CardTitle className="text-xl">{title}</CardTitle>
                                <CardDescription className="mt-1">
                                    {description}
                                </CardDescription>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={onReset}
                                disabled={!isDirty || isSaving || isLoading}
                            >
                                <RotateCcw className="h-4 w-4 mr-2" />
                                Reset
                            </Button>
                            <Button
                                size="sm"
                                onClick={handleSave}
                                disabled={!isDirty || isSaving || isLoading}
                                className="min-w-[100px]"
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Saving...
                                    </>
                                ) : saveSuccess ? (
                                    <>
                                        <CheckCircle2 className="h-4 w-4 mr-2 text-emerald-500" />
                                        Saved
                                    </>
                                ) : (
                                    <>
                                        <Save className="h-4 w-4 mr-2" />
                                        Save
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                        </div>
                    ) : (
                        children
                    )}
                </CardContent>
            </Card>
        </motion.div>
    )
}
