import type { DocumentType } from './api'

const INVOICE_EDITABLE = [
  'supplier_name',
  'supplier_vat_id',
  'customer_vat_id',
  'invoice_number',
  'purchase_order',
  'date',
  'due_date',
  'subtotal',
  'vat_total',
  'total',
  'currency',
] as const

const RECEIPT_EDITABLE = [
  'merchant_name',
  'date',
  'subtotal',
  'vat_total',
  'total',
  'currency',
] as const

const LABELS: Record<string, string> = {
  document_type: 'Document type',
  supplier_name: 'Supplier name',
  supplier_vat_id: 'Supplier VAT number',
  customer_vat_id: 'Customer VAT number',
  invoice_number: 'Invoice number',
  purchase_order: 'Purchase order',
  merchant_name: 'Merchant name',
  date: 'Document date',
  due_date: 'Due date',
  subtotal: 'Subtotal',
  vat_total: 'VAT total',
  total: 'Total',
  currency: 'Currency',
}

export function editableFields(documentType: DocumentType): readonly string[] {
  return documentType === 'invoice' ? INVOICE_EDITABLE : RECEIPT_EDITABLE
}

export function fieldLabel(fieldName: string): string {
  return LABELS[fieldName] ?? fieldName.replaceAll('_', ' ')
}

export function sourceLabel(source: string | undefined): string {
  if (source === 'human') return 'Corrected by you'
  if (source === 'azure_openai_fallback') return 'AI fallback'
  if (source === 'document_intelligence') return 'Document Intelligence'
  return 'Not found'
}

export function displayValue(value: unknown): string {
  return value === null || value === undefined || value === '' ? 'Not found' : String(value)
}

export function inputValue(value: unknown): string {
  return value === null || value === undefined ? '' : String(value)
}
