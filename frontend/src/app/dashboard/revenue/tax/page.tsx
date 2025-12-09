"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    FileText,
    Download,
    DollarSign,
    TrendingUp,
    Receipt,
    Percent,
    Calendar,
    AlertCircle,
    Loader2,
} from "lucide-react";
import analyticsApi, { TaxReport } from "@/lib/api/analytics";

export default function TaxReportsPage() {
    const currentYear = new Date().getFullYear();
    const [selectedYear, setSelectedYear] = useState<string>(currentYear.toString());
    const [taxReport, setTaxReport] = useState<TaxReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);

    // Generate available years (last 5 years)
    const availableYears = Array.from({ length: 5 }, (_, i) => currentYear - i);

    useEffect(() => {
        loadTaxReport();
    }, [selectedYear]);

    const loadTaxReport = async () => {
        setLoading(true);
        try {
            const data = await analyticsApi.getTaxReport(parseInt(selectedYear));
            setTaxReport(data || generateMockTaxReport(parseInt(selectedYear)));
        } catch (error) {
            console.error("Failed to load tax report:", error);
            setTaxReport(generateMockTaxReport(parseInt(selectedYear)));
        } finally {
            setLoading(false);
        }
    };

    const generateMockTaxReport = (year: number): TaxReport => {
        const isCurrentYear = year === currentYear;
        const multiplier = isCurrentYear ? 0.9 : 1;

        return {
            year,
            total_revenue: Math.floor(45000 * multiplier),
            total_ads: Math.floor(32000 * multiplier),
            total_memberships: Math.floor(5500 * multiplier),
            total_super_chat: Math.floor(3200 * multiplier),
            total_merchandise: Math.floor(2800 * multiplier),
            total_youtube_premium: Math.floor(1500 * multiplier),
            tax_withheld: Math.floor(6750 * multiplier),
            net_earnings: Math.floor(38250 * multiplier),
            currency: "USD",
        };
    };

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
        }).format(amount);
    };

    const handleExport = async (format: "pdf" | "csv") => {
        setExporting(true);
        try {
            const result = await analyticsApi.exportTaxReport(parseInt(selectedYear), format);
            if (result.download_url) {
                window.open(result.download_url, "_blank");
            }
        } catch (error) {
            // For demo, show alert
            alert(`Tax report for ${selectedYear} would be exported as ${format.toUpperCase()}`);
        } finally {
            setExporting(false);
        }
    };

    const summaryCards = taxReport ? [
        {
            title: "Total Revenue",
            value: formatCurrency(taxReport.total_revenue),
            icon: DollarSign,
            gradient: "from-green-500 to-emerald-600",
            description: "Gross earnings before tax",
        },
        {
            title: "Tax Withheld",
            value: formatCurrency(taxReport.tax_withheld),
            icon: Percent,
            gradient: "from-red-500 to-red-600",
            description: "Estimated tax withholding",
        },
        {
            title: "Net Earnings",
            value: formatCurrency(taxReport.net_earnings),
            icon: TrendingUp,
            gradient: "from-blue-500 to-blue-600",
            description: "After tax withholding",
        },
    ] : [];

    const breakdownItems = taxReport ? [
        { label: "Ad Revenue", value: taxReport.total_ads, color: "bg-red-500" },
        { label: "Channel Memberships", value: taxReport.total_memberships, color: "bg-orange-500" },
        { label: "Super Chat & Super Thanks", value: taxReport.total_super_chat, color: "bg-yellow-500" },
        { label: "Merchandise Shelf", value: taxReport.total_merchandise, color: "bg-green-500" },
        { label: "YouTube Premium Revenue", value: taxReport.total_youtube_premium, color: "bg-blue-500" },
    ] : [];

    return (
        <DashboardLayout
            breadcrumbs={[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Revenue", href: "/dashboard/revenue" },
                { label: "Tax Reports" },
            ]}
        >
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Tax Reports</h1>
                        <p className="text-muted-foreground">
                            Generate tax-relevant summaries for your YouTube earnings
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Year Selector */}
                        <Select value={selectedYear} onValueChange={setSelectedYear}>
                            <SelectTrigger className="w-[140px]">
                                <Calendar className="h-4 w-4 mr-2" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {availableYears.map((year) => (
                                    <SelectItem key={year} value={year.toString()}>
                                        {year}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        {/* Export Button */}
                        <Button
                            onClick={() => handleExport("pdf")}
                            disabled={exporting || loading}
                            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                        >
                            {exporting ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <Download className="h-4 w-4 mr-2" />
                            )}
                            Export PDF
                        </Button>
                    </div>
                </div>

                {/* Disclaimer */}
                <Card className="border-amber-500/50 bg-amber-500/5">
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5" />
                            <div>
                                <p className="font-medium text-amber-700 dark:text-amber-400">
                                    Tax Information Disclaimer
                                </p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    This report is for informational purposes only and should not be considered tax advice.
                                    Please consult with a qualified tax professional for accurate tax filing.
                                    Actual tax obligations may vary based on your jurisdiction and individual circumstances.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {loading ? (
                    <div className="grid gap-4 md:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <Card key={i} className="border-0 bg-card shadow-lg animate-pulse">
                                <CardContent className="p-6">
                                    <div className="h-4 bg-muted rounded w-1/2 mb-4" />
                                    <div className="h-8 bg-muted rounded w-3/4 mb-2" />
                                    <div className="h-3 bg-muted rounded w-2/3" />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <>
                        {/* Summary Cards */}
                        <div className="grid gap-4 md:grid-cols-3">
                            {summaryCards.map((card, index) => (
                                <Card key={index} className={`border-0 bg-gradient-to-br ${card.gradient} text-white shadow-xl`}>
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-white/80 text-sm font-medium">{card.title}</p>
                                                <p className="text-3xl font-bold mt-1">{card.value}</p>
                                                <p className="text-white/70 text-xs mt-2">{card.description}</p>
                                            </div>
                                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
                                                <card.icon className="h-6 w-6" />
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Revenue Breakdown */}
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <Receipt className="h-5 w-5 text-green-500" />
                                    <CardTitle className="text-lg">Revenue Breakdown - {selectedYear}</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {breakdownItems.map((item, index) => {
                                        const percentage = taxReport ? (item.value / taxReport.total_revenue) * 100 : 0;
                                        return (
                                            <div key={index} className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <div className={`h-3 w-3 rounded-full ${item.color}`} />
                                                        <span className="text-sm font-medium">{item.label}</span>
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <span className="text-sm text-muted-foreground">
                                                            {percentage.toFixed(1)}%
                                                        </span>
                                                        <span className="text-sm font-semibold w-24 text-right">
                                                            {formatCurrency(item.value)}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${item.color} transition-all duration-500`}
                                                        style={{ width: `${percentage}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                {/* Total */}
                                <div className="mt-6 pt-4 border-t">
                                    <div className="flex items-center justify-between">
                                        <span className="font-semibold">Total Gross Revenue</span>
                                        <span className="text-xl font-bold text-green-600">
                                            {formatCurrency(taxReport?.total_revenue || 0)}
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Tax Summary */}
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <FileText className="h-5 w-5 text-blue-500" />
                                    <CardTitle className="text-lg">Tax Summary</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between py-3 border-b">
                                        <span className="text-muted-foreground">Gross Revenue</span>
                                        <span className="font-medium">{formatCurrency(taxReport?.total_revenue || 0)}</span>
                                    </div>
                                    <div className="flex items-center justify-between py-3 border-b">
                                        <span className="text-muted-foreground">Estimated Tax Withheld (15%)</span>
                                        <span className="font-medium text-red-500">
                                            -{formatCurrency(taxReport?.tax_withheld || 0)}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between py-3">
                                        <span className="font-semibold">Net Earnings</span>
                                        <span className="text-xl font-bold text-green-600">
                                            {formatCurrency(taxReport?.net_earnings || 0)}
                                        </span>
                                    </div>
                                </div>

                                <div className="mt-6 p-4 rounded-lg bg-muted/50">
                                    <p className="text-sm text-muted-foreground">
                                        <strong>Note:</strong> The tax withheld amount shown is an estimate based on standard
                                        YouTube withholding rates. Your actual tax liability may differ based on your tax
                                        treaty status, country of residence, and other factors. Please refer to your official
                                        YouTube payment statements for accurate figures.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Export Options */}
                        <Card className="border-0 bg-card shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-2">
                                    <Download className="h-5 w-5 text-purple-500" />
                                    <CardTitle className="text-lg">Export Options</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <Button
                                        variant="outline"
                                        className="h-auto py-4 justify-start"
                                        onClick={() => handleExport("pdf")}
                                        disabled={exporting}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
                                                <FileText className="h-5 w-5 text-red-500" />
                                            </div>
                                            <div className="text-left">
                                                <p className="font-medium">PDF Report</p>
                                                <p className="text-xs text-muted-foreground">
                                                    Formatted for printing and records
                                                </p>
                                            </div>
                                        </div>
                                    </Button>
                                    <Button
                                        variant="outline"
                                        className="h-auto py-4 justify-start"
                                        onClick={() => handleExport("csv")}
                                        disabled={exporting}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                                                <FileText className="h-5 w-5 text-green-500" />
                                            </div>
                                            <div className="text-left">
                                                <p className="font-medium">CSV Export</p>
                                                <p className="text-xs text-muted-foreground">
                                                    For spreadsheets and accounting software
                                                </p>
                                            </div>
                                        </div>
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>
        </DashboardLayout>
    );
}
