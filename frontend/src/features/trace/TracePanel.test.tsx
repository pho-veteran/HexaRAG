import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('renders inspection tabs and empty-state guidance before the first answer', () => {
    render(
      <TracePanel
        trace={null}
        error={null}
        traceLabel={null}
        activeTab="observability"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByText('Select a response to inspect evidence and explanation.')).toBeInTheDocument()
  })

  it('renders observability sections when the observability tab is active', () => {
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
          inlineCitations: [],
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
        traceLabel="Response 2"
        activeTab="observability"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('Inspecting Response 2.')).toBeInTheDocument()
    expect(screen.getByText('architecture.md')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
  })

  it('renders curated narrative steps when the thinking-process tab is active', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-monitoring',
              title: 'monitoring.md',
              excerpt: 'PaymentGW latency p95 is 185 ms.',
              version: undefined,
              recencyNote: undefined,
            },
          ],
          inlineCitations: [],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'success',
              summary: 'Fetched current PaymentGW metrics',
              input: { question: 'What is PaymentGW latency?' },
              output: { latency_p95_ms: 185 },
            },
          ],
          memoryWindow: ['Who owns the Notifications service?'],
          groundingNotes: ['Used live monitoring data.'],
          uncertainty: null,
        }}
        error={null}
        traceLabel="Response 2"
        activeTab="thinking"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('How the answer was formed')).toBeInTheDocument()
    expect(screen.getByText('Checked sources')).toBeInTheDocument()
    expect(screen.getByText('Ran tools')).toBeInTheDocument()
    expect(screen.getByText('Used session context')).toBeInTheDocument()
    expect(screen.getByText('Grounded answer')).toBeInTheDocument()
  })

  it('renders failed-request details on the observability tab', () => {
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
        traceLabel={null}
        activeTab="observability"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
