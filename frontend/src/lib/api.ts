import { env } from './env'

export type DocumentType = 'invoice' | 'receipt'

export type CheckResult = {
  status: string
  message: string
  difference?: string | null
  missing?: string[]
  key?: string | null
  supplier_valid?: boolean | null
  customer_valid?: boolean | null
  customer_matches?: boolean | null
  confidence?: number | null
}

export type Issue = {
  code: string
  severity: 'error' | 'warning'
  message: string
  field: string | null
}

export type GlSuggestion = {
  account_code: string
  account_name: string
  confidence: number
}

export type AdvisorRecommendation = {
  recommendation: 'APPROVE' | 'CORRECTION_REQUIRED' | 'ESCALATE'
  summary: string
  reasons: string[]
  questions_for_reviewer: string[]
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type GlAccount = {
  code: string
  name: string
}

export type Review = {
  record_id: number
  document_type: DocumentType
  filename: string
  saved_name: string
  review_status: string
  upload_count: number
  can_approve: boolean
  can_edit: boolean
  can_request_correction: boolean
  primary_confidence: number | null
  selected_account_code: string | null
  classification: {
    document_type: DocumentType
    confidence: number
  }
  field_sources: Record<string, string>
  conflicts: string[]
  gl_suggestion: GlSuggestion
  advisor: AdvisorRecommendation | null
  document: Record<string, unknown>
  checks: Record<string, CheckResult>
  issues: Issue[]
}

export type CorrectionEmail = {
  subject: string
  body: string
}

export type Decision = 'approved' | 'rejected' | 'correction_requested'

async function readBody<T>(response: Response, fallbackMessage: string): Promise<T> {
  const body = await response.json() as T | { detail?: string }
  if (!response.ok) {
    const detail = typeof body === 'object' && body !== null && 'detail' in body ? body.detail : null
    throw new Error(detail ?? fallbackMessage)
  }
  return body as T
}

export async function uploadDocument(file: File, documentType: DocumentType): Promise<Review> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_type', documentType)

  const response = await fetch(`${env.apiBaseUrl}/invoices/upload`, {
    method: 'POST',
    body: formData,
  })
  return readBody<Review>(response, 'The document could not be processed.')
}

export async function fetchHistory(): Promise<Review[]> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/history`)
  return readBody<Review[]>(response, 'Review history could not be loaded.')
}

export async function saveCorrections(recordId: number, fields: Record<string, string | null>): Promise<Review> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields }),
  })
  return readBody<Review>(response, 'The corrections could not be saved.')
}

export async function saveAccount(recordId: number, accountCode: string): Promise<Review> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}/accounting`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_code: accountCode }),
  })
  return readBody<Review>(response, 'The account selection could not be saved.')
}

export async function updateDecision(recordId: number, decision: Decision): Promise<Review> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  })
  return readBody<Review>(response, 'The review decision could not be saved.')
}

export async function deleteReview(recordId: number): Promise<void> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}`, { method: 'DELETE' })
  if (!response.ok) {
    await readBody<unknown>(response, 'The review could not be deleted.')
  }
}

export async function requestCorrectionEmail(recordId: number): Promise<CorrectionEmail> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}/correction-email`, {
    method: 'POST',
  })
  return readBody<CorrectionEmail>(response, 'The correction draft could not be generated.')
}

export async function fetchGlAccounts(): Promise<GlAccount[]> {
  const response = await fetch(`${env.apiBaseUrl}/accounting/gl-accounts`)
  return readBody<GlAccount[]>(response, 'The GL catalog could not be loaded.')
}
