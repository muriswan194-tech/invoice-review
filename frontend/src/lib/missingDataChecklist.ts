import type { Issue, Review } from './api'
import { fieldLabel } from './fields'

function isMissing(value: unknown): boolean {
  return value === null || value === undefined || value === ''
}

function missingIssues(review: Review): Issue[] {
  return review.issues.filter(
    (issue) => issue.code.endsWith('_required') && issue.field !== null && isMissing(review.document[issue.field]),
  )
}

export function hasMissingDataChecklistItems(review: Review): boolean {
  return missingIssues(review).length > 0
}

function safeFilenamePart(value: string): string {
  return value.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase() || 'invoice'
}

export function missingDataChecklistFilename(review: Review): string {
  const invoiceNumber = review.document.invoice_number
  const reference = typeof invoiceNumber === 'string' && invoiceNumber.trim() ? invoiceNumber : review.filename
  return `${safeFilenamePart(reference)}-missing-data-checklist.txt`
}

/** Build a local-only hand-off checklist from issues caused by absent source data. */
export function buildMissingDataChecklist(review: Review): string {
  const items = missingIssues(review)
  const supplier = typeof review.document.supplier_name === 'string' ? review.document.supplier_name : 'Not found'
  const invoiceNumber = typeof review.document.invoice_number === 'string' ? review.document.invoice_number : 'Not found'
  const heading = [
    'GST Invoice Requirements Reviewer',
    'Missing GST invoice particulars checklist',
    `File: ${review.filename}`,
    `Supplier: ${supplier || 'Not found'}`,
    `Invoice number: ${invoiceNumber || 'Not found'}`,
    `Generated locally: ${new Date().toLocaleString('en-IN')}`,
    '',
    'This checklist lists only applicable GST invoice particulars that are absent from the source document.',
    'It does not include internal accounting controls and does not provide tax or legal advice.',
    '',
  ]

  if (items.length === 0) {
    return [...heading, 'No applicable GST invoice particular is currently missing.'].join('\n')
  }

  const sections = items.flatMap((issue, index) => [
    `${index + 1}. ${fieldLabel(issue.field ?? 'data')}`,
    '   Status: Missing',
    `   Why it matters: ${issue.message}`,
    `   Next action: ${issue.next_action ?? 'Check the source invoice and correct the applicable GST particular.'}`,
    '',
  ])
  return [...heading, ...sections].join('\n')
}
