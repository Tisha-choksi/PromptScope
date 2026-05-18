import axios from "axios"

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
})

// ─── Brand Types ─────────────────────────────────────────────────────────────

export interface Brand {
  id: number
  name: string
  aliases: string[]
  domain?: string
  description?: string
  is_active: boolean
  created_at: string
}

export interface BrandCreate {
  name: string
  aliases?: string[]
  domain?: string
  description?: string
}

export interface BrandUpdate {
  name?: string
  aliases?: string[]
  domain?: string
  description?: string
  is_active?: boolean
}

// ─── Prompt Types ─────────────────────────────────────────────────────────────

export interface Prompt {
  id: number
  text: string
  category: string
  description?: string
  is_active: boolean
  schedule_cron?: string
  created_at: string
}

export interface PromptCreate {
  text: string
  category: string
  description?: string
  schedule_cron?: string
}

// ─── Job Types ────────────────────────────────────────────────────────────────

export type JobStatus = "pending" | "running" | "completed" | "failed"

export interface MonitoringJob {
  id: number
  prompt_id: number
  status: JobStatus
  providers: string[]
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

// ─── Analytics Types ──────────────────────────────────────────────────────────

export interface TopBrand {
  brand_id: number
  brand_name: string
  visibility_score: number
  mention_count: number
}

export interface DashboardStats {
  total_brands: number
  total_active_prompts: number
  total_jobs_run: number
  avg_visibility_score: number
  top_brands: TopBrand[]
  jobs_last_7_days: number
  available_providers: string[]
}

export interface TrendPoint {
  date: string
  visibility_score: number
  mention_count: number
}

export interface BrandTrend {
  brand_id: number
  brand_name: string
  trend_points: TrendPoint[]
}

export interface ProviderBrandScore {
  brand_id: number
  brand_name: string
  visibility_score: number
  mention_count: number
}

export interface ProviderComparison {
  provider: string
  brands: ProviderBrandScore[]
}

export interface CompetitorEntry {
  brand_id: number
  brand_name: string
  overall_score: number
  provider_scores: Record<string, number>
  mention_count: number
  rank: number
}

// ─── Brand API ────────────────────────────────────────────────────────────────

export const brandsApi = {
  list: () => api.get<Brand[]>("/brands").then((r) => r.data),
  create: (data: BrandCreate) => api.post<Brand>("/brands", data).then((r) => r.data),
  get: (id: number) => api.get<Brand>(`/brands/${id}`).then((r) => r.data),
  update: (id: number, data: BrandUpdate) =>
    api.put<Brand>(`/brands/${id}`, data).then((r) => r.data),
  remove: (id: number) => api.delete(`/brands/${id}`).then((r) => r.data),
}

// ─── Prompts API ──────────────────────────────────────────────────────────────

export const promptsApi = {
  list: () => api.get<Prompt[]>("/prompts").then((r) => r.data),
  create: (data: PromptCreate) => api.post<Prompt>("/prompts", data).then((r) => r.data),
  get: (id: number) => api.get<Prompt>(`/prompts/${id}`).then((r) => r.data),
  run: (id: number) => api.post<MonitoringJob>(`/prompts/${id}/run`).then((r) => r.data),
}

// ─── Jobs API ─────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: (params?: { limit?: number; offset?: number }) =>
    api.get<MonitoringJob[]>("/jobs", { params }).then((r) => r.data),
  get: (id: number) => api.get<MonitoringJob>(`/jobs/${id}`).then((r) => r.data),
}

// ─── Analytics API ────────────────────────────────────────────────────────────

export const analyticsApi = {
  dashboard: () => api.get<DashboardStats>("/analytics/dashboard").then((r) => r.data),
  trends: (brandIds: number[], days: number = 30) =>
    api
      .get<BrandTrend[]>("/analytics/visibility-trends", {
        params: { brand_ids: brandIds.join(","), days },
      })
      .then((r) => r.data),
  providerComparison: () =>
    api.get<ProviderComparison[]>("/analytics/provider-comparison").then((r) => r.data),
  competitorComparison: (brandIds: number[]) =>
    api
      .get<CompetitorEntry[]>("/analytics/competitor-comparison", {
        params: { brand_ids: brandIds.join(",") },
      })
      .then((r) => r.data),
}
