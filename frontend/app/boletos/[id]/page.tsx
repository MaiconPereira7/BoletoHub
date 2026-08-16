"use client"

import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useCallback, useEffect, useState, type FormEvent } from "react"
import { ArrowLeft, CheckCircle2, Lock, Trash2, Unlock } from "lucide-react"

import { Navbar } from "@/components/Navbar"
import { StatusBadge } from "@/components/StatusBadge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import type { Boleto } from "@/types"

function formatCurrency(value: string | null) {
  if (value === null) return "—"
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value))
}

function formatDate(value: string | null) {
  if (!value) return "-"
  return new Date(`${value}T00:00:00`).toLocaleDateString("pt-BR")
}

export default function BoletoDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [boleto, setBoleto] = useState<Boleto | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [senha, setSenha] = useState("")
  const [unlocking, setUnlocking] = useState(false)
  const [unlockError, setUnlockError] = useState<string | null>(null)

  const loadBoleto = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get<Boleto>(`/boletos/${params.id}`)
      setBoleto(data)
    } catch {
      setError("Boleto não encontrado")
    } finally {
      setLoading(false)
    }
  }, [params.id])

  useEffect(() => {
    loadBoleto()
  }, [loadBoleto])

  async function markAsPaid() {
    setSaving(true)
    try {
      const { data } = await api.patch<Boleto>(`/boletos/${params.id}`, { status: "pago" })
      setBoleto(data)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    setSaving(true)
    try {
      await api.delete(`/boletos/${params.id}`)
      router.push("/dashboard")
    } finally {
      setSaving(false)
    }
  }

  async function handleUnlock(event: FormEvent) {
    event.preventDefault()
    setUnlocking(true)
    setUnlockError(null)
    try {
      const { data } = await api.post<Boleto>(`/boletos/${params.id}/desbloquear`, { senha })
      setBoleto(data)
      setSenha("")
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Senha incorreta"
      setUnlockError(message)
    } finally {
      setUnlocking(false)
    }
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <main className="container flex max-w-2xl flex-col gap-4 py-8">
        <Link
          href="/dashboard"
          className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar para meus boletos
        </Link>

        {loading && (
          <div className="flex flex-col gap-2">
            <div className="h-40 animate-pulse rounded-xl bg-muted" />
          </div>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}

        {boleto && (
          <Card className="shadow-soft">
            <CardHeader className="flex flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle>{boleto.beneficiario}</CardTitle>
                <p className="text-sm text-muted-foreground">Pagador: {boleto.pagador || "-"}</p>
              </div>
              {boleto.precisa_senha ? (
                <span className="flex items-center gap-1 rounded-full bg-secondary px-2.5 py-0.5 text-xs font-semibold text-secondary-foreground">
                  <Lock className="h-3 w-3" />
                  Protegido por senha
                </span>
              ) : (
                <StatusBadge status={boleto.status} />
              )}
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              {boleto.precisa_senha ? (
                <form onSubmit={handleUnlock} className="flex flex-col gap-3 rounded-lg border border-dashed p-4">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Lock className="h-4 w-4 text-muted-foreground" />
                    Este PDF está protegido por senha. Digite a senha para ver os dados.
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="senha">Senha do PDF</Label>
                    <Input
                      id="senha"
                      type="password"
                      required
                      value={senha}
                      onChange={(e) => setSenha(e.target.value)}
                    />
                  </div>
                  {unlockError && <p className="text-sm text-destructive">{unlockError}</p>}
                  <Button type="submit" disabled={unlocking} className="w-fit gap-1.5">
                    <Unlock className="h-4 w-4" />
                    {unlocking ? "Verificando..." : "Desbloquear"}
                  </Button>
                </form>
              ) : (
                <div className="rounded-lg bg-accent/40 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Valor</p>
                  <p className="text-3xl font-bold tabular-nums text-foreground">{formatCurrency(boleto.valor)}</p>
                </div>
              )}

              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-muted-foreground">Vencimento</dt>
                  <dd className="font-medium">{formatDate(boleto.data_vencimento)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Pagamento</dt>
                  <dd className="font-medium">{formatDate(boleto.data_pagamento)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Origem</dt>
                  <dd className="font-medium capitalize">{boleto.origem}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-muted-foreground">Linha digitável</dt>
                  <dd className="break-all rounded-md bg-muted px-2 py-1.5 font-mono text-xs">
                    {boleto.linha_digitavel || "-"}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-muted-foreground">Observações</dt>
                  <dd className="font-medium">{boleto.observacoes || "-"}</dd>
                </div>
              </dl>

              <div className="flex gap-3 border-t pt-4">
                {!boleto.precisa_senha && boleto.status !== "pago" && (
                  <Button onClick={markAsPaid} disabled={saving} className="gap-1.5">
                    <CheckCircle2 className="h-4 w-4" />
                    Marcar como pago
                  </Button>
                )}
                <Button variant="destructive" onClick={handleDelete} disabled={saving} className="gap-1.5">
                  <Trash2 className="h-4 w-4" />
                  Excluir
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
