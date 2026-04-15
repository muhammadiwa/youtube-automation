"use client"

import { useState } from "react"
import { Download, FileText, FileSpreadsheet, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useToast } from "@/components/ui/toast"
import adminApi from "@/lib/api/admin"
import type { DateRange } from "./date-range-filter"

interface ExportButtonProps {
    dateRange: DateRange
    metrics?: string[]
}

/**
 * Export Button Component
 * 
 * Provides dashboard export functionality with format selection (CSV, PDF).
 * Requirements: 2.5 - Generate CSV or PDF report with selected metrics
 */
export function ExportButton({ dateRange, metrics = ["platform", "growth", "realtime"] }: ExportButtonProps) {
    const [isExporting, setIsExporting] = useState(false)
    const [exportFormat, setExportFormat] = useState<"csv" | "pdf" | null>(null)
    const { addToast } = useToast()

    const handleExport = async (format: "csv" | "pdf") => {
        setIsExporting(true)
        setExportFormat(format)

        // Show starting toast
        addToast({
            type: "info",
            title: "Export Started",
            description: `Generating ${format.toUpperCase()} report...`,
            duration: 3000,
        })

        try {
            const response = await adminApi.exportDashboard({
                format,
                metrics,
                start_date: dateRange.startDate.toISOString(),
                end_date: dateRange.endDate.toISOString(),
                include_charts: format === "pdf",
            })

            // Poll for completion
            let attempts = 0
            const maxAttempts = 30 // 30 seconds max

            const pollStatus = async () => {
                try {
                    const status = await adminApi.getExportStatus(response.export_id)

                    if (status.status === "completed" && status.download_url) {
                        // Download the file
                        window.open(status.download_url, "_blank")

                        addToast({
                            type: "success",
                            title: "Export Complete",
                            description: `Your ${format.toUpperCase()} report is ready for download.`,
                            duration: 5000,
                        })

                        setIsExporting(false)
                        setExportFormat(null)
                    } else if (status.status === "failed") {
                        addToast({
                            type: "error",
                            title: "Export Failed",
                            description: "Failed to generate the report. Please try again.",
                            duration: 5000,
                        })
                        setIsExporting(false)
                        setExportFormat(null)
                    } else if (attempts < maxAttempts) {
                        attempts++
                        setTimeout(pollStatus, 1000)
                    } else {
                        addToast({
                            type: "error",
                            title: "Export Timeout",
                            description: "Export is taking too long. Please try again later.",
                            duration: 5000,
                        })
                        setIsExporting(false)
                        setExportFormat(null)
                    }
                } catch (pollError) {
                    console.error("Failed to check export status:", pollError)
                    addToast({
                        type: "error",
                        title: "Export Error",
                        description: "Failed to check export status. Please try again.",
                        duration: 5000,
                    })
                    setIsExporting(false)
                    setExportFormat(null)
                }
            }

            // Start polling after a short delay
            setTimeout(pollStatus, 500)
        } catch (error) {
            console.error("Failed to start export:", error)
            addToast({
                type: "error",
                title: "Export Failed",
                description: "Failed to start export. Please try again.",
                duration: 5000,
            })
            setIsExporting(false)
            setExportFormat(null)
        }
    }

    const formatDateRange = () => {
        const start = dateRange.startDate.toLocaleDateString()
        const end = dateRange.endDate.toLocaleDateString()
        return `${start} - ${end}`
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" disabled={isExporting}>
                    {isExporting ? (
                        <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Exporting {exportFormat?.toUpperCase()}...</span>
                        </>
                    ) : (
                        <>
                            <Download className="h-4 w-4" />
                            <span>Export</span>
                        </>
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="text-xs text-muted-foreground">
                    Export data for {formatDateRange()}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                    onClick={() => handleExport("csv")}
                    disabled={isExporting}
                    className="cursor-pointer"
                >
                    <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
                    <div className="flex flex-col">
                        <span>Export as CSV</span>
                        <span className="text-xs text-muted-foreground">Spreadsheet format</span>
                    </div>
                </DropdownMenuItem>
                <DropdownMenuItem
                    onClick={() => handleExport("pdf")}
                    disabled={isExporting}
                    className="cursor-pointer"
                >
                    <FileText className="h-4 w-4 mr-2 text-red-600" />
                    <div className="flex flex-col">
                        <span>Export as PDF</span>
                        <span className="text-xs text-muted-foreground">Printable report</span>
                    </div>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
