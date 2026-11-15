const INVOICE_EDITABLE = [
  'supplier_name',
  'supplier_gstin',
  'buyer_gstin',
  'place_of_supply',
  'hsn_sac',
  'invoice_number',
  'taxable_value',
  'cgst',
  'sgst_or_utgst',
  'igst',
  'cess',
  'reverse_charge',
  'date',
  'total',
] as const

const LABELS: Record<string, string> = {
  document_type: 'Document type',
  supplier_name: 'Supplier name',
  supplier_gstin: 'Supplier GSTIN',
  buyer_gstin: 'Buyer GSTIN',
  supplier_pan: 'Supplier PAN',
  place_of_supply: 'Place of supply',
  hsn_sac: 'HSN/SAC',
  invoice_number: 'Invoice number',
  taxable_value: 'Taxable value',
  cgst: 'CGST',
  sgst_or_utgst: 'SGST / UTGST',
  igst: 'IGST',
  cess: 'Cess',
  reverse_charge: 'Reverse charge',
  purchase_order: 'Purchase order',
  project_code: 'Project code',
  cost_centre: 'Cost centre',
  merchant_name: 'Merchant name',
  date: 'Document date',
  due_date: 'Due date',
  subtotal: 'Subtotal',
  vat_total: 'VAT total',
  total: 'Total',
  currency: 'Currency',
}

const INR_FIELDS = new Set(['taxable_value', 'cgst', 'sgst_or_utgst', 'igst', 'cess', 'total', 'subtotal', 'vat_total'])

export function editableFields(): readonly string[] {
  return INVOICE_EDITABLE
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

export function displayValue(value: unknown, fieldName?: string): string {
  if (fieldName && INR_FIELDS.has(fieldName) && value !== null && value !== undefined && value !== '') {
    const amount = Number(value)
    if (Number.isFinite(amount)) return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount)
  }
  return value === null || value === undefined || value === '' ? 'Not found' : String(value)
}

export function inputValue(value: unknown): string {
  return value === null || value === undefined ? '' : String(value)
}
