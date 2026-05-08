import type { ChatErrorState, TracePanelTab, TracePayload } from '../../types/chat'

import { buildTraceNarrative } from './buildTraceNarrative'

interface TracePanelProps {
  trace: TracePayload | null
  error: ChatErrorState | null
  traceLabel: string | null
  activeTab: TracePanelTab
  onTabChange: (tab: TracePanelTab) => void
  onOpenMockup: () => void
}

export function TracePanel({
  trace,
  error,
  traceLabel,
  activeTab,
  onTabChange,
  onOpenMockup,
}: TracePanelProps) {
  const headerCopy = error
    ? 'Showing request error details.'
    : traceLabel
      ? `Inspecting ${traceLabel}.`
      : 'Always visible for every answer.'

  const isObservability = activeTab === 'observability'
  const narrativeSteps = trace ? buildTraceNarrative(trace) : []

  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Inspection console</h2>
        <p>{headerCopy}</p>
      </header>

      <div className="trace-tabs" role="tablist" aria-label="Inspection views">
        <button
          type="button"
          role="tab"
          aria-selected={isObservability}
          className={`trace-tab${isObservability ? ' trace-tab--active' : ''}`}
          onClick={() => onTabChange('observability')}
        >
          Observability
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isObservability}
          className={`trace-tab${!isObservability ? ' trace-tab--active' : ''}`}
          onClick={() => onTabChange('thinking')}
        >
          Thinking process
        </button>
      </div>

      {isObservability ? (
        error ? (
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

            {trace.conflictResolution ? (
              <section className="trace-section">
                <h3>Conflict resolution</h3>
                <p>
                  <strong>Chosen source:</strong> {trace.conflictResolution.chosenSource}
                </p>
                <p>{trace.conflictResolution.rationale}</p>
                {trace.conflictResolution.competingSources.length > 0 ? (
                  <ul className="trace-list">
                    {trace.conflictResolution.competingSources.map((source, index) => (
                      <li key={`${source}-${index}`}>{source}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}

            {trace.uncertainty ? (
              <section className="trace-section">
                <h3>Uncertainty</h3>
                <p>{trace.uncertainty}</p>
              </section>
            ) : null}
          </>
        ) : (
          <p className="trace-empty">Select a response to inspect evidence and explanation.</p>
        )
      ) : trace ? (
        <section className="trace-section trace-section--narrative">
          <h3>How the answer was formed</h3>
          <ol className="trace-narrative">
            {narrativeSteps.map((step) => (
              <li key={step.id} className="trace-step">
                <span className="trace-step__title">{step.title}</span>
                <p>{step.detail}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : (
        <p className="trace-empty">Select a response to inspect evidence and explanation.</p>
      )}

      <button type="button" className="trace-mockup-trigger" onClick={onOpenMockup}>
        Open frontend mockup
      </button>
    </div>
  )
}
