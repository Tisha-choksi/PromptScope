"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { promptsApi, type Prompt } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PromptForm } from "@/components/prompts/prompt-form"
import { formatDate } from "@/lib/utils"
import {
  MessageSquare,
  Play,
  AlertCircle,
  Loader2,
  Clock,
  CheckCircle2,
} from "lucide-react"

const CATEGORY_LABELS: Record<string, string> = {
  product_recommendation: "Product Rec.",
  brand_awareness: "Brand Awareness",
  competitor_analysis: "Competitor",
  customer_support: "Support",
  market_research: "Market Research",
  general: "General",
}

const CATEGORY_VARIANTS: Record<string, "default" | "info" | "warning" | "success" | "secondary"> = {
  product_recommendation: "default",
  brand_awareness: "info",
  competitor_analysis: "warning",
  customer_support: "success",
  market_research: "secondary",
  general: "secondary",
}

function RunButton({ prompt }: { prompt: Prompt }) {
  const [justRan, setJustRan] = useState(false)
  const queryClient = useQueryClient()

  const runMutation = useMutation({
    mutationFn: () => promptsApi.run(prompt.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
      setJustRan(true)
      setTimeout(() => setJustRan(false), 3000)
    },
  })

  if (justRan) {
    return (
      <Button variant="ghost" size="sm" className="text-emerald-400 hover:text-emerald-300 gap-1.5" disabled>
        <CheckCircle2 className="h-3.5 w-3.5" />
        Queued
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      className="gap-1.5 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
      onClick={() => runMutation.mutate()}
      disabled={runMutation.isPending}
    >
      {runMutation.isPending ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <Play className="h-3.5 w-3.5" />
      )}
      Run Now
    </Button>
  )
}

export default function PromptsPage() {
  const { data: prompts, isLoading, error } = useQuery({
    queryKey: ["prompts"],
    queryFn: promptsApi.list,
  })

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertCircle className="h-7 w-7 text-red-400" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium">Failed to load prompts</p>
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
          <h1 className="text-2xl font-bold text-slate-100">Prompts</h1>
          <p className="text-slate-400 mt-1">
            Manage monitoring prompts sent to AI providers
          </p>
        </div>
        <PromptForm />
      </div>

      {/* Prompts Table */}
      <Card>
        <CardHeader className="pb-0">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-indigo-400" />
            <CardTitle className="text-base">
              {isLoading
                ? "Loading..."
                : `${prompts?.length ?? 0} Prompt${(prompts?.length ?? 0) !== 1 ? "s" : ""}`}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0 mt-4">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4">
                  <div className="h-4 flex-1 bg-slate-700 rounded" />
                  <div className="h-5 w-28 bg-slate-700 rounded-md" />
                  <div className="h-5 w-16 bg-slate-700 rounded-md" />
                  <div className="h-8 w-20 bg-slate-700 rounded" />
                </div>
              ))}
            </div>
          ) : !prompts?.length ? (
            <div className="py-16 text-center space-y-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-700/50 border border-slate-600/50 mx-auto">
                <MessageSquare className="h-6 w-6 text-slate-500" />
              </div>
              <div>
                <p className="text-slate-400 font-medium">No prompts yet</p>
                <p className="text-slate-600 text-sm mt-0.5">
                  Add your first prompt to start monitoring
                </p>
              </div>
              <PromptForm />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Prompt</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {prompts.map((prompt) => (
                  <TableRow key={prompt.id}>
                    <TableCell className="max-w-sm">
                      <p className="text-slate-200 font-medium line-clamp-2 text-sm leading-relaxed">
                        {prompt.text}
                      </p>
                      {prompt.description && (
                        <p className="text-slate-500 text-xs mt-1 line-clamp-1">
                          {prompt.description}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={CATEGORY_VARIANTS[prompt.category] ?? "secondary"}>
                        {CATEGORY_LABELS[prompt.category] ?? prompt.category}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {prompt.schedule_cron ? (
                        <div className="flex items-center gap-1.5 text-slate-400 text-xs">
                          <Clock className="h-3 w-3 shrink-0" />
                          <span className="font-mono">{prompt.schedule_cron}</span>
                        </div>
                      ) : (
                        <span className="text-slate-600 text-sm">Manual only</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={prompt.is_active ? "success" : "secondary"}>
                        {prompt.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(prompt.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <RunButton prompt={prompt} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
