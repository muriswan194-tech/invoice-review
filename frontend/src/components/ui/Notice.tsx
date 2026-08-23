type Props = {
  tone?: 'error' | 'success' | 'warning' | 'quiet'
  children: React.ReactNode
}

/** Inline status message. Never an alert dialog. */
function Notice({ tone = 'quiet', children }: Props) {
  return (
    <p className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span>{children}</span>
    </p>
  )
}

export default Notice
