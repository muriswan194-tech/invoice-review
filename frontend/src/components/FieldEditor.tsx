import { useState } from 'react'

import type { Review } from '../lib/api'
import { editableFields, fieldLabel, inputValue, sourceLabel } from '../lib/fields'

type Props = {
  review: Review
  isSaving: boolean
  onSave: (fields: Record<string, string | null>) => Promise<boolean>
}

/** Editable projection of the extracted fields, with the source of each value. */
function FieldEditor({ review, isSaving, onSave }: Props) {
  const fields = editableFields(review.document_type)
  const [edits, setEdits] = useState<Record<string, string>>({})

  function valueFor(name: string) {
    return edits[name] ?? inputValue(review.document[name])
  }

  const changed = fields.filter(
    (name) => name in edits && edits[name] !== inputValue(review.document[name]),
  )

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (changed.length === 0) return
    const saved = await onSave(Object.fromEntries(changed.map((name) => [name, edits[name] || null])))
    if (saved) setEdits({})
  }

  return (
    <form className="block" onSubmit={handleSubmit}>
      <div className="block-head">
        <h3>Review extracted fields</h3>
        <span className="block-count">
          {changed.length > 0 ? `${changed.length} unsaved` : `${fields.length} fields`}
        </span>
      </div>

      <div className="field-editor">
        {fields.map((name) => {
          const isEdited = changed.includes(name)
          const isHuman = review.field_sources[name] === 'human'
          return (
            <div
              className={`field-row ${isHuman ? 'is-human' : ''} ${isEdited ? 'is-edited' : ''}`.trim()}
              key={name}
            >
              <label htmlFor={`field-${name}`}>{fieldLabel(name)}</label>
              <input
                id={`field-${name}`}
                value={valueFor(name)}
                onChange={(event) => setEdits({ ...edits, [name]: event.target.value })}
                disabled={!review.can_edit || isSaving}
                placeholder="Not found"
                autoComplete="off"
              />
              <small className="field-source">
                {isEdited ? 'Unsaved change' : sourceLabel(review.field_sources[name])}
              </small>
            </div>
          )
        })}
      </div>

      {review.can_edit ? (
        <div className="editor-actions">
          <button type="submit" disabled={isSaving || changed.length === 0}>
            {isSaving ? 'Saving\u2026' : 'Save and rerun checks'}
          </button>
          {changed.length > 0 && (
            <button type="button" className="button-quiet" onClick={() => setEdits({})} disabled={isSaving}>
              Discard
            </button>
          )}
          <p>Correct anything Azure read incorrectly, then rerun the checks.</p>
        </div>
      ) : (
        <p className="notice notice-quiet">
          <span>This document is decided, so its values are now read-only.</span>
        </p>
      )}
    </form>
  )
}

export default FieldEditor
