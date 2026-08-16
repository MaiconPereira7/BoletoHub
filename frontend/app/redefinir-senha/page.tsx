"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useState, type FormEvent } from "react"
import { ArrowLeft, KeyRound } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { PasswordInput } from "@/components/ui/password-input"
import { api } from "@/lib/api"

function RedefinirSenhaForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token") || ""

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError("As senhas não coincidem")
      return
    }

    setSubmitting(true)
    try {
      await api.post("/auth/reset-password", { token, new_password: password })
      setDone(true)
      setTimeout(() => router.push("/login"), 2500)
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível redefinir a senha"
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="w-full max-w-sm shadow-soft">
      <CardHeader className="items-center text-center">
        <span className="mb-2 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-soft">
          <KeyRound className="h-5 w-5" />
        </span>
        <CardTitle>Criar nova senha</CardTitle>
        <CardDescription>Escolha uma nova senha para sua conta</CardDescription>
      </CardHeader>
      <CardContent>
        {!token ? (
          <p className="text-center text-sm text-destructive">
            Link inválido — falta o token de redefinição. Solicite um novo link.
          </p>
        ) : done ? (
          <p className="text-center text-sm text-muted-foreground">
            Senha redefinida com sucesso! Redirecionando para o login...
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Nova senha</Label>
              <PasswordInput
                id="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="confirmPassword">Confirmar nova senha</Label>
              <PasswordInput
                id="confirmPassword"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <Button type="submit" disabled={submitting}>
              {submitting ? "Salvando..." : "Redefinir senha"}
            </Button>
          </form>
        )}

        <Link
          href="/login"
          className="mt-4 inline-flex w-full items-center justify-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar para o login
        </Link>
      </CardContent>
    </Card>
  )
}

export default function RedefinirSenhaPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden p-6">
      <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-blue-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />

      <Suspense fallback={null}>
        <RedefinirSenhaForm />
      </Suspense>
    </main>
  )
}
