"use client"

import { useCallback, useEffect, useState, type FormEvent } from "react"
import { Pencil, Plus, Tag, Trash2, X } from "lucide-react"

import { Navbar } from "@/components/Navbar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import type { Category, CategoryCreateInput } from "@/types"

const EMPTY_FORM: CategoryCreateInput = { name: "", color: "#64748b" }

export default function CategoriasPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<CategoryCreateInput>(EMPTY_FORM)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadCategories = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<Category[]>("/categories")
      setCategories(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  function updateField<K extends keyof CategoryCreateInput>(field: K, value: CategoryCreateInput[K]) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function startEdit(category: Category) {
    setEditingId(category.id)
    setForm({ name: category.name, color: category.color })
    setError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setError(null)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      if (editingId) {
        await api.patch(`/categories/${editingId}`, form)
      } else {
        await api.post("/categories", form)
      }
      setForm(EMPTY_FORM)
      setEditingId(null)
      await loadCategories()
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível salvar a categoria"
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/categories/${id}`)
    if (editingId === id) cancelEdit()
    await loadCategories()
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <Navbar />

      <main className="container flex max-w-2xl flex-col gap-6 py-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Categorias</h1>
          <p className="text-sm text-muted-foreground">
            Organize seus boletos por categoria para acompanhar os gastos no dashboard.
          </p>
        </div>

        {loading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted" />
        ) : categories.length > 0 ? (
          <div className="flex flex-col gap-2">
            {categories.map((category) => (
              <div
                key={category.id}
                className="flex items-center justify-between rounded-xl border bg-card p-4 shadow-soft"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-lg"
                    style={{ backgroundColor: `${category.color}20`, color: category.color }}
                  >
                    <Tag className="h-4 w-4" />
                  </span>
                  <p className="text-sm font-medium">{category.name}</p>
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" className="text-muted-foreground" onClick={() => startEdit(category)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => handleDelete(category.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed bg-card/50 p-8 text-center text-sm text-muted-foreground">
            Nenhuma categoria cadastrada ainda.
          </div>
        )}

        <Card className="shadow-soft">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-lg">{editingId ? "Editar categoria" : "Nova categoria"}</CardTitle>
            {editingId && (
              <Button variant="ghost" size="icon" onClick={cancelEdit} className="text-muted-foreground">
                <X className="h-4 w-4" />
              </Button>
            )}
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto]">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="name">Nome *</Label>
                  <Input
                    id="name"
                    required
                    value={form.name}
                    onChange={(e) => updateField("name", e.target.value)}
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="color">Cor</Label>
                  <input
                    id="color"
                    type="color"
                    value={form.color}
                    onChange={(e) => updateField("color", e.target.value)}
                    className="h-10 w-16 cursor-pointer rounded-md border border-input bg-background"
                  />
                </div>
              </div>

              {error && <p className="text-sm text-destructive">{error}</p>}

              <Button type="submit" disabled={submitting} className="w-fit gap-1.5">
                <Plus className="h-4 w-4" />
                {submitting ? "Salvando..." : editingId ? "Salvar alterações" : "Adicionar categoria"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
