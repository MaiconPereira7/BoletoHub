"use client"

import { useState } from "react"
import { Loader2, ScanSearch } from "lucide-react"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import type { ScanStatusResponse, ScanTriggerResponse } from "@/types"

const POLL_INTERVAL_MS = 2000
const MAX_POLL_ATTEMPTS = 150 // ~5 minutos — caixas com bastante e-mail podem demorar
const SLOW_HINT_AFTER_ATTEMPTS = 20 // ~40s

interface ScanButtonProps {
  onScanComplete: (boletosFound: number) => void
}

export function ScanButton({ onScanComplete }: ScanButtonProps) {
  const [scanning, setScanning] = useState(false)
  const [slow, setSlow] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleScan() {
    setScanning(true)
    setSlow(false)
    setError(null)

    try {
      const { data: trigger } = await api.post<ScanTriggerResponse>("/boletos/scan")

      for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))

        if (attempt === SLOW_HINT_AFTER_ATTEMPTS) {
          setSlow(true)
        }

        const { data: status } = await api.get<ScanStatusResponse>(`/boletos/scan/${trigger.task_id}`)

        if (status.state === "completed") {
          onScanComplete(status.boletos_found || 0)
          setScanning(false)
          return
        }

        if (status.state === "failed") {
          setError(status.error || "Falha ao escanear e-mails")
          setScanning(false)
          return
        }
      }

      setError("O escaneamento está demorando mais que o esperado. Ele continua rodando — confira o dashboard em alguns instantes.")
    } catch {
      setError("Não foi possível iniciar o escaneamento")
    } finally {
      setScanning(false)
      setSlow(false)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button onClick={handleScan} disabled={scanning} className="gap-1.5">
        {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanSearch className="h-4 w-4" />}
        {scanning ? (slow ? "Ainda escaneando..." : "Escaneando...") : "Escanear e-mails"}
      </Button>
      {scanning && slow && (
        <p className="max-w-xs text-right text-xs text-muted-foreground">
          Caixas com bastante e-mail podem demorar alguns minutos.
        </p>
      )}
      {error && <p className="max-w-xs text-right text-sm text-destructive">{error}</p>}
    </div>
  )
}
