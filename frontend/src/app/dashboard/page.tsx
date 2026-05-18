"use client"

import { useQuery } from "@tanstack/react-query"
import {
  Building2,
  MessageSquare,
  Activity,
  TrendingUp,
  Clock,
  Cpu,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { analyticsApi, jobsApi } from "@/lib/api"
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
import { formatDate, formatScore, getScoreColor, getStatusBg } from "@/lib/utils"

function StatCard({
  title,
  value,
  icon: Icon,
  description,
  valueClassName,
}: {
  title: string
  value: string | number
  icon: React.ElementType
  description?: string
  valueClassName?: string
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-slate-400">{title}</p>
            <p className={`text-3xl font-bold tracking-tight ${valueClassName ?? "text-slate-100"}`}>
              {value}
            </p>
            {description && (
              <p className="text-xs text-slate-500">{description}</p>
            )}
          </div>
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-600/10 border border-indigo-600/20">
            <Icon className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function getRankBadge(rank: number) {
  if (rank === 1) return "bg-yellow-400/10 text-yellow-300 border-yellow-400/30"
  if (rank === 2) return "bg-slate-400/10 text-slate-300 border-slate-400/30"
  if (rank === 3) return "bg-amber-700/20 text-amber-500 border-amber-700/30"
  return "bg-slate-700/50 text-slate-400 border-slate-600/30"
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

export default function DashboardPage() {
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsApi.dashboard,
  })

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs", { limit: 5 }],
    queryFn: () => jobsApi.list({ limit: 5 }),
  })

  if (statsError) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertCircle className="h-7 w-7 text-red-400" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium">Failed to load dashboard</p>
          <p className="text-slate-500 text-sm mt-1">Make sure the backend is running at localhost:8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 mt-1">
          AI visibility monitoring overview
        </p>
      </div>

      {/* Stats Cards */}
      {statsLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 w-24 bg-slate-700 rounded" />
                  <div className="h-8 w-16 bg-slate-700 rounded" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            title="Total Brands"
            value={stats?.total_brands ?? 0}
            icon={Building2}
            description="Monitored brands"
          />
          <StatCard
            title="Active Prompts"
            value={stats?.total_active_prompts ?? 0}
            icon={MessageSquare}
            description="Running prompts"
          />
          <StatCard
            title="Jobs Run"
            value={stats?.total_jobs_run ?? 0}
            icon={Activity}
            description={`${stats?.jobs_last_7_days ?? 0} in last 7 days`}
          />
          <StatCard
            title="Avg Visibility"
            value={`${formatScore(stats?.avg_visibility_score ?? 0)}%`}
            icon={TrendingUp}
            description="Across all brands"
            valueClassName={getScoreColor(stats?.avg_visibility_score ?? 0)}
          />
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Top Brands Leaderboard */}
        <Card className="xl:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-indigo-400" />
              Top Brands by Visibility
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {statsLoading ? (
              <div className="p-6 space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="animate-pulse flex items-center gap-4">
                    <div className="h-6 w-6 bg-slate-700 rounded" />
                    <div className="h-4 flex-1 bg-slate-700 rounded" />
                    <div className="h-4 w-16 bg-slate-700 rounded" />
                  </div>
                ))}
              </div>
            ) : !stats?.top_brands?.length ? (
              <div className="p-6 text-center text-slate-500 text-sm">
                No brand data yet. Add brands and run prompts to see results.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Rank</TableHead>
                    <TableHead>Brand</TableHead>
                    <TableHead className="text-right">Visibility Score</TableHead>
                    <TableHead className="text-right">Mentions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.top_brands.map((brand, index) => (
                    <TableRow key={brand.brand_id}>
                      <TableCell>
                        <span
                          className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-bold border ${getRankBadge(index + 1)}`}
                        >
                          {index + 1}
                        </span>
                      </TableCell>
                      <TableCell className="font-medium text-slate-200">
                        {brand.brand_name}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={`font-semibold ${getScoreColor(brand.visibility_score)}`}>
                          {formatScore(brand.visibility_score)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-slate-400">
                        {brand.mention_count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Provider Availability */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Cpu className="h-4 w-4 text-indigo-400" />
                Available Providers
              </CardTitle>
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div className="flex flex-wrap gap-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="animate-pulse h-7 w-20 bg-slate-700 rounded-md" />
                  ))}
                </div>
              ) : !stats?.available_providers?.length ? (
                <p className="text-sm text-slate-500">No providers configured</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {stats.available_providers.map((provider) => (
                    <div
                      key={provider}
                      className="flex items-center gap-1.5 rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                      {provider}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Jobs */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4 text-indigo-400" />
                Recent Jobs
              </CardTitle>
            </CardHeader>
            <CardContent>
              {jobsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="animate-pulse flex items-center justify-between">
                      <div className="h-4 w-24 bg-slate-700 rounded" />
                      <div className="h-5 w-16 bg-slate-700 rounded-md" />
                    </div>
                  ))}
                </div>
              ) : !jobs?.length ? (
                <p className="text-sm text-slate-500">No jobs run yet</p>
              ) : (
                <div className="space-y-2.5">
                  {jobs.slice(0, 5).map((job) => (
                    <div
                      key={job.id}
                      className="flex items-center justify-between gap-2"
                    >
                      <div className="min-w-0">
                        <p className="text-xs text-slate-400 truncate">
                          Job #{job.id} · Prompt #{job.prompt_id}
                        </p>
                        <p className="text-xs text-slate-600 mt-0.5">
                          {formatDate(job.created_at)}
                        </p>
                      </div>
                      <Badge variant={getStatusVariant(job.status)} className="shrink-0 text-xs">
                        {job.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
