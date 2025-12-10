import { apiClient } from "./client";

// Types matching backend schemas
export type JobStatus = "queued" | "processing" | "completed" | "failed" | "dlq";
export type JobType =
    | "video_upload"
    | "video_transcode"
    | "stream_start"
    | "stream_stop"
    | "ai_title_generation"
    | "ai_thumbnail_generation"
    | "analytics_sync"
    | "notification_send";

export interface Job {
    id: string;
    job_type: string;
    payload: Record<string, unknown>;
    priority: number;
    attempts: number;
    max_attempts: number;
    status: JobStatus;
    result?: Record<string, unknown>;
    error?: string;
    error_details?: Record<string, unknown>;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    progress?: number;
    // Computed field for frontend compatibility
    type: JobType;
}

export interface JobsResponse {
    items: Job[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface DLQResponse {
    items: Job[];
    total: number;
    limit: number;
    offset: number;
}

export interface QueueStats {
    total_jobs: number;
    queued: number;
    processing: number;
    completed: number;
    failed: number;
    dlq: number;
    processing_rate: number;
    average_duration: number;
}

export interface JobFilters {
    status?: JobStatus;
    job_type?: string;
    page?: number;
    page_size?: number;
}

// Helper to normalize job data from backend
function normalizeJob(job: Job): Job {
    return {
        ...job,
        type: (job.job_type || job.type) as JobType,
    };
}

// API functions matching backend router.py endpoints
export const jobsApi = {
    /**
     * List jobs with filters
     * Backend: GET /jobs
     */
    async getJobs(filters?: JobFilters): Promise<JobsResponse> {
        const params: Record<string, string | number | boolean | undefined> = {
            status: filters?.status,
            job_type: filters?.job_type,
            page: filters?.page || 1,
            page_size: filters?.page_size || 50,
        };
        const response = await apiClient.get<JobsResponse>("/jobs", params);
        return {
            ...response,
            items: response.items.map(normalizeJob),
        };
    },

    /**
     * Get a single job by ID
     * Backend: GET /jobs/{job_id}
     */
    async getJob(jobId: string): Promise<Job> {
        const job = await apiClient.get<Job>(`/jobs/${jobId}`);
        return normalizeJob(job);
    },

    /**
     * Get queue statistics for dashboard
     * Backend: GET /jobs/stats/queue
     */
    async getQueueStats(): Promise<QueueStats> {
        return apiClient.get<QueueStats>("/jobs/stats/queue");
    },

    /**
     * Get jobs in dead letter queue
     * Backend: GET /jobs/dlq/jobs
     */
    async getDLQJobs(limit?: number, offset?: number): Promise<DLQResponse> {
        const params: Record<string, string | number | boolean | undefined> = {
            limit: limit || 100,
            offset: offset || 0,
        };
        const response = await apiClient.get<DLQResponse>("/jobs/dlq/jobs", params);
        return {
            ...response,
            items: response.items.map(normalizeJob),
        };
    },

    /**
     * Requeue a single job
     * Backend: POST /jobs/{job_id}/requeue
     */
    async requeueJob(jobId: string, resetAttempts: boolean = true): Promise<Job> {
        const response = await apiClient.post<{ job: Job }>(`/jobs/${jobId}/requeue?reset_attempts=${resetAttempts}`);
        return normalizeJob(response.job || response as unknown as Job);
    },

    /**
     * Bulk requeue multiple jobs
     * Backend: POST /jobs/bulk-requeue
     */
    async bulkRequeueJobs(jobIds: string[]): Promise<{ success: number; failed: number }> {
        return apiClient.post<{ success: number; failed: number }>("/jobs/bulk-requeue", {
            job_ids: jobIds,
            reset_attempts: true,
        });
    },

    /**
     * Acknowledge a DLQ alert
     * Backend: POST /jobs/dlq/alerts/acknowledge
     */
    async acknowledgeDLQAlert(alertId: string, acknowledgedBy: string): Promise<void> {
        return apiClient.post("/jobs/dlq/alerts/acknowledge", {
            alert_id: alertId,
            acknowledged_by: acknowledgedBy,
        });
    },
};

export default jobsApi;
