import type { ChatErrorState, TracePayload } from '../../types/chat'

interface TracePanelProps {
  trace: TracePayload | null
  error: ChatErrorState | null
}

export function TracePanel({ trace, error }: TracePanelProps) {
  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Observability</h2>
        <p>Always visible for every answer.</p>
      </header>

      {error ? (
        <>
          <section className="trace-section">
          <h3>Last request</h3>
          <p>
            <strong>Session:</strong> {error.request.sessionId}
          </p>
          <p>
            <strong>Message:</strong> {error.request.message}
          </p>
        </section>

          <section className="trace-section">
            <h3>Error details</h3>
            <p>{error.message}</p>
            <ul className="trace-list">
              {error.details.map((detail, index) => (
                <li key={`${detail}-${index}`}>{detail}</li>
              ))}
            </ul>
          </section>
        </>
      ) : trace ? (
        <>
          <section className="trace-section">
            <h3>Sources</h3>
            <ul className="trace-list">
              {trace.citations.map((citation) => (
                <li key={citation.sourceId}>{citation.title}</li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Tool calls</h3>
            <ul className="trace-list">
              {trace.toolCalls.map((tool, index) => (
                <li key={`${tool.name}-${index}`}>
                  {tool.name}: {tool.summary}
                </li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Memory</h3>
            <ul className="trace-list">
              {trace.memoryWindow.map((entry, index) => (
                <li key={`${entry}-${index}`}>{entry}</li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Grounding</h3>
            <ul className="trace-list">
              {trace.groundingNotes.map((note, index) => (
                <li key={`${note}-${index}`}>{note}</li>
              ))}
            </ul>
          </section>

          {trace.uncertainty ? (
            <section className="trace-section">
              <h3>Uncertainty</h3>
              <p>{trace.uncertainty}</p>
            </section>
          ) : null}
        </>
      ) : (
        <p className="trace-empty">Send a question to inspect retrieval, tools, memory, and grounding.</p>
      )}
    </div>
  )
}
