import type { CheckResult, Issue, Review } from '../lib/api'
import { fieldLabel } from '../lib/fields'
import { buildMissingDataChecklist, hasMissingDataChecklistItems, missingDataChecklistFilename } from '../lib/missingDataChecklist'
type Props = {
  review: Review
}

function isMissingParticular(issue: Issue): boolean {
  return issue.code.endsWith('_required') && issue.field !== null
}

function findingLabel(issue: Issue): string {
  if (isMissingParticular(issue)) return fieldLabel(issue.field ?? 'Invoice particular')
  return {
    supplier_gstin_invalid: 'Supplier GSTIN appears invalid',
    buyer_gstin_invalid: 'Recipient GSTIN appears invalid',
    invoice_total_mismatch: 'Invoice total does not reconcile',
    tax_structure_inconsistent: 'GST tax structure needs review',
  }[issue.code] ?? issue.message
}

function checkLabel(name: string): string {
  return {
    screening_profile: 'Screening profile',
    gstins: 'GSTIN format check',
    gst_arithmetic: 'GST arithmetic',
    tax_structure: 'Tax structure',
    extraction_confidence: 'Extraction quality',
  }[name] ?? name.replaceAll('_', ' ')
}

function checkSummary(name: string, check: CheckResult): string {
  if (name === 'gstins') {
    const supplier = check.supplier_valid === null ? 'Supplier GSTIN is missing' : check.supplier_valid ? null : 'Supplier GSTIN needs verification'
    const recipient = check.buyer_valid === null ? 'recipient GSTIN is missing' : check.buyer_valid ? null : 'recipient GSTIN needs verification'
    return [supplier, recipient].filter(Boolean).join('; ') || 'Both GSTINs pass the local format check.'
  }
  if (name === 'extraction_confidence' && check.confidence !== null && check.confidence !== undefined) {
    return `Document extraction confidence: ${Math.round(check.confidence * 100)}%.`
  }
  return check.message
}

function checkState(name: string, check: CheckResult): { label: string; tone: string; icon: string } {
  if (name === 'tax_structure' && check.status === 'warning') return { label: 'Needs review', tone: 'warning', icon: '!' }
  if (check.status === 'passed') return { label: 'Checked', tone: 'passed', icon: '✓' }
  if (check.status === 'failed') return { label: 'Needs review', tone: 'failed', icon: '!' }
  return { label: 'Needs review', tone: 'warning', icon: '!' }
}

/** Coded policy findings first, then the raw check detail behind them. */
function ReviewFindings({ review }: Props) {
  const missingParticulars = review.issues.filter(isMissingParticular)
  const verificationFindings = review.issues.filter((issue) => !isMissingParticular(issue))
  const canDownloadChecklist = hasMissingDataChecklistItems(review)
  const profile = review.checks.screening_profile
  const profileAssessments = profile?.assessments
  const placeOfSupply = profileAssessments?.place_of_supply
  const reverseCharge = profileAssessments?.reverse_charge

  function downloadMissingDataChecklist() {
    const blob = new Blob([buildMissingDataChecklist(review)], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = missingDataChecklistFilename(review)
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      {profile && <section className="screening-profile" aria-label="GST screening profile">
        <div><span>Screening profile</span><strong>{profile.name ?? 'Standard registered-recipient B2B tax invoice'}</strong><p>Core particulars are applicable. Place of supply is applicable only when IGST is detected. This screen does not assess every Rule 46 particular.</p></div>
        <dl><div><dt>Core particulars</dt><dd>Applicable</dd></div><div><dt>Place of supply</dt><dd>{placeOfSupply?.applicability === 'applicable' ? `Applicable · ${placeOfSupply.state}` : 'Not applicable'}</dd></div><div><dt>Reverse charge</dt><dd>{reverseCharge?.state === 'missing' ? 'Applicable · missing' : 'Applicable · present'}</dd></div></dl>
      </section>}
      <section id="policy-issues" className="block" aria-labelledby="issues-heading">
        <div className="block-head">
          <div>
            <h3 id="issues-heading">GST invoice requirements</h3>
            <p className="block-description">Review the missing particulars and values that need verification.</p>
          </div>
          <span className="block-count">
              {review.issues.length === 0
                ? 'None open'
                : `${review.issues.length} item${review.issues.length === 1 ? '' : 's'} need attention`}
          </span>
        </div>

        {review.issues.length === 0 ? (
          <p className="notice notice-success">
            <span>All checked GST invoice requirements are present on visible evidence.</span>
          </p>
        ) : (
          <div className="finding-groups">
            {missingParticulars.length > 0 && <section className="finding-group missing" aria-labelledby="missing-particulars-heading">
              <div className="finding-group-head"><div><h4 id="missing-particulars-heading">Missing from the invoice</h4><p>Ask the supplier for a corrected invoice containing these particulars.</p></div>{canDownloadChecklist && <button type="button" className="button-secondary button-small" onClick={downloadMissingDataChecklist}>Download checklist</button>}</div>
              <ul>{missingParticulars.map((issue) => <li key={issue.code}><b className="dot failed" aria-hidden="true" />{findingLabel(issue)}</li>)}</ul>
            </section>}
            {verificationFindings.length > 0 && <section className="finding-group verify" aria-labelledby="verification-heading">
              <div className="finding-group-head"><div><h4 id="verification-heading">Needs verification</h4><p>Compare these values with the original invoice before relying on them.</p></div></div>
              <div className="verification-list">{verificationFindings.map((issue) => <article key={issue.code}><h5><b className={`dot ${issue.severity === 'error' ? 'failed' : 'warning'}`} aria-hidden="true" />{findingLabel(issue)}</h5><p>{issue.message}</p>{issue.code.includes('gstin') && <small>Local format/checksum check only; this is not a government registration lookup.</small>}</article>)}</div>
            </section>}
          </div>
        )}
      </section>

      <section id="deterministic-checks" className="check-glass" aria-labelledby="checks-heading">
        <div className="check-glass-head"><div><h3 id="checks-heading">How this invoice was checked</h3><p>Review evidence behind the GST requirements result.</p></div></div>
        <div className="check-summary-list">
          {Object.entries(review.checks).filter(([name]) => name !== 'screening_profile' && name !== 'required_particulars' && name !== 'required').map(([name, check]) => {
            const state = checkState(name, check)
            return <article className={`check-summary ${state.tone}`} key={name}>
              <span className="check-icon" aria-hidden="true">{state.icon}</span><div><h4>{checkLabel(name)}</h4><p>{checkSummary(name, check)}</p></div><span className="check-state">{state.label}</span>
            </article>
          })}
        </div>
        <details className="check-details"><summary>View technical details</summary><div>{Object.entries(review.checks).filter(([name]) => name !== 'screening_profile').map(([name, check]) => <p key={name}><strong>{checkLabel(name)}:</strong> {check.message}{name === 'gst_arithmetic' && check.difference ? ` Difference: ${check.difference}.` : ''}</p>)}</div></details>
      </section>
    </>
  )
}

export default ReviewFindings
