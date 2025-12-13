"use client"

import { useState, useEffect, useCallback } from "react"
import { Cog, RefreshCw, Clock, AlertTriangle, Users, Layers } from "lucide-react"
import { ConfigFormWrapper } from "@/components/admin/config"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { configApi, type JobQueueConfig } from "@/lib/api/admin"

const defaultConfig: JobQueueConfig = {
    max_job_retries: 3,
    retry_backoff_multiplier: 2.0,
    retry_initial_delay_seconds: 5,
    retry_max_delay_seconds: 300,
    job_timeout_minutes: 60,
    dlq_alert_threshold: 10,
    worker_heartbeat_interval_seconds: 30,
    worker_unhealthy_threshold_seconds: 60,
    max_jobs_per_worker: 5,
    queue_priority_levels: 3,
}

export default function JobConfigPage() {
    const [config, setConfig] = useState<JobQueueConfig>(defaultConfig)
    const [originalConfig, setOriginalConfig] = useState<JobQueueConfig>(defaultConfig)
    const [isLoading, setIsLoading] = useState(true)

    const isDirty = JSON.stringify(config) !== JSON.stringify(originalConfig)

    const fetchConfig = useCallback(async () => {
        try {
            const data = await configApi.getJobQueueConfig()
            setConfig(data)
            setOriginalConfig(data)
        } catch (error) {
            console.error("Failed to fetch job queue config:", error)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchConfig()
    }, [fetchConfig])

    const handleSave = async () => {
        await configApi.updateJobQueueConfig(config)
        setOriginalConfig(config)
    }

    const handleReset = () => {
        setConfig(originalConfig)
    }

    const updateConfig = <K extends keyof JobQueueConfig>(key: K, value: JobQueueConfig[K]) => {
        setConfig((prev) => ({ ...prev, [key]: value }))
    }

    const formatDuration = (seconds: number): string => {
        if (seconds < 60) return `${seconds} seconds`
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`
        return `${Math.floor(seconds / 3600)} hours`
    }

    const calculateMaxDelay = (): string => {
        const { retry_initial_delay_seconds, retry_backoff_multiplier, max_job_retries, retry_max_delay_seconds } = config
        let delay = retry_initial_delay_seconds
        let totalDelay = 0
        for (let i = 0; i < max_job_retries; i++) {
            const actualDelay = Math.min(delay, retry_max_delay_seconds)
            totalDelay += actualDelay
            delay = delay * retry_backoff_multiplier
        }
        return formatDuration(totalDelay)
    }

    return (
        <ConfigFormWrapper
            title="Job Queue Configuration"
            description="Configure job queue retry behavior, timeouts, and worker settings."
            icon={<Cog className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
            onSave={handleSave}
            onReset={handleReset}
            isDirty={isDirty}
            isLoading={isLoading}
        >
            <div className="space-y-8">
                {/* Retry Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <RefreshCw className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Retry Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">
                        Configure how failed jobs are retried with exponential backoff.
                    </p>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_job_retries">Max Retry Attempts</Label>
                                <Input
                                    id="max_job_retries"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.max_job_retries}
                                    onChange={(e) => updateConfig("max_job_retries", parseInt(e.target.value) || 3)}
                                />
                                <p className="text-xs text-slate-500">1-10 attempts before moving to DLQ</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="retry_backoff_multiplier">Backoff Multiplier</Label>
                                <Input
                                    id="retry_backoff_multiplier"
                                    type="number"
                                    min={1.0}
                                    max={5.0}
                                    step={0.1}
                                    value={config.retry_backoff_multiplier}
                                    onChange={(e) => updateConfig("retry_backoff_multiplier", parseFloat(e.target.value) || 2.0)}
                                />
                                <p className="text-xs text-slate-500">1.0-5.0x delay increase per retry</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="retry_initial_delay_seconds">Initial Retry Delay</Label>
                                <Input
                                    id="retry_initial_delay_seconds"
                                    type="number"
                                    min={1}
                                    max={60}
                                    value={config.retry_initial_delay_seconds}
                                    onChange={(e) => updateConfig("retry_initial_delay_seconds", parseInt(e.target.value) || 5)}
                                />
                                <p className="text-xs text-slate-500">{formatDuration(config.retry_initial_delay_seconds)} (1-60 seconds)</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="retry_max_delay_seconds">Max Retry Delay</Label>
                                <Input
                                    id="retry_max_delay_seconds"
                                    type="number"
                                    min={60}
                                    max={3600}
                                    value={config.retry_max_delay_seconds}
                                    onChange={(e) => updateConfig("retry_max_delay_seconds", parseInt(e.target.value) || 300)}
                                />
                                <p className="text-xs text-slate-500">{formatDuration(config.retry_max_delay_seconds)} (60-3600 seconds)</p>
                            </div>
                        </div>
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/50">
                            <div className="flex items-start gap-2">
                                <RefreshCw className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Retry Behavior</p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                        Failed jobs will be retried up to {config.max_job_retries} times with exponential backoff.
                                        Starting at {formatDuration(config.retry_initial_delay_seconds)}, delays increase by {config.retry_backoff_multiplier}x
                                        up to a maximum of {formatDuration(config.retry_max_delay_seconds)}.
                                        Total retry time: ~{calculateMaxDelay()}.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Timeout Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Clock className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Timeout Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">Configure job execution timeouts and heartbeat intervals.</p>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="job_timeout_minutes">Job Timeout</Label>
                                <Input
                                    id="job_timeout_minutes"
                                    type="number"
                                    min={1}
                                    max={1440}
                                    value={config.job_timeout_minutes}
                                    onChange={(e) => updateConfig("job_timeout_minutes", parseInt(e.target.value) || 60)}
                                />
                                <p className="text-xs text-slate-500">{config.job_timeout_minutes} minutes (1-1440 minutes / 24 hours)</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="worker_heartbeat_interval_seconds">Worker Heartbeat Interval</Label>
                                <Input
                                    id="worker_heartbeat_interval_seconds"
                                    type="number"
                                    min={10}
                                    max={120}
                                    value={config.worker_heartbeat_interval_seconds}
                                    onChange={(e) => updateConfig("worker_heartbeat_interval_seconds", parseInt(e.target.value) || 30)}
                                />
                                <p className="text-xs text-slate-500">{formatDuration(config.worker_heartbeat_interval_seconds)} (10-120 seconds)</p>
                            </div>
                        </div>
                        <div className="space-y-2 max-w-md">
                            <Label htmlFor="worker_unhealthy_threshold_seconds">Worker Unhealthy Threshold</Label>
                            <Input
                                id="worker_unhealthy_threshold_seconds"
                                type="number"
                                min={30}
                                max={300}
                                value={config.worker_unhealthy_threshold_seconds}
                                onChange={(e) => updateConfig("worker_unhealthy_threshold_seconds", parseInt(e.target.value) || 60)}
                            />
                            <p className="text-xs text-slate-500">{formatDuration(config.worker_unhealthy_threshold_seconds)} without heartbeat marks worker as unhealthy (30-300 seconds)</p>
                        </div>
                        <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                Jobs running longer than {config.job_timeout_minutes} minutes will be terminated and marked as failed.
                                Workers must send heartbeats every {formatDuration(config.worker_heartbeat_interval_seconds)} or they will be
                                marked unhealthy after {formatDuration(config.worker_unhealthy_threshold_seconds)}.
                            </p>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Worker Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Users className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Worker Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">Configure worker capacity and job distribution.</p>
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="max_jobs_per_worker">Max Jobs Per Worker</Label>
                                <Input
                                    id="max_jobs_per_worker"
                                    type="number"
                                    min={1}
                                    max={20}
                                    value={config.max_jobs_per_worker}
                                    onChange={(e) => updateConfig("max_jobs_per_worker", parseInt(e.target.value) || 5)}
                                />
                                <p className="text-xs text-slate-500">1-20 concurrent jobs per worker</p>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="queue_priority_levels">Queue Priority Levels</Label>
                                <Input
                                    id="queue_priority_levels"
                                    type="number"
                                    min={1}
                                    max={10}
                                    value={config.queue_priority_levels}
                                    onChange={(e) => updateConfig("queue_priority_levels", parseInt(e.target.value) || 3)}
                                />
                                <p className="text-xs text-slate-500">1-10 priority levels (higher = more urgent)</p>
                            </div>
                        </div>
                        <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                            <p className="text-sm text-slate-600 dark:text-slate-400">
                                Each worker can process up to {config.max_jobs_per_worker} jobs concurrently.
                                Jobs are organized into {config.queue_priority_levels} priority levels, with higher priority jobs processed first.
                            </p>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* DLQ Settings */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Dead Letter Queue (DLQ) Settings</h3>
                    </div>
                    <p className="text-sm text-slate-500 mb-4">Configure alerts for failed jobs that have exhausted all retry attempts.</p>
                    <div className="space-y-4">
                        <div className="space-y-2 max-w-md">
                            <Label htmlFor="dlq_alert_threshold">DLQ Alert Threshold</Label>
                            <Input
                                id="dlq_alert_threshold"
                                type="number"
                                min={1}
                                max={100}
                                value={config.dlq_alert_threshold}
                                onChange={(e) => updateConfig("dlq_alert_threshold", parseInt(e.target.value) || 10)}
                            />
                            <p className="text-xs text-slate-500">Alert when DLQ contains {config.dlq_alert_threshold}+ jobs (1-100)</p>
                        </div>
                        <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50">
                            <div className="flex items-start gap-2">
                                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-amber-900 dark:text-amber-100">Dead Letter Queue</p>
                                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                                        Jobs that fail after {config.max_job_retries} retry attempts are moved to the Dead Letter Queue (DLQ).
                                        An alert will be triggered when the DLQ contains {config.dlq_alert_threshold} or more jobs.
                                        DLQ jobs require manual investigation and can be retried or discarded from the System Monitoring page.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <Separator />

                {/* Summary */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <Layers className="h-4 w-4 text-slate-500" />
                        <h3 className="font-medium text-slate-900 dark:text-white">Configuration Summary</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <p className="text-xs text-slate-500 uppercase tracking-wide">Retry Policy</p>
                            <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">{config.max_job_retries} retries</p>
                            <p className="text-xs text-slate-500 mt-1">{config.retry_backoff_multiplier}x backoff</p>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <p className="text-xs text-slate-500 uppercase tracking-wide">Job Timeout</p>
                            <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">{config.job_timeout_minutes} min</p>
                            <p className="text-xs text-slate-500 mt-1">Max execution time</p>
                        </div>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <p className="text-xs text-slate-500 uppercase tracking-wide">Worker Capacity</p>
                            <p className="text-lg font-semibold text-slate-900 dark:text-white mt-1">{config.max_jobs_per_worker} jobs</p>
                            <p className="text-xs text-slate-500 mt-1">Per worker concurrent</p>
                        </div>
                    </div>
                </div>
            </div>
        </ConfigFormWrapper>
    )
}
