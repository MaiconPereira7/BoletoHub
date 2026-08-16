"use client"

import Link from "next/link"
import { useState, type FormEvent } from "react"
import { ArrowLeft, KeyRound, Mail } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"

export default function EsqueciSenhaPage() {
  const [email, setEmail] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)

    try {
      await api.post("/auth/forgot-password", { email })
    } finally {
      setSubmitting(false)
      setSent(true)
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden p-6">
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-blue-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />

      <Card className="w-full max-w-sm shadow-soft">
        <CardHeader className="items-center text-center">
          <span className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-soft">
            <KeyRound className="h-5 w-5" />
          </span>
          <CardTitle>Esqueci minha senha</CardTitle>
          <CardDescription>Informe seu e-mail para receber um link de redefinição</CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="flex flex-col gap-4 text-center">
              <p className="text-sm text-muted-foreground">
                Se esse e-mail existir na nossa base, enviamos um link de redefinição de senha. Confira sua caixa de
                entrada (e o spam).
              </p>
              <Link
                href="/login"
                className="inline-flex items-center justify-center gap-1.5 text-sm font-medium text-primary hover:underline"
              >
                <ArrowLeft className="h-4 w-4" />
                Voltar para o login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="email">E-mail</Label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    required
                    className="pl-9"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <Button type="submit" disabled={submitting}>
                {submitting ? "Enviando..." : "Enviar link de redefinição"}
              </Button>

              <Link
                href="/login"
                className="inline-flex items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="h-4 w-4" />
                Voltar para o login
              </Link>
            </form>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
