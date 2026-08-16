"use client"

import Link from "next/link"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Mail, Receipt, ScanSearch, ShieldCheck } from "lucide-react"

import { buttonVariants } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

const FEATURES = [
  {
    icon: Mail,
    title: "Conecte seu e-mail",
    description: "Ligamos na sua caixa de entrada via IMAP para encontrar boletos automaticamente.",
  },
  {
    icon: ScanSearch,
    title: "Detecção automática",
    description: "Extraímos valor, vencimento e linha digitável direto do PDF, sem digitar nada.",
  },
  {
    icon: ShieldCheck,
    title: "Tudo em um lugar",
    description: "Acompanhe status de pendente, pago e vencido com alertas antes do prazo.",
  },
]

export default function HomePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard")
    }
  }, [loading, user, router])

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-16 overflow-hidden p-6 py-24">
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-blue-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-cyan-400/20 blur-3xl" />

      <div className="flex flex-col items-center gap-6 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-soft">
          <Receipt className="h-7 w-7" />
        </span>
        <h1 className="brand-gradient-text text-5xl font-bold tracking-tight">BoletoHub</h1>
        <p className="max-w-md text-center text-muted-foreground">
          Conecte sua caixa de e-mail, detecte boletos automaticamente e organize tudo em um só lugar.
        </p>
        <div className="flex gap-3">
          <Link href="/login" className={buttonVariants({ variant: "default" })}>
            Entrar
          </Link>
          <Link href="/register" className={buttonVariants({ variant: "outline" })}>
            Criar conta
          </Link>
        </div>
      </div>

      <div className="grid w-full max-w-3xl gap-4 sm:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="flex flex-col gap-2 rounded-xl border bg-card p-5 shadow-soft">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <Icon className="h-4 w-4" />
            </span>
            <h3 className="text-sm font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        ))}
      </div>
    </main>
  )
}
