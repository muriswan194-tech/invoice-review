import { reviewDocumentUrl } from '../lib/api'

type Props = {
  recordId: number
  filename: string
  savedName: string
}

/** Shows the original uploaded evidence without exposing the storage path. */
function DocumentPreview({ recordId, filename, savedName }: Props) {
  const source = reviewDocumentUrl(recordId)
  const isPdf = savedName.toLowerCase().endsWith('.pdf')

  return (
    <aside id="source-document" className="document-preview" aria-labelledby="document-preview-title">
      <div className="document-preview-head">
        <div>
          <p className="eyebrow">Source invoice</p>
          <h2 id="document-preview-title">Verify against the original</h2>
          <span className="document-name" title={filename}>{filename}</span>
        </div>
        <div className="document-actions" aria-label="Source document actions">
          <a href={source} download>Download</a>
          <a href={source} target="_blank" rel="noreferrer">Open ↗</a>
        </div>
      </div>
      <p className="document-helper">Compare this source with the extracted particulars.</p>
      <div className="document-frame">
        {isPdf
          ? <iframe title={`Original document: ${filename}`} src={source} />
          : <img src={source} alt={`Original document: ${filename}`} />}
      </div>
    </aside>
  )
}

export default DocumentPreview
