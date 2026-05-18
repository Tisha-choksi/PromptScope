"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { jobsApi, type MonitoringJob } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { formatDateTime, formatDate } from "@/lib/utils"
import {
  Activity,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Cpu,
  AlertTriangle,
} from "lucide-react"

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-400" />
    case "running":
      return <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
    case "pending":
      return <Clock className="h-4 w-4 text-yellow-400" />
    case "failed":
      return <XCircle className="h-4 w-4 text-red-400" />
    default:
      return <Clock className="h-4 w-4 text-slate-400" />
  }
}

function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info" {
  switch (status) {
    case "completed": return "success"
    case "running": return "info"
    case "pending": return "warning"
    case "failed": return "destructive"
    default: return "secondary"
  }
}

function getDuration(job: MonitoringJob): string {
  if (!job.started_at) return "—"
  const end = job.completed_at ? new Date(job.completed_at) : new Date()
  const start = new Date(job.started_at)
  const diffMs = end.getTime() - start.getTime()
  if (diffMs < 1000) return `${diffMs}ms`
  if (diffMs < 60000) return `${(diffMs / 1000).toFixed(1)}s`
  return `${Math.floor(diffMs / 60000)}m ${Math.floor((diffMs % 60000) / 1000)}s`
}

function JobDetailDialog({
  job,
  open,
  onClose,
}: {
  job: MonitoringJob | null
  open: boolean
  onClose: () => void
}) {
  if (!job) return null

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <StatusIcon status={job.status} />
            Job #{job.id}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-slate-900 border border-slate-700/50 p-3 space-y-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Status</p>
              <Badge variant={getStatusVariant(job.status)} className="capitalize">
                {job.status}
              </Badge>
            </div>
            <div className="rounded-lg bg-slate-900 border border-slate-700/50 p-3 space-y-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Duration</p>
              <p className="text-sm font-medium text-slate-300">{getDuration(job)}</p>
            </div>
            <div className="rounded-lg bg-slate-900 border border-slate-700/50 p-3 space-y-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Prompt ID</p>
              <p className="text-sm font-medium text-slate-300">#{job.prompt_id}</p>
            </div>
            <div className="rounded-lg bg-slate-900 border border-slate-700/50 p-3 space-y-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Created</p>
              <p className="text-sm font-medium text-slate-300">{formatDate(job.created_at)}</p>
            </div>
          </div>

          {job.providers?.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Providers</p>
              <div className="flex flex-wrap gap-1.5">
                {job.providers.map((p) => (
                  <div
                    key={p}
                    className="flex items-center gap-1.5 rounded-md border border-slate-600/50 bg-slate-700/50 px-2 py-1 text-xs text-slate-300"
                  >
                    <Cpu className="h-3 w-3 text-slate-400" />
                    {p}
                  </div>
                ))}
              </div>
            </div>
          )}

          {job.started_at && (
            <div className="space-y-1.5">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">Timeline</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Started</span>
                  <span className="text-slate-300">{formatDateTime(job.started_at)}</span>
                </div>
                {job.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Completed</span>
                    <span className="text-slate-300">{formatDateTime(job.completed_at)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {job.error_message && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 space-y-1">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
                <p className="text-xs font-medium text-red-400 uppercase tracking-wider">Error</p>
              </div>
              <p className="text-sm text-red-300 mt-1">{job.error_message}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default function JobsPage() {
  const [selectedJob, setSelectedJob] = useState<MonitoringJob | null>(null)

  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => jobsApi.list(),
    refetchInterval: 5000, // auto-refresh every 5s for running jobs
  })

  const hasRunningJobs = jobs?.some((j) => j.status === "running" || j.status === "pending")

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertCircle className="h-7 w-7 text-red-400" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium">Failed to load jobs</p>
          <p className="text-slate-500 text-sm mt-1">Make sure the backend is running</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Jobs
            {hasRunningJobs && (
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
            )}
          </h1>
          <p className="text-slate-400 mt-1">
            Monitoring job history and status
          </p>
        </div>
        {hasRunningJobs && (
          <div className="flex items-center gap-2 rounded-lg bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 text-sm text-blue-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Auto-refreshing
          </div>
        )}
      </div>

      {/* Status summary chips */}
      {!isLoading && jobs && jobs.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {(["completed", "running", "pending", "failed"] as const).map((status) => {
            const count = jobs.filter((j) => j.status === status).length
            if (count === 0) return null
            return (
              <div
                key={status}
                className="flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-800/50 px-3 py-1.5"
              >
                <StatusIcon status={status} />
                <span className="text-sm text-slate-300 font-medium">{count}</span>
                <span className="text-sm text-slate-500 capitalize">{status}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Jobs Table */}
      <Card>
        <CardHeader className="pb-0">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-400" />
            <CardTitle className="text-base">
              {isLoading
                ? "Loading..."
                : `${jobs?.length ?? 0} Job${(jobs?.length ?? 0) !== 1 ? "s" : ""}`}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0 mt-4">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4">
                  <div className="h-5 w-12 bg-slate-700 rounded-md" />
                  <div className="h-4 flex-1 bg-slate-700 rounded" />
                  <div className="h-4 w-24 bg-slate-700 rounded" />
                  <div className="h-4 w-16 bg-slate-700 rounded" />
                </div>
              ))}
            </div>
          ) : !jobs?.length ? (
            <div className="py-16 text-center space-y-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-700/50 border border-slate-600/50 mx-auto">
                <Activity className="h-6 w-6 text-slate-500" />
              </div>
              <div>
                <p className="text-slate-400 font-medium">No jobs yet</p>
                <p className="text-slate-600 text-sm mt-0.5">
                  Run a prompt to create your first monitoring job
                </p>
              </div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Job ID</TableHead>
                  <TableHead>Prompt</TableHead>
                  <TableHead>Providers</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow
                    key={job.id}
                    className="cursor-pointer"
                    onClick={() => setSelectedJob(job)}
                  >
                    <TableCell>
                      <Badge variant={getStatusVariant(job.status)} className="capitalize gap-1.5">
                        <StatusIcon status={job.status} />
                        {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-slate-400 text-sm">
                      #{job.id}
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm">
                      Prompt #{job.prompt_id}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {job.providers?.slice(0, 3).map((p) => (
                          <span
                            key={p}
                            className="inline-flex items-center gap-1 rounded border border-slate-600/50 bg-slate-700/50 px-1.5 py-0.5 text-xs text-slate-400"
                          >
                            <Cpu className="h-2.5 w-2.5" />
                            {p}
                          </span>
                        ))}
                        {(job.providers?.length ?? 0) > 3 && (
                          <span className="text-xs text-slate-600">
                            +{job.providers.length - 3}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm font-mono">
                      {getDuration(job)}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDateTime(job.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <JobDetailDialog
        job={selectedJob}
        open={!!selectedJob}
        onClose={() => setSelectedJob(null)}
      />
    </div>
  )
}
