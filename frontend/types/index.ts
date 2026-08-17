export type BoletoStatus = "pendente" | "pago" | "vencido"
export type BoletoOrigem = "email" | "manual"

export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Category {
  id: string
  user_id: string
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface CategoryCreateInput {
  name: string
  color: string
}

export interface CategoryUpdateInput {
  name?: string
  color?: string
}

export interface Boleto {
  id: string
  user_id: string
  beneficiario: string
  pagador: string | null
  valor: string | null
  linha_digitavel: string | null
  codigo_barras: string | null
  data_vencimento: string | null
  data_pagamento: string | null
  status: BoletoStatus
  origem: BoletoOrigem
  precisa_senha: boolean
  arquivo_pdf_path: string | null
  observacoes: string | null
  category_id: string | null
  category: Category | null
  created_at: string
  updated_at: string
}

export interface BoletoListResponse {
  items: Boleto[]
  total: number
  page: number
  limit: number
}

export interface BoletoCreateInput {
  beneficiario: string
  pagador?: string
  valor: string
  linha_digitavel?: string
  codigo_barras?: string
  data_vencimento: string
  observacoes?: string
  category_id?: string
}

export interface BoletoUpdateInput {
  beneficiario?: string
  pagador?: string
  valor?: string
  linha_digitavel?: string
  codigo_barras?: string
  data_vencimento?: string
  data_pagamento?: string
  status?: BoletoStatus
  observacoes?: string
  category_id?: string | null
}

export interface BoletoFilters {
  status?: BoletoStatus
  vencimento_de?: string
  vencimento_ate?: string
  category_id?: string
  page?: number
  limit?: number
}

export interface ScanTriggerResponse {
  task_id: string
}

export interface ScanStatusResponse {
  task_id: string
  state: string
  boletos_found?: number | null
  error?: string | null
}

export interface EmailAccount {
  id: string
  email: string
  imap_host: string
  imap_port: number
  imap_use_ssl: boolean
  ativo: boolean
  created_at: string
}

export interface EmailAccountCreateInput {
  email: string
  imap_host: string
  imap_port: number
  imap_password: string
  imap_use_ssl: boolean
}
