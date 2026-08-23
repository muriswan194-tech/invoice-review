/** Layout-shaped placeholder shown while the pipeline runs. */
function ProcessingSkeleton() {
  return (
    <div className="skeleton-stack" aria-hidden="true">
      <div className="skeleton half" />
      <div className="skeleton tall wide" />
      <div className="skeleton wide" />
      <div className="skeleton two-thirds" />
      <div className="skeleton wide" />
      <div className="skeleton half" />
    </div>
  )
}

export default ProcessingSkeleton
