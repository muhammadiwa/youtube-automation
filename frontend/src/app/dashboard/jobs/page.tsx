"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import {
    ListTodo,
    RefreshCw,
    Clock,
    CheckCircle2,
    XCircle,
    Loader2,
    AlertTriangle,
    ChevronLeft,
    ChevronRight,
    Search,
    Play,
    RotateCcw,
    Eye,
    Inbox,
} from "lucide-react";
import { jobsApi, Job, JobStatus, JobType, QueueStats } from "@/lib/api/jobs";
import { formatDistanceToNow } from "date-fns";

const JOB_TYPE_LABELS: Record<JobType, string> = {
    video_upload: "Video Upload",
    video_transcode: "Video Transcode",
    stream_start: "Stream Start",
    stream_stop: "Stream Stop",
    ai_title_generation: "AI Title Generation",
    ai_thumbnail_generation: "AI Thumbnail Generation",
    analytics_sync: "Analytics Sync",
    notification_send: "Notification Send",
};

const STATUS_CONFIG: Record<JobStatus, { label: string; color: string; icon: React.ReactNode }> = {
    queued: { label: "Queued", color: "bg-blue-500/10 text-blue-500", icon: <Clock className="h-3 w-3" /> },
    processing: { label: "Processing", color: "bg-yellow-500/10 text-yellow-500", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
    completed: { label: "Completed", color: "bg-green-500/10 text-green-500", icon: <CheckCircle2 className="h-3 w-3" /> },
    failed: { label: "Failed", color: "bg-red-500/10 text-red-500", icon: <XCircle className="h-3 w-3" /> },
    dlq: { label: "Dead Letter", color: "bg-purple-500/10 text-purple-500", icon: <AlertTriangle className="h-3 w-3" /> },
};


// Mock data for development
const mockStats: QueueStats = {
    total_jobs: 1247,
    queued: 23,
    processing: 5,
    completed: 1189,
    failed: 18,
    dlq: 12,
    processing_rate: 45.2,
    average_duration: 12.5,
};

const mockJobs: Job[] = [
    {
        id: "job-001",
        type: "video_upload",
        payload: { video_id: "vid-123", title: "My Awesome Video" },
        priority: 1,
        attempts: 1,
        max_attempts: 3,
        status: "completed",
        created_at: new Date(Date.now() - 3600000).toISOString(),
        started_at: new Date(Date.now() - 3500000).toISOString(),
        completed_at: new Date(Date.now() - 3000000).toISOString(),
        progress: 100,
    },
    {
        id: "job-002",
        type: "video_transcode",
        payload: { video_id: "vid-124", resolution: "1080p" },
        priority: 2,
        attempts: 1,
        max_attempts: 3,
        status: "processing",
        created_at: new Date(Date.now() - 1800000).toISOString(),
        started_at: new Date(Date.now() - 1200000).toISOString(),
        progress: 67,
    },
    {
        id: "job-003",
        type: "ai_title_generation",
        payload: { video_id: "vid-125" },
        priority: 3,
        attempts: 1,
        max_attempts: 3,
        status: "queued",
        created_at: new Date(Date.now() - 600000).toISOString(),
    },
    {
        id: "job-004",
        type: "stream_start",
        payload: { stream_id: "str-001", channel: "My Channel" },
        priority: 1,
        attempts: 3,
        max_attempts: 3,
        status: "failed",
        error: "Connection timeout: Unable to establish RTMP connection",
        created_at: new Date(Date.now() - 7200000).toISOString(),
        started_at: new Date(Date.now() - 7100000).toISOString(),
    },
    {
        id: "job-005",
        type: "analytics_sync",
        payload: { account_id: "acc-001" },
        priority: 5,
        attempts: 3,
        max_attempts: 3,
        status: "dlq",
        error: "API rate limit exceeded after multiple retries",
        created_at: new Date(Date.now() - 86400000).toISOString(),
    },
    {
        id: "job-006",
        type: "ai_thumbnail_generation",
        payload: { video_id: "vid-126", style: "gaming" },
        priority: 2,
        attempts: 1,
        max_attempts: 3,
        status: "processing",
        created_at: new Date(Date.now() - 300000).toISOString(),
        started_at: new Date(Date.now() - 200000).toISOString(),
        progress: 34,
    },
    {
        id: "job-007",
        type: "notification_send",
        payload: { user_id: "usr-001", type: "email" },
        priority: 4,
        attempts: 1,
        max_attempts: 3,
        status: "completed",
        created_at: new Date(Date.now() - 900000).toISOString(),
        completed_at: new Date(Date.now() - 850000).toISOString(),
        progress: 100,
    },
];

export default function JobsPage() {
    const [jobs, setJobs] = useState<Job[]>(mockJobs);
    const [stats, setStats] = useState<QueueStats>(mockStats);
    const [loading, setLoading] = useState(false);
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [typeFilter, setTypeFilter] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [requeueLoading, setRequeueLoading] = useState<string | null>(null);
    const pageSize = 10;

    const filteredJobs = jobs.filter((job) => {
        if (statusFilter !== "all" && job.status !== statusFilter) return false;
        if (typeFilter !== "all" && job.type !== typeFilter) return false;
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            return (
                job.id.toLowerCase().includes(query) ||
                JOB_TYPE_LABELS[job.type].toLowerCase().includes(query)
            );
        }
        return true;
    });

    const totalPages = Math.ceil(filteredJobs.length / pageSize);
    const paginatedJobs = filteredJobs.slice(
        (currentPage - 1) * pageSize,
        currentPage * pageSize
    );

    const handleRequeue = async (jobId: string) => {
        setRequeueLoading(jobId);
        try {
            // In production: await jobsApi.requeueJob(jobId);
            await new Promise((resolve) => setTimeout(resolve, 1000));
            setJobs((prev) =>
                prev.map((job) =>
                    job.id === jobId ? { ...job, status: "queued" as JobStatus, attempts: 0 } : job
                )
            );
        } finally {
            setRequeueLoading(null);
        }
    };

    const handleRefresh = async () => {
        setLoading(true);
        try {
            // In production: const data = await jobsApi.getJobs({ status, type, page, page_size });
            await new Promise((resolve) => setTimeout(resolve, 500));
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Job Queue</h1>
                        <p className="text-muted-foreground">
                            Monitor and manage background jobs
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Link href="/dashboard/jobs/dlq">
                            <Button variant="outline" className="gap-2">
                                <Inbox className="h-4 w-4" />
                                DLQ ({stats.dlq})
                            </Button>
                        </Link>
                        <Button onClick={handleRefresh} disabled={loading} className="gap-2">
                            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                            Refresh
                        </Button>
                    </div>
                </div>


                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/10">
                                    <ListTodo className="h-5 w-5 text-blue-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.total_jobs}</p>
                                    <p className="text-xs text-muted-foreground">Total Jobs</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/10">
                                    <Clock className="h-5 w-5 text-blue-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.queued}</p>
                                    <p className="text-xs text-muted-foreground">Queued</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-yellow-500/10">
                                    <Loader2 className="h-5 w-5 text-yellow-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.processing}</p>
                                    <p className="text-xs text-muted-foreground">Processing</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-green-500/10">
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.completed}</p>
                                    <p className="text-xs text-muted-foreground">Completed</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-red-500/10">
                                    <XCircle className="h-5 w-5 text-red-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.failed}</p>
                                    <p className="text-xs text-muted-foreground">Failed</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-purple-500/10">
                                    <AlertTriangle className="h-5 w-5 text-purple-500" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stats.dlq}</p>
                                    <p className="text-xs text-muted-foreground">Dead Letter</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Filters */}
                <Card>
                    <CardContent className="p-4">
                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search jobs..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-full sm:w-[180px]">
                                    <SelectValue placeholder="Filter by status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="queued">Queued</SelectItem>
                                    <SelectItem value="processing">Processing</SelectItem>
                                    <SelectItem value="completed">Completed</SelectItem>
                                    <SelectItem value="failed">Failed</SelectItem>
                                    <SelectItem value="dlq">Dead Letter</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={typeFilter} onValueChange={setTypeFilter}>
                                <SelectTrigger className="w-full sm:w-[200px]">
                                    <SelectValue placeholder="Filter by type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Types</SelectItem>
                                    <SelectItem value="video_upload">Video Upload</SelectItem>
                                    <SelectItem value="video_transcode">Video Transcode</SelectItem>
                                    <SelectItem value="stream_start">Stream Start</SelectItem>
                                    <SelectItem value="stream_stop">Stream Stop</SelectItem>
                                    <SelectItem value="ai_title_generation">AI Title</SelectItem>
                                    <SelectItem value="ai_thumbnail_generation">AI Thumbnail</SelectItem>
                                    <SelectItem value="analytics_sync">Analytics Sync</SelectItem>
                                    <SelectItem value="notification_send">Notification</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>


                {/* Jobs Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Jobs ({filteredJobs.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Job ID</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Progress</TableHead>
                                    <TableHead>Attempts</TableHead>
                                    <TableHead>Created</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {paginatedJobs.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center py-8">
                                            <div className="flex flex-col items-center gap-2 text-muted-foreground">
                                                <ListTodo className="h-8 w-8" />
                                                <p>No jobs found</p>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    paginatedJobs.map((job) => {
                                        const statusConfig = STATUS_CONFIG[job.status];
                                        return (
                                            <TableRow key={job.id}>
                                                <TableCell className="font-mono text-sm">
                                                    {job.id}
                                                </TableCell>
                                                <TableCell>
                                                    <span className="text-sm">
                                                        {JOB_TYPE_LABELS[job.type]}
                                                    </span>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge
                                                        variant="secondary"
                                                        className={`gap-1 ${statusConfig.color}`}
                                                    >
                                                        {statusConfig.icon}
                                                        {statusConfig.label}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    {job.status === "processing" && job.progress !== undefined ? (
                                                        <div className="flex items-center gap-2 w-24">
                                                            <Progress value={job.progress} className="h-2" />
                                                            <span className="text-xs text-muted-foreground">
                                                                {job.progress}%
                                                            </span>
                                                        </div>
                                                    ) : job.status === "completed" ? (
                                                        <span className="text-xs text-green-500">100%</span>
                                                    ) : (
                                                        <span className="text-xs text-muted-foreground">-</span>
                                                    )}
                                                </TableCell>
                                                <TableCell>
                                                    <span className="text-sm">
                                                        {job.attempts}/{job.max_attempts}
                                                    </span>
                                                </TableCell>
                                                <TableCell>
                                                    <span className="text-sm text-muted-foreground">
                                                        {formatDistanceToNow(new Date(job.created_at), {
                                                            addSuffix: true,
                                                        })}
                                                    </span>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <div className="flex items-center justify-end gap-1">
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="h-8 w-8"
                                                            onClick={() => setSelectedJob(job)}
                                                        >
                                                            <Eye className="h-4 w-4" />
                                                        </Button>
                                                        {(job.status === "failed" || job.status === "dlq") && (
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
                                                        )}
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })
                                )}
                            </TableBody>
                        </Table>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex items-center justify-between mt-4 pt-4 border-t">
                                <p className="text-sm text-muted-foreground">
                                    Showing {(currentPage - 1) * pageSize + 1} to{" "}
                                    {Math.min(currentPage * pageSize, filteredJobs.length)} of{" "}
                                    {filteredJobs.length} jobs
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
                                    <span className="text-sm">
                                        Page {currentPage} of {totalPages}
                                    </span>
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
                    </CardContent>
                </Card>


                {/* Job Detail Modal */}
                <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
                    <DialogContent className="max-w-lg">
                        <DialogHeader>
                            <DialogTitle>Job Details</DialogTitle>
                            <DialogDescription>
                                {selectedJob?.id}
                            </DialogDescription>
                        </DialogHeader>
                        {selectedJob && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Type</p>
                                        <p className="font-medium">{JOB_TYPE_LABELS[selectedJob.type]}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Status</p>
                                        <Badge
                                            variant="secondary"
                                            className={`gap-1 ${STATUS_CONFIG[selectedJob.status].color}`}
                                        >
                                            {STATUS_CONFIG[selectedJob.status].icon}
                                            {STATUS_CONFIG[selectedJob.status].label}
                                        </Badge>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Priority</p>
                                        <p className="font-medium">{selectedJob.priority}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Attempts</p>
                                        <p className="font-medium">
                                            {selectedJob.attempts}/{selectedJob.max_attempts}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-muted-foreground">Created</p>
                                        <p className="font-medium text-sm">
                                            {new Date(selectedJob.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                    {selectedJob.started_at && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">Started</p>
                                            <p className="font-medium text-sm">
                                                {new Date(selectedJob.started_at).toLocaleString()}
                                            </p>
                                        </div>
                                    )}
                                    {selectedJob.completed_at && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">Completed</p>
                                            <p className="font-medium text-sm">
                                                {new Date(selectedJob.completed_at).toLocaleString()}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {selectedJob.progress !== undefined && selectedJob.status === "processing" && (
                                    <div>
                                        <p className="text-sm text-muted-foreground mb-2">Progress</p>
                                        <div className="flex items-center gap-3">
                                            <Progress value={selectedJob.progress} className="flex-1" />
                                            <span className="text-sm font-medium">{selectedJob.progress}%</span>
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <p className="text-sm text-muted-foreground mb-2">Payload</p>
                                    <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-32">
                                        {JSON.stringify(selectedJob.payload, null, 2)}
                                    </pre>
                                </div>

                                {selectedJob.error && (
                                    <div>
                                        <p className="text-sm text-muted-foreground mb-2">Error</p>
                                        <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
                                            <p className="text-sm text-red-500">{selectedJob.error}</p>
                                        </div>
                                    </div>
                                )}

                                {(selectedJob.status === "failed" || selectedJob.status === "dlq") && (
                                    <Button
                                        className="w-full gap-2"
                                        onClick={() => {
                                            handleRequeue(selectedJob.id);
                                            setSelectedJob(null);
                                        }}
                                    >
                                        <RotateCcw className="h-4 w-4" />
                                        Requeue Job
                                    </Button>
                                )}
                            </div>
                        )}
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}
