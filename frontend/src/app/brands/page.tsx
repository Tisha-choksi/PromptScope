"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { brandsApi, type Brand } from "@/lib/api"
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { BrandForm } from "@/components/brands/brand-form"
import { formatDate } from "@/lib/utils"
import {
  Building2,
  Edit2,
  Trash2,
  AlertCircle,
  Loader2,
  Globe,
  Tag,
} from "lucide-react"

function DeleteDialog({
  brand,
  open,
  onClose,
}: {
  brand: Brand | null
  open: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const deleteMutation = useMutation({
    mutationFn: (id: number) => brandsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["brands"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      onClose()
    },
  })

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Brand</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete{" "}
            <span className="font-semibold text-slate-300">{brand?.name}</span>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        {deleteMutation.error && (
          <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
            {(deleteMutation.error as Error).message || "Failed to delete brand"}
          </p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={deleteMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            disabled={deleteMutation.isPending}
            onClick={() => brand && deleteMutation.mutate(brand.id)}
          >
            {deleteMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function BrandsPage() {
  const [brandToDelete, setBrandToDelete] = useState<Brand | null>(null)

  const { data: brands, isLoading, error } = useQuery({
    queryKey: ["brands"],
    queryFn: brandsApi.list,
  })

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/10 border border-red-500/20">
          <AlertCircle className="h-7 w-7 text-red-400" />
        </div>
        <div className="text-center">
          <p className="text-slate-300 font-medium">Failed to load brands</p>
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
          <h1 className="text-2xl font-bold text-slate-100">Brands</h1>
          <p className="text-slate-400 mt-1">
            Manage brands tracked across AI providers
          </p>
        </div>
        <BrandForm />
      </div>

      {/* Brands Table */}
      <Card>
        <CardHeader className="pb-0">
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-indigo-400" />
            <CardTitle className="text-base">
              {isLoading ? "Loading..." : `${brands?.length ?? 0} Brand${(brands?.length ?? 0) !== 1 ? "s" : ""}`}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0 mt-4">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse flex items-center gap-4">
                  <div className="h-4 flex-1 bg-slate-700 rounded" />
                  <div className="h-4 w-32 bg-slate-700 rounded" />
                  <div className="h-4 w-24 bg-slate-700 rounded" />
                  <div className="h-8 w-16 bg-slate-700 rounded" />
                </div>
              ))}
            </div>
          ) : !brands?.length ? (
            <div className="py-16 text-center space-y-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-700/50 border border-slate-600/50 mx-auto">
                <Building2 className="h-6 w-6 text-slate-500" />
              </div>
              <div>
                <p className="text-slate-400 font-medium">No brands yet</p>
                <p className="text-slate-600 text-sm mt-0.5">
                  Add your first brand to start monitoring
                </p>
              </div>
              <BrandForm />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Aliases</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Added</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {brands.map((brand) => (
                  <TableRow key={brand.id}>
                    <TableCell className="font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600/15 border border-indigo-600/20 shrink-0">
                          <Building2 className="h-3.5 w-3.5 text-indigo-400" />
                        </div>
                        {brand.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {brand.aliases?.length ? (
                          brand.aliases.slice(0, 3).map((alias) => (
                            <span
                              key={alias}
                              className="inline-flex items-center gap-1 rounded border border-slate-600/50 bg-slate-700/50 px-1.5 py-0.5 text-xs text-slate-400"
                            >
                              <Tag className="h-2.5 w-2.5" />
                              {alias}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-600 text-sm">—</span>
                        )}
                        {(brand.aliases?.length ?? 0) > 3 && (
                          <span className="text-xs text-slate-500">
                            +{brand.aliases.length - 3} more
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {brand.domain ? (
                        <div className="flex items-center gap-1.5 text-slate-400 text-sm">
                          <Globe className="h-3.5 w-3.5 shrink-0" />
                          {brand.domain}
                        </div>
                      ) : (
                        <span className="text-slate-600 text-sm">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={brand.is_active ? "success" : "secondary"}>
                        {brand.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(brand.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <BrandForm
                          brand={brand}
                          trigger={
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <Edit2 className="h-3.5 w-3.5" />
                            </Button>
                          }
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-400 hover:text-red-400 hover:bg-red-500/10"
                          onClick={() => setBrandToDelete(brand)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <DeleteDialog
        brand={brandToDelete}
        open={!!brandToDelete}
        onClose={() => setBrandToDelete(null)}
      />
    </div>
  )
}
