"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { promptsApi, type PromptCreate } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Plus, Loader2 } from "lucide-react"

const CATEGORIES = [
  { value: "product_recommendation", label: "Product Recommendation" },
  { value: "brand_awareness", label: "Brand Awareness" },
  { value: "competitor_analysis", label: "Competitor Analysis" },
  { value: "customer_support", label: "Customer Support" },
  { value: "market_research", label: "Market Research" },
  { value: "general", label: "General" },
]

interface PromptFormProps {
  trigger?: React.ReactNode
  onSuccess?: () => void
}

export function PromptForm({ trigger, onSuccess }: PromptFormProps) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState("")
  const [category, setCategory] = useState("")
  const [description, setDescription] = useState("")
  const [scheduleCron, setScheduleCron] = useState("")
  const [errors, setErrors] = useState<Record<string, string>>({})

  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data: PromptCreate) => promptsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      handleClose()
      onSuccess?.()
    },
  })

  function handleClose() {
    setOpen(false)
    setText("")
    setCategory("")
    setDescription("")
    setScheduleCron("")
    setErrors({})
    createMutation.reset()
  }

  function validate() {
    const newErrors: Record<string, string> = {}
    if (!text.trim()) newErrors.text = "Prompt text is required"
    if (!category) newErrors.category = "Category is required"
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    const data: PromptCreate = {
      text: text.trim(),
      category,
      description: description.trim() || undefined,
      schedule_cron: scheduleCron.trim() || undefined,
    }

    createMutation.mutate(data)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); else setOpen(true) }}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <Plus className="h-4 w-4" />
            Add Prompt
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Add Prompt</DialogTitle>
          <DialogDescription>
            Create a new monitoring prompt to track brand visibility.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="prompt-text">
              Prompt Text <span className="text-red-400">*</span>
            </label>
            <textarea
              id="prompt-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. What are the best project management tools available?"
              rows={4}
              className={`flex w-full rounded-lg border bg-slate-900 px-3 py-2 text-sm text-slate-100 shadow-sm transition-colors placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 resize-none ${
                errors.text ? "border-red-500 focus-visible:ring-red-500" : "border-slate-600"
              }`}
            />
            {errors.text && (
              <p className="text-xs text-red-400">{errors.text}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="prompt-category">
              Category <span className="text-red-400">*</span>
            </label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger
                id="prompt-category"
                className={errors.category ? "border-red-500 focus:ring-red-500" : ""}
              >
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.category && (
              <p className="text-xs text-red-400">{errors.category}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="prompt-description">
              Description
              <span className="ml-1 text-xs text-slate-500">(optional)</span>
            </label>
            <Input
              id="prompt-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Internal description of this prompt's purpose"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="prompt-cron">
              Schedule (Cron)
              <span className="ml-1 text-xs text-slate-500">(optional)</span>
            </label>
            <Input
              id="prompt-cron"
              value={scheduleCron}
              onChange={(e) => setScheduleCron(e.target.value)}
              placeholder="e.g. 0 9 * * * (daily at 9am)"
              className="font-mono text-xs"
            />
            <p className="text-xs text-slate-600">
              Leave empty to run manually only
            </p>
          </div>

          {createMutation.error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {(createMutation.error as Error).message || "Something went wrong"}
            </p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={createMutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Add Prompt
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
