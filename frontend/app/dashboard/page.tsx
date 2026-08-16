"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, ChevronLeft, ChevronRight, Plus } from "lucide-react"

import { BoletoTable } from "@/components/BoletoTable"
import { FilterBar } from "@/components/FilterBar"
import { Navbar } from "@/components/Navbar"
import { ScanButton } from "@/components/ScanButton"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import type { Boleto, BoletoFilters, BoletoListResponse } from "@/types"

const DEFAULT_LIMIT = 20

export default function DashboardPage() {
  const [filters, setFilters] = useState<BoletoFilters>({ page: 1, limit: DEFAULT_LIMIT })
  const [boletos, setBoletos] = useState<Boleto[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [scanMessage, setScanMessage] = useState<string | null>(null)

  const loadBoletos = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<BoletoListResponse>("/boletos", { params: filters })
      setBoletos(data.items)
      setTotal(data.total)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadBoletos()
  }, [loadBoletos])

  const limit = filters.limit || DEFAULT_LIMIT
  const page = filters.page || 1
  const totalPages = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <main className="container flex flex-col gap-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Meus boletos</h1>
            <p className="text-sm text-muted-foreground">{total} boleto(s) encontrado(s)</p>
          </div>

          <div className="flex items-center gap-3">
            <ScanButton
              onScanComplete={(found) => {
                setScanMessage(`Escaneamento concluído: ${found} boleto(s) encontrado(s).`)
                loadBoletos()
              }}
            />
            <Link href="/boletos/novo" className="inline-flex">
              <Button variant="outline" className="gap-1.5">
                <Plus className="h-4 w-4" />
                Novo boleto
              </Button>
            </Link>
          </div>
        </div>

        {scanMessage && (
          <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-400">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {scanMessage}
          </div>
        )}

        <FilterBar filters={filters} onChange={setFilters} />

        {loading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : (
          <BoletoTable boletos={boletos} />
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setFilters({ ...filters, page: page - 1 })}
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </Button>
            <span className="text-sm text-muted-foreground">
              Página {page} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setFilters({ ...filters, page: page + 1 })}
            >
              Próxima
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </main>
    </div>
  )
}
