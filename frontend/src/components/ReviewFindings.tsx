import type { Review } from '../lib/api'

type Props = {
  review: Review
}

function vatDetail(value: boolean | null | undefined): string {
  if (value === null || value === undefined) return 'missing'
  return value ? 'valid' : 'invalid'
}

/** Coded policy findings first, then the raw check detail behind them. */
function ReviewFindings({ review }: Props) {
  const errorCount = review.issues.filter((issue) => issue.severity === 'error').length
  const warningCount = review.issues.length - errorCount

  return (
    <>
      {review.advisor && (
        <section className="block advisor-card" aria-labelledby="advisor-heading">
          <div className="block-head">
            <h3 id="advisor-heading">AI review advisor</h3>
            <span className="block-count">{review.advisor.recommendation.replaceAll('_', ' ')}</span>
          </div>
          <p>{review.advisor.summary}</p>
          <ul>
            {review.advisor.reasons.map((reason) => <li key={reason}>{reason}</li>)}
          </ul>
          {review.advisor.questions_for_reviewer.length > 0 && (
            <p className="advisor-questions">
              Reviewer questions: {review.advisor.questions_for_reviewer.join(' ')}
            </p>
          )}
          <small>The advisor explains evidence only; Northstar rules and the reviewer control approval.</small>
        </section>
      )}
      <section className="block" aria-labelledby="issues-heading">
        <div className="block-head">
          <h3 id="issues-heading">Policy issues</h3>
          <span className="block-count">
            {review.issues.length === 0
              ? 'None open'
              : `${errorCount} blocking / ${warningCount} advisory`}
          </span>
        </div>

        {review.issues.length === 0 ? (
          <p className="notice notice-success">
            <span>Every Northstar rule passed for this document.</span>
          </p>
        ) : (
          <div>
            {review.issues.map((issue) => (
              <div className={`issue-row ${issue.severity}`} key={issue.code}>
                <span>
                  <b className={`dot ${issue.severity === 'error' ? 'failed' : 'warning'}`} aria-hidden="true" />
                  {issue.code}
                </span>
                <strong>{issue.severity === 'error' ? 'blocking' : 'advisory'}</strong>
                <small>{issue.message}</small>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="block" aria-labelledby="checks-heading">
        <div className="block-head">
          <h3 id="checks-heading">Deterministic checks</h3>
          <span className="block-count">{Object.keys(review.checks).length} run</span>
        </div>

        <div>
          {Object.entries(review.checks).map(([name, check]) => (
            <div className="check-row" key={name}>
              <span>
                <b className={`dot ${check.status}`} aria-hidden="true" />
                {name.replaceAll('_', ' ')}
              </span>
              <strong className={check.status}>{check.status}</strong>
              <small>{check.message}</small>
              {name === 'vat' && (
                <small className="check-detail">
                  supplier {vatDetail(check.supplier_valid)} / customer {vatDetail(check.customer_valid)}
                  {check.customer_matches === false && ' / not Northstar'}
                </small>
              )}
              {name === 'confidence' && check.confidence !== null && check.confidence !== undefined && (
                <small className="check-detail">
                  primary extraction {Math.round(check.confidence * 100)}%
                </small>
              )}
              {name === 'total' && check.difference && (
                <small className="check-detail">difference {check.difference}</small>
              )}
            </div>
          ))}
        </div>
      </section>
    </>
  )
}

export default ReviewFindings
