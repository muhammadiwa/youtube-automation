"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    FileText,
    Download,
    Calendar,
    Clock,
    CheckCircle,
    AlertCircle,
    Loader2,
    Plus,
    Eye,
    Trash2,
    FileSpreadsheet,
} from "lucide-react";
import analyticsApi, { AnalyticsReport } from "@/lib/api/analytics";
import accountsApi from "@/lib/api/accounts";
import { YouTubeAccount } from "@/types";
import { cn } from "@/lib/utils";

type ReportType = "daily" | "weekly" | "monthly" | "custom";
type ReportFormat = "pdf" | "csv" | "json";

const AVAILABLE_METRICS = [
    { id: "views", label: "Views", description: "Total video views" },
    { id: "subscribers", label: "Subscribers", description: "Subscriber count changes" },
    { id: "watch_time", label: "Watch Time", description: "Total watch time in hours" },
    { id: "revenue", label: "Revenue", description: "Estimated earnings" },
    { id: "engagement", label: "Engagement", description: "Likes, comments, shares" },
    { id: "traffic_sources", label: "Traffic Sources", description: "Where viewers come from" },
    { id: "demographics", label: "Demographics", description: "Audience age and gender" },
    { id: "top_videos", label: "Top Videos", description: "Best performing content" },
];

export default function ReportsPage() {
    const [accounts, setAccounts] = useState<YouTubeAccount[]>([]);
    const [reports, setReports] = useState<AnalyticsReport[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [showPreview, setShowPreview] = useState(false);

    // Form state
    const [reportName, setReportName] = useState("");
    const [reportType, setReportType] = useState<ReportType>("monthly");
    const [reportFormat, setReportFormat] = useState<ReportFormat>("pdf");
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>(["views", "subscribers", "watch_time", "revenue"]);
    const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [accountsData, reportsData] = await Promise.all([
                accountsApi.getAccounts(),
                analyticsApi.getReports(),
            ]);
            setAccounts(accountsData);
            setReports(reportsData);

            // Select all accounts by default
            if (accountsData.length > 0) {
                setSelectedAccounts(accountsData.map(a => a.id));
            }
        } catch (error) {
            console.error("Failed to load data:", error);
        } finally {
            setLoading(false);
        }
    };

    const toggleMetric = (metricId: string) => {
        setSelectedMetrics(prev => {
            if (prev.includes(metricId)) {
                return prev.filter(id => id !== metricId);
            }
            return [...prev, metricId];
        });
    };

    const toggleAccount = (accountId: string) => {
        setSelectedAccounts(prev => {
            if (prev.includes(accountId)) {
                return prev.filter(id => id !== accountId);
            }
            return [...prev, accountId];
        });
    };

    const handleGenerateReport = async () => {
        if (!reportName || selectedMetrics.length === 0) {
            alert("Please provide a report name and select at least one metric");
            return;
        }

        setGenerating(true);
        try {
            const newReport = await analyticsApi.generateReport({
                name: reportName,
                type: reportType,
                start_date: startDate || undefined,
                end_date: endDate || undefined,
                metrics: selectedMetrics,
                format: reportFormat,
                account_ids: selectedAccounts.length > 0 ? selectedAccounts : undefined,
            });

            setReports(prev => [newReport, ...prev]);
            setShowPreview(false);

            // Reset form
            setReportName("");
            setSelectedMetrics(["views", "subscribers", "watch_time", "revenue"]);
        } catch (error) {
            console.error("Failed to generate report:", error);
            // Add mock report for demo
            const mockReport: AnalyticsReport = {
                id: Date.now().toString(),
                name: reportName,
                type: reportType,
                start_date: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
                end_date: endDate || new Date().toISOString(),
                metrics: selectedMetrics,
                format: reportFormat,
                status: "completed",
                download_url: "#",
                created_at: new Date().toISOString(),
            };
            setReports(prev => [mockReport, ...prev]);
            setShowPreview(false);
            setReportName("");
        } finally {
            setGenerating(false);
        }
    };

    const getStatusIcon = (status: AnalyticsReport["status"]) => {
        switch (status) {
            case "completed":
                return <CheckCircle className="h-4 w-4 text-green-500" />;
            case "generating":
            case "pending":
                return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
            case "failed":
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            default:
                return null;
        }
    };

    const getStatusLabel = (status: AnalyticsReport["status"]) => {
        switch (status) {
            case "completed":
                return "Ready";
            case "generating":
                return "Generating...";
            case "pending":
                return "Pending";
            case "failed":
                return "Failed";
            default:
                return status;
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Analytics", href: "/dashboard/analytics" },
                { label: "Reports" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Report Generator</h1>
                    <p className="text-muted-foreground">
                        Create custom analytics reports in PDF or CSV format
                    </p>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Report Configuration Form */}
                    <div className="lg:col-span-2 space-y-6">
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-lg">Report Configuration</CardTitle>
                                <CardDescription>
                                    Configure your report settings and select metrics to include
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* Report Name */}
                                <div className="space-y-2">
                                    <Label htmlFor="reportName">Report Name</Label>
                                    <Input
                                        id="reportName"
                                        placeholder="e.g., Monthly Performance Report"
                                        value={reportName}
                                        onChange={(e) => setReportName(e.target.value)}
                                    />
                                </div>

                                {/* Report Type & Format */}
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <div className="space-y-2">
                                        <Label>Report Type</Label>
                                        <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="daily">Daily</SelectItem>
                                                <SelectItem value="weekly">Weekly</SelectItem>
                                                <SelectItem value="monthly">Monthly</SelectItem>
                                                <SelectItem value="custom">Custom Range</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Export Format</Label>
                                        <Select value={reportFormat} onValueChange={(v) => setReportFormat(v as ReportFormat)}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="pdf">PDF Document</SelectItem>
                                                <SelectItem value="csv">CSV Spreadsheet</SelectItem>
                                                <SelectItem value="json">JSON Data</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>

                                {/* Custom Date Range */}
                                {reportType === "custom" && (
                                    <div className="grid gap-4 sm:grid-cols-2">
                                        <div className="space-y-2">
                                            <Label htmlFor="startDate">Start Date</Label>
                                            <Input
                                                id="startDate"
                                                type="date"
                                                value={startDate}
                                                onChange={(e) => setStartDate(e.target.value)}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <Label htmlFor="endDate">End Date</Label>
                                            <Input
                                                id="endDate"
                                                type="date"
                                                value={endDate}
                                                onChange={(e) => setEndDate(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* Metrics Selection */}
                                <div className="space-y-3">
                                    <Label>Metrics to Include</Label>
                                    <div className="grid gap-3 sm:grid-cols-2">
                                        {AVAILABLE_METRICS.map((metric) => (
                                            <div
                                                key={metric.id}
                                                className={cn(
                                                    "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all",
                                                    selectedMetrics.includes(metric.id)
                                                        ? "border-primary bg-primary/5"
                                                        : "hover:bg-muted/50"
                                                )}
                                                onClick={() => toggleMetric(metric.id)}
                                            >
                                                <Checkbox checked={selectedMetrics.includes(metric.id)} />
                                                <div>
                                                    <p className="text-sm font-medium">{metric.label}</p>
                                                    <p className="text-xs text-muted-foreground">{metric.description}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Account Selection */}
                                {accounts.length > 0 && (
                                    <div className="space-y-3">
                                        <Label>Channels to Include</Label>
                                        <div className="flex flex-wrap gap-2">
                                            {accounts.map((account) => (
                                                <div
                                                    key={account.id}
                                                    className={cn(
                                                        "flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-all",
                                                        selectedAccounts.includes(account.id)
                                                            ? "border-primary bg-primary/5"
                                                            : "hover:bg-muted/50"
                                                    )}
                                                    onClick={() => toggleAccount(account.id)}
                                                >
                                                    <Checkbox checked={selectedAccounts.includes(account.id)} />
                                                    <span className="text-sm">{account.channelTitle}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex gap-3 pt-4">
                                    <Button
                                        variant="outline"
                                        onClick={() => setShowPreview(true)}
                                        disabled={!reportName || selectedMetrics.length === 0}
                                    >
                                        <Eye className="h-4 w-4 mr-2" />
                                        Preview
                                    </Button>
                                    <Button
                                        onClick={handleGenerateReport}
                                        disabled={generating || !reportName || selectedMetrics.length === 0}
                                    >
                                        {generating ? (
                                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        ) : (
                                            <Plus className="h-4 w-4 mr-2" />
                                        )}
                                        Generate Report
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Preview Modal */}
                        {showPreview && (
                            <Card className="border-0 bg-card shadow-lg">
                                <CardHeader>
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-lg">Report Preview</CardTitle>
                                        <Button variant="ghost" size="sm" onClick={() => setShowPreview(false)}>
                                            Close
                                        </Button>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="p-6 bg-muted/30 rounded-lg border-2 border-dashed">
                                        <div className="text-center mb-6">
                                            <h2 className="text-xl font-bold">{reportName || "Untitled Report"}</h2>
                                            <p className="text-sm text-muted-foreground">
                                                {reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report • {reportFormat.toUpperCase()}
                                            </p>
                                        </div>

                                        <div className="space-y-4">
                                            <div>
                                                <h3 className="text-sm font-semibold mb-2">Included Metrics:</h3>
                                                <div className="flex flex-wrap gap-2">
                                                    {selectedMetrics.map((metricId) => {
                                                        const metric = AVAILABLE_METRICS.find(m => m.id === metricId);
                                                        return (
                                                            <span key={metricId} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
                                                                {metric?.label}
                                                            </span>
                                                        );
                                                    })}
                                                </div>
                                            </div>

                                            {selectedAccounts.length > 0 && (
                                                <div>
                                                    <h3 className="text-sm font-semibold mb-2">Channels:</h3>
                                                    <div className="flex flex-wrap gap-2">
                                                        {selectedAccounts.map((accountId) => {
                                                            const account = accounts.find(a => a.id === accountId);
                                                            return (
                                                                <span key={accountId} className="px-2 py-1 bg-muted text-xs rounded-full">
                                                                    {account?.channelTitle}
                                                                </span>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>

                    {/* Recent Reports */}
                    <div>
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-lg">Recent Reports</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {reports.length === 0 ? (
                                    <div className="text-center py-8">
                                        <FileText className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                                        <p className="text-sm text-muted-foreground">No reports generated yet</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {reports.slice(0, 5).map((report) => (
                                            <div
                                                key={report.id}
                                                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                                            >
                                                <div className="flex items-center gap-3 min-w-0">
                                                    {report.format === "pdf" ? (
                                                        <FileText className="h-8 w-8 text-red-500 shrink-0" />
                                                    ) : (
                                                        <FileSpreadsheet className="h-8 w-8 text-green-500 shrink-0" />
                                                    )}
                                                    <div className="min-w-0">
                                                        <p className="text-sm font-medium truncate">{report.name}</p>
                                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                            {getStatusIcon(report.status)}
                                                            <span>{getStatusLabel(report.status)}</span>
                                                            <span>•</span>
                                                            <span>{formatDate(report.created_at)}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                {report.status === "completed" && report.download_url && (
                                                    <Button variant="ghost" size="icon" asChild>
                                                        <a href={report.download_url} download>
                                                            <Download className="h-4 w-4" />
                                                        </a>
                                                    </Button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
