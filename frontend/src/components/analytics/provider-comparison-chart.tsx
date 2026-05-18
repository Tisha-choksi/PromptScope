"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { type ProviderComparison } from "@/lib/api"
import { BRAND_COLORS } from "@/lib/utils"

interface ProviderComparisonChartProps {
  data: ProviderComparison[]
}

interface ChartDataPoint {
  provider: string
  [brandName: string]: string | number
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; fill: string }>
  label?: string
}) => {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2.5 shadow-2xl min-w-[160px]">
      <p className="text-xs font-semibold text-slate-300 mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-sm shrink-0"
              style={{ backgroundColor: entry.fill }}
            />
            <span className="text-slate-400 truncate max-w-[120px]">{entry.name}</span>
          </div>
          <span className="font-semibold text-slate-100">{entry.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

export function ProviderComparisonChart({ data }: ProviderComparisonChartProps) {
  if (!data?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        No provider comparison data available
      </div>
    )
  }

  // Get all unique brand names
  const allBrands = Array.from(
    new Set(data.flatMap((d) => d.brands.map((b) => b.brand_name)))
  )

  // Pivot: provider → { brandName: score }
  const chartData: ChartDataPoint[] = data.map((providerData) => {
    const point: ChartDataPoint = { provider: providerData.provider }
    providerData.brands.forEach((brand) => {
      point[brand.brand_name] = brand.visibility_score
    })
    return point
  })

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis
          dataKey="provider"
          tick={{ fill: "#64748b", fontSize: 12 }}
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
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Legend
          wrapperStyle={{ paddingTop: "16px" }}
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: "12px" }}>{value}</span>
          )}
        />
        {allBrands.map((brandName, index) => (
          <Bar
            key={brandName}
            dataKey={brandName}
            fill={BRAND_COLORS[index % BRAND_COLORS.length]}
            radius={[3, 3, 0, 0]}
            maxBarSize={40}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
