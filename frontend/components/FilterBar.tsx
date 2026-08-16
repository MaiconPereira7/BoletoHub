"use client"

import { FilterX } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { BoletoFilters, BoletoStatus } from "@/types"

interface FilterBarProps {
  filters: BoletoFilters
  onChange: (filters: BoletoFilters) => void
}

const STATUS_OPTIONS: { value: BoletoStatus | ""; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "pendente", label: "Pendente" },
  { value: "pago", label: "Pago" },
  { value: "vencido", label: "Vencido" },
]

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border bg-card p-4 shadow-soft">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          className="h-10 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={filters.status || ""}
          onChange={(e) =>
            onChange({ ...filters, status: (e.target.value || undefined) as BoletoStatus | undefined, page: 1 })
          }
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="vencimento_de">Vencimento de</Label>
        <Input
          id="vencimento_de"
          type="date"
          value={filters.vencimento_de || ""}
          onChange={(e) => onChange({ ...filters, vencimento_de: e.target.value || undefined, page: 1 })}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="vencimento_ate">Vencimento até</Label>
        <Input
          id="vencimento_ate"
          type="date"
          value={filters.vencimento_ate || ""}
          onChange={(e) => onChange({ ...filters, vencimento_ate: e.target.value || undefined, page: 1 })}
        />
      </div>

      <Button
        variant="outline"
        className="gap-1.5"
        onClick={() => onChange({ page: 1, limit: filters.limit })}
      >
        <FilterX className="h-4 w-4" />
        Limpar filtros
      </Button>
    </div>
  )
}
