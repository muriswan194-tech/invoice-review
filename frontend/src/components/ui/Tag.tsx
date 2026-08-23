const STATUS_TONE: Record<string, string> = {
  pending: 'tag-pending',
  approved: 'tag-approved',
  rejected: 'tag-rejected',
  correction_requested: 'tag-correction',
}

type Props = {
  children: React.ReactNode
  status?: string
}

/** Square label. Reserved for state, not decoration. */
function Tag({ children, status }: Props) {
  const tone = status ? STATUS_TONE[status] ?? '' : ''
  return <span className={`tag ${tone}`.trim()}>{children}</span>
}

export default Tag
