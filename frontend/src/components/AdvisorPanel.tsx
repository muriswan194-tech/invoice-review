import type { AdvisorRecommendation } from '../lib/api'

type Props = {
  advisor: AdvisorRecommendation
}

/** Shows the Foundry advisor's recommendation. It never overrides the human gate. */
function AdvisorPanel({ advisor }: Props) {
  const severityClass =
    advisor.recommendation === 'APPROVE'
      ? 'advisor-approve'
      : advisor.recommendation === 'CORRECTION_REQUIRED'
        ? 'advisor-correction'
        : 'advisor-escalate'

  return (
    <section className="advisor-panel">
      <div className="advisor-header">
        <p className="eyebrow">AI Advisor</p>
        <span className={`advisor-badge ${severityClass}`}>
          {advisor.recommendation.replaceAll('_', ' ')}
        </span>
      </div>

      <p className="advisor-summary">{advisor.summary}</p>

      {advisor.reasons.length > 0 && (
        <div className="advisor-section">
          <p className="eyebrow">Reasons</p>
          <ul className="advisor-list">
            {advisor.reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {advisor.questions_for_reviewer.length > 0 && (
        <div className="advisor-section">
          <p className="eyebrow">Questions for you</p>
          <ul className="advisor-list">
            {advisor.questions_for_reviewer.map((q, idx) => (
              <li key={idx}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="advisor-disclaimer">
        This is AI-generated guidance. The final decision is yours.
      </p>
    </section>
  )
}

export default AdvisorPanel