import Link from "next/link"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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

export function BoletoCard({ boleto }: { boleto: Boleto }) {
  return (
    <Link href={`/boletos/${boleto.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <CardHeader className="flex flex-row items-start justify-between space-y-0">
          <CardTitle className="text-base">{boleto.beneficiario}</CardTitle>
          <StatusBadge status={boleto.status} />
        </CardHeader>
        <CardContent className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{formatCurrency(boleto.valor)}</span>
          <span>Vence em {formatDate(boleto.data_vencimento)}</span>
        </CardContent>
      </Card>
    </Link>
  )
}
