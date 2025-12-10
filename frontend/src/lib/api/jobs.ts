import { apiClient } from "./client";

// Types
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
    type: JobType;
    payload: Record<string, unknown>;
    priority: number;
    attempts: number;
    max_attempts: number;
    status: JobStatus;
    result?: Record<string, unknown>;
    error?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    progress?: number;
}

export interface JobsResponse {
    items: Job[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
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
    type?: JobType;
    page?: number;
    page_size?: number;
}

// API functions
export const jobsApi = {
    async getJobs(filters?: JobFilters): Promise<JobsResponse> {
        const params: Record<string, string | number | boolean | undefined> = {
            status: filters?.status,
            type: filters?.type,
            page: filters?.page,
            page_size: filters?.page_size,
        };
        return apiClient.get<JobsResponse>("/jobs", params);
    },

    async getJob(jobId: string): Promise<Job> {
        return apiClient.get<Job>(`/jobs/${jobId}`);
    },

    async getQueueStats(): Promise<QueueStats> {
        return apiClient.get<QueueStats>("/jobs/stats");
    },

    async getDLQJobs(page?: number, pageSize?: number): Promise<JobsResponse> {
        return apiClient.get<JobsResponse>("/jobs/dlq", { page, page_size: pageSize });
    },

    async requeueJob(jobId: string): Promise<Job> {
        return apiClient.post<Job>(`/jobs/${jobId}/requeue`);
    },

    async bulkRequeueJobs(jobIds: string[]): Promise<{ success: number; failed: number }> {
        return apiClient.post<{ success: number; failed: number }>("/jobs/bulk-requeue", { job_ids: jobIds });
    },

    async cancelJob(jobId: string): Promise<void> {
        return apiClient.post<void>(`/jobs/${jobId}/cancel`);
    },
};

export default jobsApi;
