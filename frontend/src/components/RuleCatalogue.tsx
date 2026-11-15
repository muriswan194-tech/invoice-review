import { useState } from 'react'

type Rule = {
  id: string
  name: string
  category: string
  severity: 'error' | 'warning'
  fields: string
  logic: string
  route: string
  nextAction: string
  source: string
  limitation: string
}

const STORAGE_KEY = 'gst-invoice-screening-profile-2026-09'
const POLICY_VERSION = 'b2b-screening-2026-09'

const DEFAULT_RULES: Rule[] = [
  { id: 'required_particulars', name: 'Core B2B invoice particulars', category: 'GST screening profile', severity: 'error', fields: 'supplier GSTIN, recipient GSTIN, invoice number/date, HSN/SAC, taxable value, GST breakup, total', logic: 'For the registered-recipient B2B profile, mark an absent core particular as missing.', route: 'Supplier clarification', nextAction: 'Ask for a corrected invoice containing the missing particular.', source: 'CGST Rules, Rule 46', limitation: 'The screen does not assess every Rule 46 particular or every invoice type.' },
  { id: 'gstins', name: 'GSTIN local format check', category: 'GST identity', severity: 'error', fields: 'supplier_gstin, buyer_gstin', logic: 'Validate GSTIN structure and checksum locally when a GSTIN is present.', route: 'Supplier clarification', nextAction: 'Confirm or correct the GSTIN shown on the invoice.', source: 'GST Portal / CBIC reference material', limitation: 'A checksum does not prove that a registration is active.' },
  { id: 'gst_arithmetic', name: 'GST arithmetic reconciliation', category: 'GST arithmetic', severity: 'error', fields: 'taxable_value, cgst, sgst_or_utgst, igst, cess, total', logic: 'Reconcile taxable value plus available GST components to the invoice total within ₹0.01.', route: 'Supplier clarification', nextAction: 'Request a corrected invoice or explanation of the difference.', source: 'CGST Rules, Rule 46', limitation: 'Arithmetic agreement does not prove tax correctness.' },
  { id: 'tax_structure', name: 'Conditional tax structure checks', category: 'GST tax structure', severity: 'warning', fields: 'cgst, sgst_or_utgst, igst, place_of_supply, reverse_charge', logic: 'Place of supply is applicable when IGST is detected. Flag mixed intra-State and inter-State taxes. Show an absent reverse-charge declaration for review.', route: 'Supplier clarification', nextAction: 'Compare the source invoice and confirm the applicable tax structure.', source: 'CGST Rules, Rule 46', limitation: 'The screen does not determine supply type, tax liability, or reverse-charge applicability.' },
  { id: 'extraction_confidence', name: 'Extraction quality evidence', category: 'Evidence quality', severity: 'warning', fields: 'primary extraction confidence', logic: 'Show low confidence as a prompt to compare the source invoice.', route: 'Reviewer', nextAction: 'Verify the extracted particulars against the original document.', source: 'Application evidence policy', limitation: 'Confidence is not a GST compliance conclusion.' },
]

function loadRules(): Rule[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return JSON.parse(stored) as Rule[]
  } catch { /* Use the documented defaults when local storage is unavailable. */ }
  return DEFAULT_RULES
}

function RuleCatalogue() {
  const [rules, setRules] = useState<Rule[]>(loadRules)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [draft, setDraft] = useState<Rule | null>(null)
  const [saved, setSaved] = useState(false)

  function updateDraft(field: keyof Rule, value: string) {
    if (draft) setDraft({ ...draft, [field]: value })
  }

  function startEdit(rule: Rule) {
    setEditingId(rule.id); setDraft({ ...rule }); setSaved(false)
  }

  function saveDraft() {
    if (!draft) return
    const next = rules.map((rule) => rule.id === draft.id ? draft : rule)
    setRules(next); localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); setEditingId(null); setDraft(null); setSaved(true)
  }

  function resetRules() {
    setRules(DEFAULT_RULES); localStorage.removeItem(STORAGE_KEY); setEditingId(null); setDraft(null); setSaved(true)
  }

  return <section className="rules-page" aria-labelledby="rules-title">
    <div className="rules-head"><div><p className="step-label">Policy reference</p><h1 id="rules-title">GST rule catalogue</h1><p className="page-copy">Maintain the human-readable policy behind the desk's exception explanations. The executable GST checks remain in the backend and are not changed by editing this catalogue.</p></div><span className="policy-version">{POLICY_VERSION}</span></div>
    <div className="rules-toolbar"><span>{rules.length} screening rules</span><button type="button" className="button-secondary button-small" onClick={resetRules}>Reset catalogue</button>{saved && <small>Saved locally in this browser.</small>}</div>
    <div className="rules-list">{rules.map((rule) => editingId === rule.id && draft ? <form className="rule-editor" key={rule.id} onSubmit={(event) => { event.preventDefault(); saveDraft() }}><div className="rule-editor-head"><strong>{draft.id}</strong><button type="button" className="button-quiet" onClick={() => { setEditingId(null); setDraft(null) }}>Cancel</button></div>{(['name', 'category', 'fields', 'logic', 'route', 'nextAction', 'source', 'limitation'] as const).map((field) => <label key={field}>{field === 'nextAction' ? 'Next action' : field.charAt(0).toUpperCase() + field.slice(1)}<textarea value={draft[field]} onChange={(event) => updateDraft(field, event.target.value)} rows={field === 'logic' || field === 'limitation' ? 3 : 2} /></label>)}<label>Severity<select value={draft.severity} onChange={(event) => updateDraft('severity', event.target.value)}><option value="error">Error</option><option value="warning">Warning</option></select></label><button type="submit" className="button-primary">Save rule metadata</button></form> : <article className={`rule-card ${rule.severity}`} key={rule.id}><div className="rule-card-top"><div><span className="rule-category">{rule.category}</span><h2>{rule.name}</h2><code>{rule.id}</code></div><div className="rule-card-actions"><span className={`rule-severity ${rule.severity}`}>{rule.severity}</span><button type="button" className="button-secondary button-small" onClick={() => startEdit(rule)}>Edit</button></div></div><dl className="rule-details"><div><dt>Fields</dt><dd>{rule.fields}</dd></div><div><dt>Logic</dt><dd>{rule.logic}</dd></div><div><dt>Route</dt><dd>{rule.route}</dd></div><div><dt>Next action</dt><dd>{rule.nextAction}</dd></div><div><dt>Source</dt><dd>{rule.source}</dd></div><div><dt>Limitation</dt><dd>{rule.limitation}</dd></div></dl></article>)}</div>
    <p className="source-disclaimer">This catalogue is a policy reference and local browser draft. It does not provide tax or legal advice. A qualified reviewer must approve changes before they become executable policy.</p>
  </section>
}

export default RuleCatalogue
