import { useEffect, useState } from 'react'

import DocumentInbox from './components/DocumentInbox'
import DocumentPreview from './components/DocumentPreview'
import FieldEditor from './components/FieldEditor'
import OfficialGstSources from './components/OfficialGstSources'
import ReviewFindings from './components/ReviewFindings'
import RuleCatalogue from './components/RuleCatalogue'
import UploadStep from './components/UploadStep'
import Notice from './components/ui/Notice'
import Tag from './components/ui/Tag'
import { deleteReview, fetchHistory, openDemoReview, saveCorrections, uploadDocumentWithProgress, type ProcessingStage, type Review } from './lib/api'

type Screen = 'landing' | 'upload' | 'processing' | 'review' | 'history' | 'sources' | 'rules'

const PROCESSING_STEPS: { id: ProcessingStage; name: string; description: string }[] = [
  { id: 'extract', name: 'Extract invoice particulars', description: 'Reading with Document Intelligence; an AI fallback runs only if core fields are unavailable.' },
  { id: 'validate', name: 'Check GST requirements', description: 'Applying applicable GST particulars and local consistency checks.' },
]

function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [review, setReview] = useState<Review | null>(null)
  const [history, setHistory] = useState<Review[]>([])
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isOpeningDemo, setIsOpeningDemo] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [activeProcessingStage, setActiveProcessingStage] = useState<ProcessingStage>('extract')

  useEffect(() => { void refreshHistory() }, [])

  async function refreshHistory() { setHistory(await fetchHistory().catch(() => [])) }
  function reportError(caught: unknown, fallback: string) { setError(caught instanceof Error ? caught.message : fallback) }
  function beginNewReview() { setReview(null); setSelectedFile(null); setError(null); setNotice(null); setActiveProcessingStage('extract'); setScreen('upload') }

  async function runReview() {
    if (!selectedFile) return
    setError(null); setNotice(null); setScreen('processing'); setIsProcessing(true)
    try {
      setReview(await uploadDocumentWithProgress(selectedFile, 'invoice', setActiveProcessingStage))
      await refreshHistory(); setScreen('review')
    } catch (caught) { reportError(caught, 'The invoice could not be processed.'); setScreen('upload') } finally { setIsProcessing(false) }
  }

  async function openDemo() {
    setIsOpeningDemo(true); setError(null); setNotice(null)
    try { setReview(await openDemoReview()); await refreshHistory(); setScreen('review') }
    catch (caught) { reportError(caught, 'The local demo could not be opened.') } finally { setIsOpeningDemo(false) }
  }

  async function handleCorrections(fields: Record<string, string | null>) {
    if (!review) return false
    setIsSaving(true); setError(null)
    try { setReview(await saveCorrections(review.record_id, fields)); await refreshHistory(); setNotice('Saved changes and reran the GST checks.'); return true }
    catch (caught) { reportError(caught, 'The corrections could not be saved.'); return false } finally { setIsSaving(false) }
  }

  async function handleDelete(recordId: number) {
    if (!window.confirm('Delete this locally stored review and its upload?')) return
    try { await deleteReview(recordId); await refreshHistory(); if (review?.record_id === recordId) setReview(null); setNotice('Review deleted.') }
    catch (caught) { reportError(caught, 'The review could not be deleted.') }
  }

  function openReview(record: Review) { setReview(record); setError(null); setNotice(null); setScreen('review') }

  function goTo(screenName: Screen) { setIsMenuOpen(false); setScreen(screenName) }

  return <div className="app-shell">
    <header className="app-nav"><button type="button" className="brand-link" onClick={() => goTo('landing')}><strong>GST Invoice Requirements Reviewer</strong><span>Generic GST invoice completeness review</span></button><div className="menu-wrap"><button type="button" className="menu-button" aria-label="Open workspace menu" aria-expanded={isMenuOpen} onClick={() => setIsMenuOpen(!isMenuOpen)}><span /><span /><span /></button>{isMenuOpen && <nav className="menu-panel" aria-label="Workspace menu"><button type="button" onClick={() => goTo('history')}>History</button><button type="button" onClick={() => goTo('sources')}>Official GST sources</button><button type="button" onClick={() => goTo('rules')}>GST requirements</button></nav>}</div></header>
    <main className={screen === 'landing' ? 'landing-main' : screen === 'review' ? 'workflow-main review-main' : 'workflow-main'}>
      {screen === 'landing' && <section className="landing-card" aria-labelledby="landing-title"><p className="org-label">GST invoice completeness review</p><h1 id="landing-title">Check applicable GST invoice particulars</h1><p className="landing-copy">Upload an invoice to identify missing GST particulars and local inconsistencies. This tool does not make payment, accounting, or tax-advice decisions.</p><div className="landing-actions"><button type="button" className="button-primary" onClick={beginNewReview}>Review an invoice</button><button type="button" className="button-secondary" onClick={() => void openDemo()} disabled={isOpeningDemo}>{isOpeningDemo ? 'Opening demo…' : 'Open fictional demo'}</button></div><div className="how-it-works"><h2>How it works</h2>{['Upload an invoice', 'Extract visible particulars', 'Review GST requirements'].map((label, index) => <div className="how-row" key={label}><span>{index + 1}</span><strong>{label}</strong><p>{['Choose a PDF, PNG, or JPEG invoice.', 'Compare extracted values with the original document.', 'See only the applicable GST requirements and consistency checks.'][index]}</p></div>)}</div></section>}
      {screen === 'upload' && <section className="workflow-column" aria-labelledby="upload-title"><button type="button" className="back-link" onClick={() => setScreen('landing')}>Back</button><p className="step-label">Step 1 of 3</p><h1 id="upload-title">Choose a GST invoice</h1><p className="page-copy">Live documents are sent to Azure only when you select Run review.</p>{error && <Notice tone="error">{error}</Notice>}<UploadStep selectedFile={selectedFile} onFile={setSelectedFile} onClear={() => setSelectedFile(null)} /><div className="workflow-actions"><button type="button" className="button-secondary" disabled={isOpeningDemo} onClick={() => void openDemo()}>Use fictional demo</button><button type="button" className="button-primary" disabled={!selectedFile} onClick={() => void runReview()}>Run review</button></div></section>}
      {screen === 'processing' && <section className="processing-card" aria-live="polite" aria-labelledby="processing-title"><div className="processing-orbit" aria-hidden="true" /><p className="step-label">Step 2 of 3</p><h1 id="processing-title">Reviewing invoice</h1><p className="page-copy">Working through the GST invoice review for {selectedFile?.name ?? 'your document'}.</p><ol className="pipeline-list">{PROCESSING_STEPS.map(({ id, name, description }, index) => { const activeIndex = PROCESSING_STEPS.findIndex((step) => step.id === activeProcessingStage); const state = index < activeIndex ? 'completed' : index === activeIndex && isProcessing ? 'active' : ''; return <li className={state} key={id}><span>{index + 1}</span><div><strong>{name}</strong><p>{description}</p></div></li> })}</ol></section>}
      {screen === 'review' && review && <section className="review-column" aria-labelledby="review-title"><div className="review-intro"><div><p className="step-label">Step 3 of 3</p><h1 id="review-title">GST invoice review</h1><p className="page-copy">{review.filename}</p></div><Tag status={review.issues.some((issue) => issue.severity === 'error') ? 'needs_review' : 'ready'}>{review.issues.some((issue) => issue.severity === 'error') ? 'needs correction' : 'visible particulars complete'}</Tag></div>{error && <Notice tone="error">{error}</Notice>}{notice && <Notice tone="success">{notice}</Notice>}{review.is_demo && <Notice tone="warning">Fictional demo data. It is a sample only and does not send an Azure request.</Notice>}<div className="review-outcome"><ReviewFindings review={review} /></div><div className="review-workspace"><DocumentPreview recordId={review.record_id} filename={review.filename} savedName={review.saved_name} /><div className="review-details"><FieldEditor review={review} isSaving={isSaving} onSave={handleCorrections} /></div></div></section>}
      {screen === 'history' && <section className="history-page" aria-labelledby="history-title"><div className="history-page-head"><div><h1 id="history-title">Review history</h1><p className="page-copy">Locally saved GST invoice reviews, newest first.</p></div><button type="button" className="button-primary" onClick={beginNewReview}>New review</button></div>{error && <Notice tone="error">{error}</Notice>}{notice && <Notice tone="success">{notice}</Notice>}<DocumentInbox history={history} openId={review?.record_id ?? null} onOpen={openReview} onDelete={(id) => void handleDelete(id)} /></section>}
      {screen === 'sources' && <OfficialGstSources />}{screen === 'rules' && <RuleCatalogue />}
    </main>
  </div>
}

export default App
