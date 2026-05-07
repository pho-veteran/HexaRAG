import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('shows empty-state guidance before the first answer', () => {
    render(<TracePanel trace={null} error={null} />)

    expect(
      screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.'),
    ).toBeInTheDocument()
  })

  it('renders successful trace sections', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-architecture',
              title: 'architecture.md',
              excerpt: 'Current p95 latency sits below the alert threshold.',
              version: undefined,
              recencyNote: 'Stubbed knowledge base note.',
            },
          ],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'success',
              summary: 'Prepared stub observability data',
              input: { question: 'What is PaymentGW latency?' },
              output: { mode: 'stub', latency_p95_ms: 185 },
            },
          ],
          memoryWindow: ['No prior turns in Phase 1 single-turn mode.'],
          groundingNotes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
          uncertainty: 'Live systems are not wired in this slice.',
        }}
        error={null}
      />,
    )

    expect(screen.getByText('architecture.md')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
    expect(screen.getByText('No prior turns in Phase 1 single-turn mode.')).toBeInTheDocument()
    expect(screen.getByText('Live systems are not wired in this slice.')).toBeInTheDocument()
  })

  it('renders degraded trace sections when the backend returns a fallback answer', () => {
    render(
      <TracePanel
        trace={{
          citations: [],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'error',
              summary: 'Live monitoring call failed.',
              input: { question: 'What is NotificationSvc status?' },
              output: null,
            },
          ],
          memoryWindow: ['What is PaymentGW latency?', 'Stub answer for: What is PaymentGW latency?'],
          groundingNotes: ['Returned fallback answer because the live tool step failed.'],
          uncertainty: 'Live monitoring data is temporarily unavailable.',
        }}
        error={null}
      />,
    )

    expect(screen.getByText('Tool calls')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Live monitoring call failed.')).toBeInTheDocument()
    expect(screen.getByText('Returned fallback answer because the live tool step failed.')).toBeInTheDocument()
    expect(screen.getByText('Live monitoring data is temporarily unavailable.')).toBeInTheDocument()
  })

  it('renders failed-request details when the API call fails', () => {
    render(
      <TracePanel
        trace={null}
        error={{
          message: 'Unable to generate stub response.',
          request: {
            sessionId: 'phase1-session',
            message: 'trigger failure',
          },
          details: ['Stub failure requested for UI error-state coverage.'],
        }}
      />,
    )

    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
