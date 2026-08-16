import { CheckCircle2, Clock, TriangleAlert } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { BoletoStatus } from "@/types"

const STATUS_CONFIG: Record<
  BoletoStatus,
  { label: string; variant: "success" | "warning" | "destructive"; icon: typeof Clock }
> = {
  pendente: { label: "Pendente", variant: "warning", icon: Clock },
  pago: { label: "Pago", variant: "success", icon: CheckCircle2 },
  vencido: { label: "Vencido", variant: "destructive", icon: TriangleAlert },
}

export function StatusBadge({ status }: { status: BoletoStatus }) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  return (
    <Badge variant={config.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}
