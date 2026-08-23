import { useEffect, useState } from 'react'

import AccountSelector from './components/AccountSelector'
import CorrectionEmailDialog from './components/CorrectionEmailDialog'
import DocumentInbox from './components/DocumentInbox'
import FieldEditor from './components/FieldEditor'
import ReviewFindings from './components/ReviewFindings'
import UploadStep from './components/UploadStep'
import Notice from './components/ui/Notice'
import Tag from './components/ui/Tag'
import {
  deleteReview, fetchGlAccounts, fetchHistory, requestCorrectionEmail, saveAccount,
  saveCorrections, updateDecision, uploadDocument,
  type CorrectionEmail, type Decision, type DocumentType, type GlAccount, type Review,
} from './lib/api'
import { displayValue } from './lib/fields'

type Screen = 'landing' | 'upload' | 'processing' | 'review' | 'history'

const PROCESSING_STEPS = [
  ['Classify document', 'Recognizing whether the upload is an invoice or a receipt.'],
  ['Extract and cross-check', 'Running Document Intelligence and the independent LLM review.'],
  ['Validate Northstar policy', 'Applying deterministic invoice and receipt rules, including VAT and totals.'],
  ['Suggest GL account', 'Matching normalized fields to the fixed Northstar account catalog.'],
]

function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [documentType, setDocumentType] = useState<DocumentType>('invoice')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [accounts, setAccounts] = useState<GlAccount[]>([])
  const [history, setHistory] = useState<Review[]>([])
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isDrafting, setIsDrafting] = useState(false)
  const [draft, setDraft] = useState<CorrectionEmail | null>(null)

  useEffect(() => {
    void refreshHistory()
    fetchGlAccounts().then(setAccounts).catch(() => setAccounts([]))
  }, [])

  async function refreshHistory() {
    setHistory(await fetchHistory().catch(() => []))
  }

  function reportError(caught: unknown, fallback: string) {
    setError(caught instanceof Error ? caught.message : fallback)
  }

  function beginNewReview() {
    setReview(null); setSelectedFile(null); setDraft(null); setError(null); setNotice(null); setScreen('upload')
  }

  async function runReview() {
    if (!selectedFile) return
    setError(null); setNotice(null); setScreen('processing'); setIsProcessing(true)
    try {
      setReview(await uploadDocument(selectedFile, documentType))
      await refreshHistory()
      setScreen('review')
    } catch (uploadError) {
      reportError(uploadError, 'The document could not be processed.')
      setScreen('upload')
    } finally {
      setIsProcessing(false)
    }
  }

  async function handleCorrections(fields: Record<string, string | null>) {
    if (!review) return false
    setIsSaving(true); setError(null)
    try {
      setReview(await saveCorrections(review.record_id, fields)); await refreshHistory()
      setNotice('Saved changes and reran the Northstar checks.')
      return true
    } catch (caught) { reportError(caught, 'The corrections could not be saved.'); return false } finally { setIsSaving(false) }
  }

  async function handleAccount(accountCode: string) {
    if (!review) return
    setIsSaving(true); setError(null)
    try { setReview(await saveAccount(review.record_id, accountCode)); setNotice('GL account selection saved.') }
    catch (caught) { reportError(caught, 'The account selection could not be saved.') } finally { setIsSaving(false) }
  }

  async function handleDecision(decision: Decision) {
    if (!review) return
    setIsSaving(true); setError(null)
    try {
      const updated = await updateDecision(review.record_id, decision)
      setReview(updated); await refreshHistory(); setNotice(`Decision recorded: ${updated.review_status.replaceAll('_', ' ')}.`)
    } catch (caught) { reportError(caught, 'The review decision could not be saved.') } finally { setIsSaving(false) }
  }

  async function handleCorrectionEmail() {
    if (!review) return
    setIsDrafting(true); setError(null)
    try { setDraft(await requestCorrectionEmail(review.record_id)) }
    catch (caught) { reportError(caught, 'The correction request could not be drafted.') } finally { setIsDrafting(false) }
  }

  async function handleDelete(recordId: number) {
    if (!window.confirm('Delete this review and its locally stored upload?')) return
    setError(null)
    try { await deleteReview(recordId); await refreshHistory(); if (review?.record_id === recordId) setReview(null); setNotice('Review deleted.') }
    catch (caught) { reportError(caught, 'The review could not be deleted.') }
  }

  function openReview(record: Review) {
    setReview(record); setDraft(null); setError(null); setNotice(null); setScreen('review')
  }

  return <div className="app-shell">
    {screen !== 'landing' && <header className="app-nav">
      <button type="button" className="brand-link" onClick={() => setScreen('landing')}><strong>Document review</strong><span>Northstar Facilities B.V.</span></button>
      <nav aria-label="Primary navigation"><button type="button" className="nav-link" onClick={() => setScreen('history')}>History</button><button type="button" className="button-primary button-small" onClick={beginNewReview}>New review</button></nav>
    </header>}
    <main className={screen === 'landing' ? 'landing-main' : 'workflow-main'}>
      {screen === 'landing' && <section className="landing-card" aria-labelledby="landing-title">
        <p className="org-label">Northstar Facilities B.V.</p><h1 id="landing-title">Document review</h1>
        <p className="landing-copy">Upload an invoice or receipt, run the review pipeline, and inspect the prepared result before bookkeeping.</p>
        <div className="landing-actions"><button type="button" className="button-primary" onClick={beginNewReview}>Review a document</button><button type="button" className="button-secondary" onClick={() => setScreen('history')}>View history</button></div>
        <div className="how-it-works"><h2>How it works</h2>{['Upload a document', 'Run the pipeline', 'Inspect the result'].map((label, index) => <div className="how-row" key={label}><span>{index + 1}</span><strong>{label}</strong><p>{['Choose an invoice or receipt and check the preview.', 'Classify, extract, validate VAT and policy, then suggest a GL account.', 'Review classification, extraction, findings, and the GL suggestion.'][index]}</p></div>)}</div>
      </section>}
      {screen === 'upload' && <section className="workflow-column" aria-labelledby="upload-title">
        <button type="button" className="back-link" onClick={() => setScreen('landing')}>Back</button><p className="step-label">Step 1 of 3</p><h1 id="upload-title">Choose an invoice or receipt</h1><p className="page-copy">Check the preview first. The file is only sent to Azure after you confirm.</p>
        {error && <Notice tone="error">{error}</Notice>}
        <UploadStep documentType={documentType} selectedFile={selectedFile} onTypeChange={setDocumentType} onFile={setSelectedFile} onClear={() => setSelectedFile(null)} />
        <div className="workflow-actions"><button type="button" className="button-primary" disabled={!selectedFile} onClick={() => void runReview()}>Run review</button></div>
      </section>}
      {screen === 'processing' && <section className="processing-card" aria-live="polite" aria-labelledby="processing-title">
        <div className="processing-orbit" aria-hidden="true" /><p className="step-label">Step 2 of 3</p><h1 id="processing-title">Processing document</h1><p className="page-copy">Working through the review pipeline for {selectedFile?.name ?? 'your document'}.</p>
        <ol className="pipeline-list">{PROCESSING_STEPS.map(([name, description], index) => <li className={isProcessing && index === 0 ? 'active' : ''} key={name}><span>{index + 1}</span><div><strong>{name}</strong><p>{description}</p></div></li>)}</ol><p className="processing-note">The review pipeline is running. This can take a moment.</p>
      </section>}
      {screen === 'review' && review && <section className="review-column" aria-labelledby="review-title">
        <div className="review-intro"><div><p className="step-label">Step 3 of 3</p><h1 id="review-title">Review prepared document</h1><p className="page-copy">{review.filename}</p></div><Tag status={review.review_status}>{review.review_status.replaceAll('_', ' ')}</Tag></div>
        {error && <Notice tone="error">{error}</Notice>}{notice && <Notice tone="success">{notice}</Notice>}
        {review.classification.document_type !== review.document_type && <Notice tone="warning">The AI classified this as a {review.classification.document_type}. You selected {review.document_type}; the selected type is being used for policy checks.</Notice>}
        <FieldEditor review={review} isSaving={isSaving} onSave={handleCorrections} />
        <section className="summary-section" aria-labelledby="summary-title"><h2 id="summary-title">{review.document_type === 'invoice' ? 'Invoice' : 'Receipt'} summary</h2><p>The combined values used for this review.</p><dl className="summary-grid">{Object.entries(review.document).filter(([key]) => key !== 'document_type').map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{displayValue(value)}</dd></div>)}</dl></section>
        <ReviewFindings review={review} /><AccountSelector review={review} accounts={accounts} isSaving={isSaving} onSelect={handleAccount} />
        {review.can_edit && <section className="decision-area" aria-label="Review decision">{!review.can_approve && <Notice tone="warning">Approval is available once blocking issues are resolved and a GL account is selected.</Notice>}<div className="decision-actions"><button type="button" className="button-danger" onClick={() => void handleDecision('rejected')} disabled={isSaving}>Reject</button><span />{review.can_request_correction && <button type="button" className="button-secondary" onClick={() => void handleCorrectionEmail()} disabled={isDrafting}>{isDrafting ? 'Drafting…' : 'Draft correction email'}</button>}<button type="button" className="button-approve" onClick={() => void handleDecision('approved')} disabled={isSaving || !review.can_approve}>Approve</button></div></section>}
        {draft && <CorrectionEmailDialog draft={draft} onClose={() => setDraft(null)} />}
      </section>}
      {screen === 'history' && <section className="history-page" aria-labelledby="history-title"><div className="history-page-head"><div><h1 id="history-title">Review history</h1><p className="page-copy">Previously prepared invoices and receipts, newest first.</p></div><button type="button" className="button-primary" onClick={beginNewReview}>New review</button></div>{error && <Notice tone="error">{error}</Notice>}{notice && <Notice tone="success">{notice}</Notice>}<DocumentInbox history={history} openId={review?.record_id ?? null} onOpen={openReview} onDelete={(id) => void handleDelete(id)} /></section>}
    </main>
  </div>
}

export default App
