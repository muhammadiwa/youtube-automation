"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
    ArrowLeft,
    AlertTriangle,
    RefreshCw,
    Loader2,
    Eye,
    RotateCcw,
    Trash2,
    Inbox,
    ChevronLeft,
    ChevronRight,
} from "lucide-react";
import { jobsApi, Job, JobType } from "@/lib/api/jobs";
import { formatDistanceToNow } from "date-fns";

const JOB_TYPE_LABELS: Record<string, string> = {
    video_upload: "Video Upload",
    video_transcode: "Video Transcode",
    stream_start: "Stream Start",
    stream_stop: "Stream Stop",
    ai_title_generation: "AI Title Generation",
    ai_thumbnail_generation: "AI Thumbnail Generation",
    analytics_sync: "Analytics Sync",
    notification_send: "Notification Send",
};

export default function DLQPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [total, setTotal] = useState(0);
    const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set());
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [loading, setLoading] = useState(true);
    const [requeueLoading, setRequeueLoading] = useState<string | null>(null);
    const [bulkRequeueLoading, setBulkRequeueLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const pageSize = 20;

    const totalPages = Math.ceil(total / pageSize);

    // Fetch DLQ jobs from API
    const fetchDLQJobs = useCallback(async () => {
        try {
            const offset = (currentPage - 1) * pageSize;
            const response = await jobsApi.getDLQJobs(pageSize, offset);
            setJobs(response.items);
            setTotal(response.total);
        } catch (error) {
            console.error("Failed to fetch DLQ jobs:", error);
        }
    }, [currentPage]);

    // Initial load
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await fetchDLQJobs();
            setLoading(false);
        };
        loadData();
    }, [fetchDLQJobs]);

    const handleSelectAll = (checked: boolean) => {
        if (checked) {
            setSelectedJobs(new Set(jobs.map((j) => j.id)));
        } else {
            setSelectedJobs(new Set());
        }
    };

    const handleSelectJob = (jobId: string, checked: boolean) => {
        const newSelected = new Set(selectedJobs);
        if (checked) {
            newSelected.add(jobId);
        } else {
            newSelected.delete(jobId);
        }
        setSelectedJobs(newSelected);
    };

    const handleRequeue = async (jobId: string) => {
        setRequeueLoading(jobId);
        try {
            await jobsApi.requeueJob(jobId);
            await fetchDLQJobs();
            setSelectedJobs((prev) => {
                const newSet = new Set(prev);
                newSet.delete(jobId);
                return newSet;
            });
        } catch (error) {
            console.error("Failed to requeue job:", error);
        } finally {
            setRequeueLoading(null);
        }
    };

    const handleBulkRequeue = async () => {
        if (selectedJobs.size === 0) return;
        setBulkRequeueLoading(true);
        try {
            await jobsApi.bulkRequeueJobs(Array.from(selectedJobs));
            await fetchDLQJobs();
            setSelectedJobs(new Set());
        } catch (error) {
            console.error("Failed to bulk requeue jobs:", error);
        } finally {
            setBulkRequeueLoading(false);
        }
    };

    const handleRefresh = async () => {
        setLoading(true);
        await fetchDLQJobs();
        setLoading(false);
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard/jobs">
                            <Button variant="ghost" size="icon">
                                <ArrowLeft className="h-4 w-4" />
                            </Button>
                        </Link>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                                <AlertTriangle className="h-6 w-6 text-purple-500" />
                                Dead Letter Queue
                            </h1>
                            <p className="text-muted-foreground">
                                Jobs that failed after maximum retry attempts
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {selectedJobs.size > 0 && (
                            <Button
                                variant="default"
                                onClick={handleBulkRequeue}
                                disabled={bulkRequeueLoading}
                                className="gap-2"
                            >
                                {bulkRequeueLoading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <RotateCcw className="h-4 w-4" />
                                )}
                                Reprocess Selected ({selectedJobs.size})
                            </Button>
                        )}
                        <Button onClick={handleRefresh} disabled={loading} variant="outline" className="gap-2">
                            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            Refresh
                        </Button>
                    </div>
                </div>

                {/* Info Banner */}
                <Card className="border-purple-500/20 bg-purple-500/5">
                    <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-purple-500 mt-0.5" />
                            <div>
                                <p className="font-medium text-purple-500">About Dead Letter Queue</p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Jobs in the DLQ have failed after exhausting all retry attempts.
                                    Review the error details and reprocess them after fixing the underlying issue.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>


                {/* DLQ Jobs Table */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Inbox className="h-5 w-5" />
                            Failed Jobs ({total})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </div>
                        ) : jobs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                                <Inbox className="h-12 w-12 mb-4" />
                                <p className="text-lg font-medium">DLQ is empty</p>
                                <p className="text-sm">No failed jobs requiring attention</p>
                            </div>
                        ) : (
                            <>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-12">
                                                <Checkbox
                                                    checked={jobs.length > 0 && jobs.every((j) => selectedJobs.has(j.id))}
                                                    onCheckedChange={handleSelectAll}
                                                />
                                            </TableHead>
                                            <TableHead>Job ID</TableHead>
                                            <TableHead>Type</TableHead>
                                            <TableHead>Error</TableHead>
                                            <TableHead>Attempts</TableHead>
                                            <TableHead>Failed At</TableHead>
                                            <TableHead className="text-right">Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {jobs.map((job) => (
                                            <TableRow key={job.id}>
                                                <TableCell>
                                                    <Checkbox
                                                        checked={selectedJobs.has(job.id)}
                                                        onCheckedChange={(checked) => handleSelectJob(job.id, checked as boolean)}
                                                    />
                                                </TableCell>
                                                <TableCell className="font-mono text-sm">
                                                    {job.id.slice(0, 8)}...
                                                </TableCell>
                                                <TableCell>
                                                    <span className="text-sm">{JOB_TYPE_LABELS[job.type] || job.type}</span>
                                                </TableCell>
                                                <TableCell className="max-w-xs">
                                                    <p className="text-sm text-red-500 truncate">{job.error}</p>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="secondary" className="bg-red-500/10 text-red-500">
                                                        {job.attempts}/{job.max_attempts}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <span className="text-sm text-muted-foreground">
                                                        {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <div className="flex items-center justify-end gap-1">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setSelectedJob(job)}>
                                                            <Eye className="h-4 w-4" />
                                                        </Button>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="h-8 w-8"
                                                            onClick={() => handleRequeue(job.id)}
                                                            disabled={requeueLoading === job.id}
                                                        >
                                                            {requeueLoading === job.id ? (
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            ) : (
                                                                <RotateCcw className="h-4 w-4" />
                                                            )}
                                                        </Button>
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>

                                {/* Pagination */}
                                {totalPages > 1 && (
                                    <div className="flex items-center justify-between mt-4 pt-4 border-t">
                                        <p className="text-sm text-muted-foreground">
                                            Page {currentPage} of {totalPages} ({total} total)
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                                                disabled={currentPage === 1}
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                            </Button>
                                            <span className="text-sm">Page {currentPage} of {totalPages}</span>
                                            <Button
                                                variant="outline"
                                                size="icon"
                                                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                                                disabled={currentPage === totalPages}
                                            >
                                                <ChevronRight className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </CardContent>
                </Card>


                {/* Error Detail Modal */}
                <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
                    <DialogContent className="max-w-lg">
                        <DialogHeader>
                            <DialogTitle>Job Error Details</DialogTitle>
                            <DialogDescription>{selectedJob?.id}</DialogDescription>
                        </DialogHeader>
                        {selectedJob && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Type</p>
                                        <p className="font-medium">{JOB_TYPE_LABELS[selectedJob.type] || selectedJob.type}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Priority</p>
                                        <p className="font-medium">{selectedJob.priority}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Attempts</p>
                                        <p className="font-medium">{selectedJob.attempts}/{selectedJob.max_attempts}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Created</p>
                                        <p className="font-medium text-sm">{new Date(selectedJob.created_at).toLocaleString()}</p>
                                    </div>
                                </div>

                                <div>
                                    <p className="text-sm text-muted-foreground mb-2">Payload</p>
                                    <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-32">
                                        {JSON.stringify(selectedJob.payload, null, 2)}
                                    </pre>
                                </div>

                                <div>
                                    <p className="text-sm text-muted-foreground mb-2">Error Message</p>
                                    <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
                                        <p className="text-sm text-red-500">{selectedJob.error}</p>
                                    </div>
                                </div>

                                {selectedJob.error_details && (
                                    <div>
                                        <p className="text-sm text-muted-foreground mb-2">Error Details</p>
                                        <pre className="bg-red-500/5 p-3 rounded-lg text-xs overflow-auto max-h-32 text-red-500">
                                            {JSON.stringify(selectedJob.error_details, null, 2)}
                                        </pre>
                                    </div>
                                )}

                                <div className="flex gap-2">
                                    <Button
                                        className="flex-1 gap-2"
                                        onClick={() => {
                                            handleRequeue(selectedJob.id);
                                            setSelectedJob(null);
                                        }}
                                    >
                                        <RotateCcw className="h-4 w-4" />
                                        Reprocess Job
                                    </Button>
                                </div>
                            </div>
                        )}
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}
