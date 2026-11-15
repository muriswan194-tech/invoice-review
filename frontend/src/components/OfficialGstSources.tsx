import { useEffect, useState } from 'react'

import { fetchGstSources, type GstSource } from '../lib/api'

function OfficialGstSources() {
  const [sources, setSources] = useState<GstSource[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchGstSources().then(setSources).catch((caught: unknown) => {
      setError(caught instanceof Error ? caught.message : 'GST sources could not be loaded.')
    })
  }, [])

  return <section className="sources-page" aria-labelledby="sources-title">
    <p className="step-label">Reference library</p>
    <h1 id="sources-title">Official GST sources</h1>
    <p className="page-copy">Use these government and statutory sources when reviewing or updating the desk's screening rules. Links open the source website in a new tab.</p>
    {error && <p className="source-disclaimer">{error}</p>}
    <div className="source-list">{sources.map((source) => <article className="source-card" key={source.id}><div><p className="source-authority">{source.authority} · {source.category}</p><h2>{source.name}</h2><p>{source.purpose}</p><small>Related screening rules: {source.related_rules.join(', ')}</small><small>Last checked: {source.last_checked} · {source.status.replaceAll('_', ' ')}</small><small>Limitation: {source.limitation}</small></div><a href={source.url} target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a></article>)}</div>
    <p className="source-disclaimer">These links are reference material, not a live compliance check. The desk does not provide tax or legal advice, verify active GST registration, or replace an accountant's review.</p>
  </section>
}

export default OfficialGstSources
