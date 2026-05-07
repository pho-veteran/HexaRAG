import type { Citation, InlineCitationAnchor } from '../../types/chat'

interface InlineCitationTextProps {
  content: string
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  onCitationClick: (sourceId: string) => void
}

function isRenderableAnchor(anchor: InlineCitationAnchor, contentLength: number): boolean {
  return anchor.start >= 0 && anchor.end > anchor.start && anchor.end <= contentLength
}

export function InlineCitationText({ content, citations, inlineCitations, onCitationClick }: InlineCitationTextProps) {
  if (inlineCitations.length === 0) {
    return <p>{content}</p>
  }

  const citationNumbers = new Map(citations.map((citation, index) => [citation.sourceId, index + 1]))
  const anchors = [...inlineCitations].sort((left, right) => left.start - right.start)

  if (anchors.some((anchor) => !isRenderableAnchor(anchor, content.length))) {
    return <p>{content}</p>
  }

  const parts: React.ReactNode[] = []
  let cursor = 0

  anchors.forEach((anchor, anchorIndex) => {
    if (cursor < anchor.start) {
      parts.push(<span key={`text-${anchorIndex}-${cursor}`}>{content.slice(cursor, anchor.start)}</span>)
    }

    parts.push(
      <span key={`anchor-${anchorIndex}`}>
        {content.slice(anchor.start, anchor.end)}
        {anchor.sourceIds.map((sourceId) => {
          const number = citationNumbers.get(sourceId)
          if (!number) {
            return null
          }

          return (
            <button
              key={`${anchor.start}-${sourceId}`}
              type="button"
              className="citation-inline-marker"
              onClick={() => onCitationClick(sourceId)}
            >
              [{number}]
            </button>
          )
        })}
      </span>,
    )

    cursor = anchor.end
  })

  if (cursor < content.length) {
    parts.push(<span key={`tail-${cursor}`}>{content.slice(cursor)}</span>)
  }

  return <p className="assistant-answer">{parts}</p>
}
