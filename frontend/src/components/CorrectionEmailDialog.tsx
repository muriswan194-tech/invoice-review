import { useState } from 'react'

import type { CorrectionEmail } from '../lib/api'

type Props = {
  draft: CorrectionEmail
  onClose: () => void
}

/** Shows the drafted request with a copy button. The app never sends mail. */
function CorrectionEmailDialog({ draft, onClose }: Props) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`)
    setCopied(true)
  }

  return (
    <section className="draft" aria-labelledby="draft-heading">
      <p className="eyebrow" id="draft-heading">Supplier correction request</p>
      <p className="draft-subject">{draft.subject}</p>
      <textarea value={draft.body} readOnly aria-label="Correction request body" />
      <p className="draft-disclaimer">
        Northstar never sends this for you. Copy the text into your own mail client.
      </p>
      <div className="draft-actions">
        <button type="button" onClick={handleCopy}>
          {copied ? 'Copied to clipboard' : 'Copy request'}
        </button>
        <button type="button" className="button-quiet" onClick={onClose}>
          Close
        </button>
      </div>
    </section>
  )
}

export default CorrectionEmailDialog
