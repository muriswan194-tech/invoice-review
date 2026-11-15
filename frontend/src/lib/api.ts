import { env } from './env'

export type DocumentType = 'invoice' | 'receipt'

export type CheckResult = {
  status: string
  message: string
  difference?: string | null
  missing?: string[]
  key?: string | null
  buyer_matches?: boolean | null
  supplier_valid?: boolean | null
  buyer_valid?: boolean | null
  confidence?: number | null
  name?: string
  assessments?: Record<string, { applicability: 'applicable' | 'not_applicable'; state: 'present' | 'missing' | 'invalid' | 'not_assessed' }>
}

export type Issue = {
  code: string
  severity: 'error' | 'warning'
  message: string
  field: string | null
  evidence?: Record<string, string>
  route?: 'AP reviewer' | 'Project manager' | 'Accountant / TDS review' | 'Supplier clarification'
  next_action?: string
}

export type Review = {
  record_id: number
  document_type: DocumentType
  filename: string
  saved_name: string
  review_status: string
  is_demo: boolean
  upload_count: number
  can_edit: boolean
  primary_confidence: number | null
  classification: {
    document_type: DocumentType
    confidence?: number | null
    source?: string
  }
  field_sources: Record<string, string>
  conflicts: string[]
  document: Record<string, unknown>
  checks: Record<string, CheckResult>
  issues: Issue[]
}

export type ProcessingStage = 'extract' | 'validate'

export type GstSource = {
  id: string
  name: string
  authority: string
  category: string
  purpose: string
  url: string
  related_rules: string[]
  last_checked: string
  status: string
  limitation: string
}


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

export async function uploadDocumentWithProgress(
  file: File,
  documentType: DocumentType,
  onProgress: (stage: ProcessingStage) => void,
): Promise<Review> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_type', documentType)

  const response = await fetch(`${env.apiBaseUrl}/invoices/upload/stream`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) return readBody<Review>(response, 'The document could not be processed.')
  if (!response.body) throw new Error('The review pipeline did not return progress updates.')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''
    for (const rawEvent of events) {
      if (!rawEvent.startsWith('data: ')) continue
      const event = JSON.parse(rawEvent.slice(6)) as { event: string; stage?: ProcessingStage; detail?: string; review?: Review }
      if (event.event === 'progress' && event.stage) onProgress(event.stage)
      if (event.event === 'error') throw new Error(event.detail ?? 'The document could not be processed.')
      if (event.event === 'complete' && event.review) return event.review
    }
    if (done) break
  }
  throw new Error('The review pipeline ended before returning a review.')
}

export async function openDemoReview(): Promise<Review> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/demo`, { method: 'POST' })
  return readBody<Review>(response, 'The local demo could not be opened.')
}

export async function fetchHistory(): Promise<Review[]> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/history`)
  return readBody<Review[]>(response, 'Review history could not be loaded.')
}

export async function fetchGstSources(): Promise<GstSource[]> {
  const response = await fetch(`${env.apiBaseUrl}/gst-sources`)
  return readBody<GstSource[]>(response, 'GST sources could not be loaded.')
}

export async function saveCorrections(recordId: number, fields: Record<string, string | null>): Promise<Review> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields }),
  })
  return readBody<Review>(response, 'The corrections could not be saved.')
}

export async function deleteReview(recordId: number): Promise<void> {
  const response = await fetch(`${env.apiBaseUrl}/invoices/${recordId}`, { method: 'DELETE' })
  if (!response.ok) {
    await readBody<unknown>(response, 'The review could not be deleted.')
  }
}

export function reviewDocumentUrl(recordId: number): string {
  return `${env.apiBaseUrl}/invoices/${recordId}/document`
}
