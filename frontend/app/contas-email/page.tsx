"use client"

import { useCallback, useEffect, useState, type FormEvent } from "react"
import { Mail, Plus, Trash2 } from "lucide-react"

import { Navbar } from "@/components/Navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import type { EmailAccount, EmailAccountCreateInput } from "@/types"

const EMPTY_FORM: EmailAccountCreateInput = {
  email: "",
  imap_host: "imap.gmail.com",
  imap_port: 993,
  imap_password: "",
  imap_use_ssl: true,
}

export default function ContasEmailPage() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<EmailAccountCreateInput>(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadAccounts = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<EmailAccount[]>("/email-accounts")
      setAccounts(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAccounts()
  }, [loadAccounts])

  function updateField<K extends keyof EmailAccountCreateInput>(field: K, value: EmailAccountCreateInput[K]) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      await api.post("/email-accounts", form)
      setForm(EMPTY_FORM)
      await loadAccounts()
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível adicionar a conta de e-mail"
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/email-accounts/${id}`)
    await loadAccounts()
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <main className="container flex max-w-2xl flex-col gap-6 py-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Contas de e-mail</h1>
          <p className="text-sm text-muted-foreground">
            Cadastre as caixas de e-mail que devem ser escaneadas em busca de boletos. Todas aparecem juntas no
            dashboard.
          </p>
        </div>

        {loading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted" />
        ) : accounts.length > 0 ? (
          <div className="flex flex-col gap-2">
            {accounts.map((account) => (
              <div
                key={account.id}
                className="flex items-center justify-between rounded-xl border bg-card p-4 shadow-soft"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <Mail className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm font-medium">{account.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {account.imap_host}:{account.imap_port}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive"
                  onClick={() => handleDelete(account.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed bg-card/50 p-8 text-center text-sm text-muted-foreground">
            Nenhuma conta de e-mail cadastrada ainda.
          </div>
        )}

        <Card className="shadow-soft">
          <CardHeader>
            <CardTitle className="text-lg">Adicionar conta de e-mail</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5 sm:col-span-2">
                  <Label htmlFor="email">E-mail *</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => updateField("email", e.target.value)}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="imap_host">Servidor IMAP *</Label>
                  <Input
                    id="imap_host"
                    required
                    value={form.imap_host}
                    onChange={(e) => updateField("imap_host", e.target.value)}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="imap_port">Porta *</Label>
                  <Input
                    id="imap_port"
                    type="number"
                    required
                    value={form.imap_port}
                    onChange={(e) => updateField("imap_port", Number(e.target.value))}
                  />
                </div>

                <div className="flex flex-col gap-1.5 sm:col-span-2">
                  <Label htmlFor="imap_password">Senha de app *</Label>
                  <Input
                    id="imap_password"
                    type="password"
                    required
                    value={form.imap_password}
                    onChange={(e) => updateField("imap_password", e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    No Gmail, use uma senha de app (não a senha normal da conta).
                  </p>
                </div>
              </div>

              {error && <p className="text-sm text-destructive">{error}</p>}

              <Button type="submit" disabled={submitting} className="w-fit gap-1.5">
                <Plus className="h-4 w-4" />
                {submitting ? "Adicionando..." : "Adicionar conta"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
