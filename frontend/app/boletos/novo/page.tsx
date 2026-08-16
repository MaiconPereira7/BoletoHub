import { AddBoletoForm } from "@/components/AddBoletoForm"
import { Navbar } from "@/components/Navbar"

export default function NovoBoletoPage() {
  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <main className="container flex max-w-2xl flex-col gap-6 py-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Adicionar boleto</h1>
          <p className="text-sm text-muted-foreground">
            Envie o PDF para extração automática ou cadastre os dados manualmente.
          </p>
        </div>

        <AddBoletoForm />
      </main>
    </div>
  )
}
