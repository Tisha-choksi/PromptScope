"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { type BrandTrend, type Brand } from "@/lib/api"
import { BRAND_COLORS } from "@/lib/utils"

interface VisibilityChartProps {
  data: BrandTrend[]
  brands: Brand[]
}

interface ChartDataPoint {
  date: string
  [brandName: string]: string | number
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) => {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2.5 shadow-2xl min-w-[160px]">
      <p className="text-xs text-slate-400 mb-2 font-medium">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-300 truncate max-w-[120px]">{entry.name}</span>
          </div>
          <span className="font-semibold text-slate-100">{entry.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

export function VisibilityChart({ data, brands }: VisibilityChartProps) {
  if (!data?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        No trend data available
      </div>
    )
  }

  // Pivot: date → { brandName: score }
  const dateMap = new Map<string, ChartDataPoint>()

  data.forEach((brandTrend) => {
    brandTrend.trend_points.forEach((point) => {
      const existing = dateMap.get(point.date) ?? { date: formatDateLabel(point.date) }
      existing[brandTrend.brand_name] = point.visibility_score
      dateMap.set(point.date, existing)
    })
  })

  const chartData = Array.from(dateMap.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date))
  )

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={{ stroke: "#334155" }}
          tickLine={false}
          dy={8}
        />
        <YAxis
          tick={{ fill: "#64748b", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
          domain={[0, 100]}
          width={44}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ paddingTop: "16px" }}
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: "12px" }}>{value}</span>
          )}
        />
        {data.map((brandTrend, index) => (
          <Line
            key={brandTrend.brand_id}
            type="monotone"
            dataKey={brandTrend.brand_name}
            stroke={BRAND_COLORS[index % BRAND_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, strokeWidth: 0 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
