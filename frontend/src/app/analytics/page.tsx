"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { analyticsApi, brandsApi, type Brand, type CompetitorEntry } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { VisibilityChart } from "@/components/analytics/visibility-chart"
import { ProviderComparisonChart } from "@/components/analytics/provider-comparison-chart"
import { formatScore, getScoreColor, BRAND_COLORS } from "@/lib/utils"
import {
  TrendingUp,
  BarChart3,
  Swords,
  AlertCircle,
  Loader2,
  CheckSquare,
  Square,
  Calendar,
  Trophy,
} from "lucide-react"

const DAY_OPTIONS = [
  { label: "7 days", value: 7 },
  { label: "30 days", value: 30 },
  { label: "90 days", value: 90 },
]

function BrandCheckbox({
  brand,
  checked,
  color,
  onChange,
}: {
  brand: Brand
  checked: boolean
  color: string
  onChange: (checked: boolean) => void
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-all ${
        checked
          ? "border-indigo-500/40 bg-indigo-500/10 text-slate-200"
          : "border-slate-700/50 bg-slate-800/50 text-slate-500 hover:border-slate-600 hover:text-slate-400"
      }`}
    >
      {checked ? (
        <CheckSquare className="h-4 w-4 shrink-0" style={{ color }} />
      ) : (
        <Square className="h-4 w-4 shrink-0 text-slate-600" />
      )}
      <span className="truncate max-w-[120px]">{brand.name}</span>
    </button>
  )
}

function getRankDisplay(rank: number) {
  if (rank === 1) return { label: "1st", className: "text-yellow-400 font-bold" }
  if (rank === 2) return { label: "2nd", className: "text-slate-300 font-bold" }
  if (rank === 3) return { label: "3rd", className: "text-amber-600 font-bold" }
  return { label: `${rank}th`, className: "text-slate-500" }
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(30)
  const [selectedBrandIds, setSelectedBrandIds] = useState<number[]>([])

  const { data: brands } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
    select: (data) => {
      // Auto-select all brands on first load
      return data
    },
  })

  // Auto-select all brands when brands load
  const effectiveBrandIds =
    selectedBrandIds.length > 0
      ? selectedBrandIds
      : (brands?.map((b) => b.id) ?? [])

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ["trends", effectiveBrandIds, days],
    queryFn: () => analyticsApi.trends(effectiveBrandIds, days),
    enabled: effectiveBrandIds.length > 0,
  })

  const { data: providerData, isLoading: providerLoading } = useQuery({
    queryKey: ["provider-comparison"],
    queryFn: analyticsApi.providerComparison,
  })

  const { data: competitorData, isLoading: competitorLoading } = useQuery({
    queryKey: ["competitor-comparison", effectiveBrandIds],
    queryFn: () => analyticsApi.competitorComparison(effectiveBrandIds),
    enabled: effectiveBrandIds.length > 0,
  })

  function toggleBrand(id: number) {
    const current = selectedBrandIds.length > 0 ? selectedBrandIds : (brands?.map((b) => b.id) ?? [])
    if (current.includes(id)) {
      setSelectedBrandIds(current.filter((bid) => bid !== id))
    } else {
      setSelectedBrandIds([...current, id])
    }
  }

  return (
    <div className="p-8 space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Analytics</h1>
        <p className="text-slate-400 mt-1">
          Visibility insights across AI providers and time
        </p>
      </div>

      <Tabs defaultValue="trends">
        <TabsList className="mb-2">
          <TabsTrigger value="trends" className="gap-2">
            <TrendingUp className="h-3.5 w-3.5" />
            Visibility Trends
          </TabsTrigger>
          <TabsTrigger value="providers" className="gap-2">
            <BarChart3 className="h-3.5 w-3.5" />
            Provider Comparison
          </TabsTrigger>
          <TabsTrigger value="competitors" className="gap-2">
            <Swords className="h-3.5 w-3.5" />
            Competitor Analysis
          </TabsTrigger>
        </TabsList>

        {/* ─── Tab 1: Visibility Trends ─────────────────────────────────── */}
        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-indigo-400" />
                    Brand Visibility Over Time
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Visibility score percentage per brand
                  </CardDescription>
                </div>

                {/* Date range selector */}
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-500" />
                  <div className="flex rounded-lg border border-slate-700 overflow-hidden">
                    {DAY_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        onClick={() => setDays(opt.value)}
                        className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                          days === opt.value
                            ? "bg-indigo-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-300"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Brand filter */}
              {brands && brands.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {brands.map((brand, index) => (
                    <BrandCheckbox
                      key={brand.id}
                      brand={brand}
                      checked={effectiveBrandIds.includes(brand.id)}
                      color={BRAND_COLORS[index % BRAND_COLORS.length]}
                      onChange={() => toggleBrand(brand.id)}
                    />
                  ))}
                </div>
              )}
            </CardHeader>
            <CardContent>
              {trendsLoading ? (
                <div className="flex items-center justify-center h-64 gap-3 text-slate-500">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading trend data…</span>
                </div>
              ) : !brands?.length ? (
                <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-500">
                  <AlertCircle className="h-8 w-8" />
                  <div className="text-center">
                    <p className="font-medium text-slate-400">No brands configured</p>
                    <p className="text-sm mt-0.5">Add brands to see visibility trends</p>
                  </div>
                </div>
              ) : (
                <VisibilityChart data={trends ?? []} brands={brands ?? []} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Tab 2: Provider Comparison ───────────────────────────────── */}
        <TabsContent value="providers">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-indigo-400" />
                Provider Comparison
              </CardTitle>
              <CardDescription>
                Brand visibility scores grouped by AI provider
              </CardDescription>
            </CardHeader>
            <CardContent>
              {providerLoading ? (
                <div className="flex items-center justify-center h-64 gap-3 text-slate-500">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading provider data…</span>
                </div>
              ) : !providerData?.length ? (
                <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-500">
                  <AlertCircle className="h-8 w-8" />
                  <div className="text-center">
                    <p className="font-medium text-slate-400">No provider data yet</p>
                    <p className="text-sm mt-0.5">Run some prompts to see provider comparison</p>
                  </div>
                </div>
              ) : (
                <ProviderComparisonChart data={providerData} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Tab 3: Competitor Analysis ───────────────────────────────── */}
        <TabsContent value="competitors">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Swords className="h-4 w-4 text-indigo-400" />
                Competitor Analysis
              </CardTitle>
              <CardDescription>
                Side-by-side brand performance across all AI providers
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {competitorLoading ? (
                <div className="flex items-center justify-center h-64 gap-3 text-slate-500">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm">Loading competitor data…</span>
                </div>
              ) : !competitorData?.length ? (
                <div className="flex flex-col items-center justify-center h-64 gap-3 text-slate-500">
                  <AlertCircle className="h-8 w-8" />
                  <div className="text-center">
                    <p className="font-medium text-slate-400">No competitor data yet</p>
                    <p className="text-sm mt-0.5">Run prompts with multiple brands to compare</p>
                  </div>
                </div>
              ) : (
                <CompetitorTable data={competitorData} />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function CompetitorTable({ data }: { data: CompetitorEntry[] }) {
  // Get all provider columns
  const allProviders = Array.from(
    new Set(data.flatMap((d) => Object.keys(d.provider_scores)))
  ).sort()

  const sorted = [...data].sort((a, b) => a.rank - b.rank)

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">Rank</TableHead>
          <TableHead>Brand</TableHead>
          <TableHead className="text-right">Overall Score</TableHead>
          <TableHead className="text-right">Mentions</TableHead>
          {allProviders.map((provider) => (
            <TableHead key={provider} className="text-right capitalize">
              {provider}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((entry) => {
          const { label, className } = getRankDisplay(entry.rank)
          return (
            <TableRow key={entry.brand_id}>
              <TableCell>
                <div className={`flex items-center gap-1 ${className}`}>
                  {entry.rank <= 3 && <Trophy className="h-3.5 w-3.5" />}
                  {label}
                </div>
              </TableCell>
              <TableCell className="font-medium text-slate-200">
                {entry.brand_name}
              </TableCell>
              <TableCell className="text-right">
                <span className={`font-semibold ${getScoreColor(entry.overall_score)}`}>
                  {formatScore(entry.overall_score)}%
                </span>
              </TableCell>
              <TableCell className="text-right text-slate-400">
                {entry.mention_count}
              </TableCell>
              {allProviders.map((provider) => {
                const score = entry.provider_scores[provider]
                return (
                  <TableCell key={provider} className="text-right">
                    {score != null ? (
                      <span className={`text-sm font-medium ${getScoreColor(score)}`}>
                        {formatScore(score)}%
                      </span>
                    ) : (
                      <span className="text-slate-600 text-sm">—</span>
                    )}
                  </TableCell>
                )
              })}
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}
