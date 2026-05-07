import type { Citation } from '../../types/chat'

interface CitationDetailModalProps {
  citation: Citation | null
  onClose: () => void
}

export function CitationDetailModal({ citation, onClose }: CitationDetailModalProps) {
  if (citation === null) {
    return null
  }

  const hasMetadata = Boolean(citation.version || citation.recencyNote)

  return (
    <div
      className="citation-modal-backdrop"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <section className="citation-modal" role="dialog" aria-modal="true" aria-label="Citation details">
        <div className="citation-modal__header">
          <div>
            <p className="citation-modal__eyebrow">Source document</p>
            <h2>{citation.title}</h2>
          </div>
          <button type="button" className="citation-modal__close" onClick={onClose}>
            Close citation details
          </button>
        </div>

        <section className="citation-modal__section">
          <h3>Excerpt</h3>
          <p>{citation.excerpt}</p>
        </section>

        {hasMetadata ? (
          <section className="citation-modal__section citation-modal__section--meta">
            <h3>Metadata</h3>
            <ul className="citation-modal__meta">
              {citation.version ? (
                <li>
                  <strong>Version:</strong> {citation.version}
                </li>
              ) : null}
              {citation.recencyNote ? (
                <li>
                  <strong>Recency:</strong> {citation.recencyNote}
                </li>
              ) : null}
            </ul>
          </section>
        ) : null}
      </section>
    </div>
  )
}
