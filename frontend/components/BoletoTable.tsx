"use client"

import Link from "next/link"
import { Inbox, Lock } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { CategoryBadge } from "@/components/CategoryBadge"
import { StatusBadge } from "@/components/StatusBadge"
import type { Boleto } from "@/types"

function formatCurrency(value: string | null) {
  if (value === null) return "—"
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value))
}

function formatDate(value: string | null) {
  if (!value) return "—"
  return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR")
}

export function BoletoTable({ boletos }: { boletos: Boleto[] }) {
  if (boletos.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed bg-card/50 p-10 text-center text-sm text-muted-foreground">
        <Inbox className="h-8 w-8 text-muted-foreground/60" />
        Nenhum boleto encontrado.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border bg-card shadow-soft">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left">
          <tr>
            <th className="p-3 font-medium text-muted-foreground">Beneficiário</th>
            <th className="p-3 font-medium text-muted-foreground">Valor</th>
            <th className="p-3 font-medium text-muted-foreground">Vencimento</th>
            <th className="p-3 font-medium text-muted-foreground">Status</th>
            <th className="p-3 font-medium text-muted-foreground">Categoria</th>
            <th className="p-3 font-medium text-muted-foreground">Origem</th>
          </tr>
        </thead>
        <tbody>
          {boletos.map((boleto) => (
            <tr key={boleto.id} className="border-t transition-colors hover:bg-accent/40">
              <td className="p-3">
                <Link href={`/boletos/${boleto.id}`} className="font-medium hover:text-primary hover:underline">
                  {boleto.beneficiario}
                </Link>
              </td>
              <td className="p-3 tabular-nums">{formatCurrency(boleto.valor)}</td>
              <td className="p-3 tabular-nums">{formatDate(boleto.data_vencimento)}</td>
              <td className="p-3">
                {boleto.precisa_senha ? (
                  <Badge variant="secondary" className="gap-1">
                    <Lock className="h-3 w-3" />
                    Protegido por senha
                  </Badge>
                ) : (
                  <StatusBadge status={boleto.status} />
                )}
              </td>
              <td className="p-3">
                <CategoryBadge category={boleto.category} />
              </td>
              <td className="p-3 capitalize text-muted-foreground">{boleto.origem}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
