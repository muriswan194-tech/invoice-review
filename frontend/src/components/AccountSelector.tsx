import type { GlAccount, Review } from '../lib/api'
import Notice from './ui/Notice'

type Props = {
  review: Review
  accounts: GlAccount[]
  isSaving: boolean
  onSelect: (accountCode: string) => void
}

/** The model suggests an account; the reviewer owns the selection. */
function AccountSelector({ review, accounts, isSaving, onSelect }: Props) {
  const suggestion = review.gl_suggestion
  const hasSuggestion = Boolean(suggestion?.account_code)

  return (
    <section className="block" aria-labelledby="accounting-heading">
      <div className="block-head">
        <h3 id="accounting-heading">General ledger</h3>
        <span className="block-count">
          {review.selected_account_code ? `Selected ${review.selected_account_code}` : 'Not selected'}
        </span>
      </div>

      {hasSuggestion && (
        <div className="account-suggestion">
          <span>Model suggestion</span>
          <strong>
            {suggestion.account_code} — {suggestion.account_name}
          </strong>
          <small>{Math.round(suggestion.confidence * 100)}% confidence. You make the final choice.</small>
        </div>
      )}

      <div className="field-group">
        <label htmlFor="gl-account">Northstar account</label>
        <select
          id="gl-account"
          value={review.selected_account_code ?? ''}
          onChange={(event) => onSelect(event.target.value)}
          disabled={!review.can_edit || isSaving || accounts.length === 0}
        >
          <option value="" disabled>
            Choose an account
          </option>
          {accounts.map((account) => (
            <option key={account.code} value={account.code}>
              {account.code} — {account.name}
            </option>
          ))}
        </select>
      </div>

      {review.selected_account_code === null && review.can_edit && (
        <Notice tone="warning">Select an account before this document can be approved.</Notice>
      )}
    </section>
  )
}

export default AccountSelector
