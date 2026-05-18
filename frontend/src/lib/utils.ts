import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatScore(score: number): string {
  return score.toFixed(1)
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function formatDateTime(date: string): string {
  return new Date(date).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "completed":
      return "text-emerald-400"
    case "running":
      return "text-blue-400"
    case "pending":
      return "text-yellow-400"
    case "failed":
      return "text-red-400"
    default:
      return "text-slate-400"
  }
}

export function getStatusBg(status: string): string {
  switch (status) {
    case "completed":
      return "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
    case "running":
      return "bg-blue-400/10 text-blue-400 border-blue-400/20"
    case "pending":
      return "bg-yellow-400/10 text-yellow-400 border-yellow-400/20"
    case "failed":
      return "bg-red-400/10 text-red-400 border-red-400/20"
    default:
      return "bg-slate-400/10 text-slate-400 border-slate-400/20"
  }
}

export function getScoreColor(score: number): string {
  if (score >= 70) return "text-emerald-400"
  if (score >= 40) return "text-yellow-400"
  return "text-red-400"
}

export const BRAND_COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#06b6d4",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#14b8a6",
]
