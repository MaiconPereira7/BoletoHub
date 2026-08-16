"use client"

import { useState } from "react"
import { Loader2, ScanSearch } from "lucide-react"

import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import type { ScanStatusResponse, ScanTriggerResponse } from "@/types"

const POLL_INTERVAL_MS = 2000
const MAX_POLL_ATTEMPTS = 60

interface ScanButtonProps {
  onScanComplete: (boletosFound: number) => void
}

export function ScanButton({ onScanComplete }: ScanButtonProps) {
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleScan() {
    setScanning(true)
    setError(null)

    try {
      const { data: trigger } = await api.post<ScanTriggerResponse>("/boletos/scan")

      for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))

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

      setError("Tempo limite excedido ao escanear e-mails")
    } catch {
      setError("Não foi possível iniciar o escaneamento")
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button onClick={handleScan} disabled={scanning} className="gap-1.5">
        {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanSearch className="h-4 w-4" />}
        {scanning ? "Escaneando..." : "Escanear e-mails"}
      </Button>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
