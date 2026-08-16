"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { FileText, PenLine, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import type { BoletoCreateInput } from "@/types"

const EMPTY_FORM: BoletoCreateInput = {
  beneficiario: "",
  pagador: "",
  valor: "",
  linha_digitavel: "",
  data_vencimento: "",
  observacoes: "",
}

export function AddBoletoForm() {
  const [form, setForm] = useState<BoletoCreateInput>(EMPTY_FORM)
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  function updateField<K extends keyof BoletoCreateInput>(field: K, value: BoletoCreateInput[K]) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      await api.post("/boletos", {
        ...form,
        pagador: form.pagador || undefined,
        linha_digitavel: form.linha_digitavel || undefined,
        observacoes: form.observacoes || undefined,
      })
      router.push("/dashboard")
      router.refresh()
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível salvar o boleto"
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!file) return

    setSubmitting(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append("file", file)
      await api.post("/boletos/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      router.push("/dashboard")
      router.refresh()
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível processar o PDF"
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <form onSubmit={handleUpload} className="flex flex-col gap-4 rounded-xl border bg-card p-6 shadow-soft">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Upload className="h-4 w-4" />
          </span>
          <h2 className="text-lg font-semibold">Enviar PDF do boleto</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Os dados serão extraídos automaticamente do arquivo.
        </p>

        <label
          htmlFor="pdf-file"
          className="flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed border-input bg-muted/30 px-6 py-8 text-center transition-colors hover:border-primary/50 hover:bg-accent/30"
        >
          <FileText className="h-7 w-7 text-muted-foreground" />
          <span className="text-sm font-medium">{file ? file.name : "Clique para escolher um arquivo PDF"}</span>
          <span className="text-xs text-muted-foreground">ou arraste e solte aqui</span>
        </label>
        <input
          id="pdf-file"
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <Button type="submit" disabled={!file || submitting} className="w-fit gap-1.5">
          <Upload className="h-4 w-4" />
          Enviar e extrair dados
        </Button>
      </form>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-xl border bg-card p-6 shadow-soft">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <PenLine className="h-4 w-4" />
          </span>
          <h2 className="text-lg font-semibold">Cadastrar manualmente</h2>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="beneficiario">Beneficiário *</Label>
            <Input
              id="beneficiario"
              required
              value={form.beneficiario}
              onChange={(e) => updateField("beneficiario", e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pagador">Pagador</Label>
            <Input id="pagador" value={form.pagador} onChange={(e) => updateField("pagador", e.target.value)} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="valor">Valor (R$) *</Label>
            <Input
              id="valor"
              type="number"
              step="0.01"
              min="0.01"
              required
              value={form.valor}
              onChange={(e) => updateField("valor", e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="data_vencimento">Vencimento *</Label>
            <Input
              id="data_vencimento"
              type="date"
              required
              value={form.data_vencimento}
              onChange={(e) => updateField("data_vencimento", e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <Label htmlFor="linha_digitavel">Linha digitável</Label>
            <Input
              id="linha_digitavel"
              value={form.linha_digitavel}
              onChange={(e) => updateField("linha_digitavel", e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <Label htmlFor="observacoes">Observações</Label>
            <Input
              id="observacoes"
              value={form.observacoes}
              onChange={(e) => updateField("observacoes", e.target.value)}
            />
          </div>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" disabled={submitting} className="w-fit">
          Salvar boleto
        </Button>
      </form>
    </div>
  )
}
