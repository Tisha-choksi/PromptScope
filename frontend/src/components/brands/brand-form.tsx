"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { brandsApi, type Brand, type BrandCreate } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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

interface BrandFormProps {
  brand?: Brand
  trigger?: React.ReactNode
  onSuccess?: () => void
}

export function BrandForm({ brand, trigger, onSuccess }: BrandFormProps) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(brand?.name ?? "")
  const [aliases, setAliases] = useState(brand?.aliases?.join(", ") ?? "")
  const [domain, setDomain] = useState(brand?.domain ?? "")
  const [description, setDescription] = useState(brand?.description ?? "")
  const [errors, setErrors] = useState<Record<string, string>>({})

  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data: BrandCreate) => brandsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brands"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      handleClose()
      onSuccess?.()
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: BrandCreate) => brandsApi.update(brand!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brands"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      handleClose()
      onSuccess?.()
    },
  })

  const isPending = createMutation.isPending || updateMutation.isPending
  const error = createMutation.error || updateMutation.error

  function handleClose() {
    setOpen(false)
    if (!brand) {
      setName("")
      setAliases("")
      setDomain("")
      setDescription("")
    }
    setErrors({})
    createMutation.reset()
    updateMutation.reset()
  }

  function validate() {
    const newErrors: Record<string, string> = {}
    if (!name.trim()) newErrors.name = "Brand name is required"
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return

    const data: BrandCreate = {
      name: name.trim(),
      aliases: aliases
        ? aliases.split(",").map((a) => a.trim()).filter(Boolean)
        : [],
      domain: domain.trim() || undefined,
      description: description.trim() || undefined,
    }

    if (brand) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); else setOpen(true) }}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button>
            <Plus className="h-4 w-4" />
            Add Brand
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{brand ? "Edit Brand" : "Add Brand"}</DialogTitle>
          <DialogDescription>
            {brand
              ? "Update brand information for visibility monitoring."
              : "Add a new brand to track across AI providers."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="brand-name">
              Brand Name <span className="text-red-400">*</span>
            </label>
            <Input
              id="brand-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Corp"
              className={errors.name ? "border-red-500 focus-visible:ring-red-500" : ""}
            />
            {errors.name && (
              <p className="text-xs text-red-400">{errors.name}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="brand-aliases">
              Aliases
              <span className="ml-1 text-xs text-slate-500">(comma-separated)</span>
            </label>
            <Input
              id="brand-aliases"
              value={aliases}
              onChange={(e) => setAliases(e.target.value)}
              placeholder="e.g. ACME, Acme Corporation"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="brand-domain">
              Domain
            </label>
            <Input
              id="brand-domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g. acmecorp.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-300" htmlFor="brand-description">
              Description
            </label>
            <textarea
              id="brand-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the brand..."
              rows={3}
              className="flex w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 shadow-sm transition-colors placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {(error as Error).message || "Something went wrong"}
            </p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isPending}>
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              {brand ? "Save Changes" : "Add Brand"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
