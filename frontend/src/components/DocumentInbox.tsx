import type { Review } from '../lib/api'
import Tag from './ui/Tag'

type Props = {
  history: Review[]
  openId: number | null
  onOpen: (review: Review) => void
  onDelete: (recordId: number) => void
}

function documentLabel(record: Review): string {
  const supplier = record.document.supplier_name ?? record.document.merchant_name
  return typeof supplier === 'string' && supplier.trim() !== '' ? supplier : record.filename
}

/** Reviewed documents, newest first, with reopen and delete. */
function DocumentInbox({ history, openId, onOpen, onDelete }: Props) {
  if (history.length === 0) {
    return (
      <div className="empty-state">
        <strong>No documents reviewed yet</strong>
        <p>Upload a supplier invoice or an expense receipt to start the first review.</p>
      </div>
    )
  }

  return (
    <div className="history-list">
      {history.slice(0, 8).map((record) => (
        <div
          className={`history-row ${record.record_id === openId ? 'is-open' : ''}`.trim()}
          key={record.record_id}
        >
          <button
            type="button"
            className="history-open-button"
            onClick={() => onOpen(record)}
            aria-label={`Open the review for ${documentLabel(record)}`}
          >
            {documentLabel(record)}
          </button>
          <Tag status={record.review_status}>{record.review_status.replaceAll('_', ' ')}</Tag>
          <small className="history-meta">
            {record.document_type}
            {record.upload_count > 1 && ` / seen ${record.upload_count}x`}
            {record.issues.length > 0 && ` / ${record.issues.length} issue${record.issues.length === 1 ? '' : 's'}`}
          </small>
          <button
            type="button"
            className="button-danger button-small"
            onClick={() => onDelete(record.record_id)}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}

export default DocumentInbox
