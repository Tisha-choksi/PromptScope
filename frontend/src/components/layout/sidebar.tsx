"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Building2,
  MessageSquare,
  Activity,
  BarChart3,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    href: "/brands",
    label: "Brands",
    icon: Building2,
  },
  {
    href: "/prompts",
    label: "Prompts",
    icon: MessageSquare,
  },
  {
    href: "/jobs",
    label: "Jobs",
    icon: Activity,
  },
  {
    href: "/analytics",
    label: "Analytics",
    icon: BarChart3,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-slate-900 border-r border-slate-700/50 flex flex-col z-40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-700/50">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <span className="font-semibold text-base bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">
          PromptScope
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-3 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
          Main Menu
        </p>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/")

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/20"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0",
                  isActive ? "text-indigo-400" : "text-slate-500"
                )}
              />
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-slate-700/50">
        <p className="text-xs text-slate-600">AI Visibility Monitoring</p>
        <p className="text-xs text-slate-700 mt-0.5">v1.0.0</p>
      </div>
    </aside>
  )
}
