import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

const baseTrace = {
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
      status: 'success' as const,
      summary: 'Prepared stub observability data',
      input: { question: 'What is PaymentGW latency?' },
      output: { mode: 'stub', latency_p95_ms: 185 },
    },
  ],
  memoryWindow: ['No prior turns in Phase 1 single-turn mode.'],
  groundingNotes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
  uncertainty: 'Live systems are not wired in this slice.',
  conflictResolution: undefined,
  runtime: {
    mode: 'stub',
    provider: 'stub-runtime',
    region: undefined,
    agentId: undefined,
    agentAliasId: undefined,
    model: 'deterministic-stub',
  },
  reasoning: {
    evidenceTypes: ['retrieval', 'tool', 'memory'],
    selectedSources: ['architecture.md'],
    toolBasis: ['monitoring_snapshot'],
    memoryApplied: true,
    memorySummary: 'Used 1 recent conversation item to keep the answer on topic.',
    uncertaintyReason: 'Live systems are not wired in this slice.',
    answerStrategy: 'grounded-answer',
    runtimeLabel: 'deterministic-stub via stub-runtime',
    caveat: 'Live systems are not wired in this slice.',
    sourceSummary: 'Selected 1 source that directly shaped the answer.',
    toolSummary: 'Used 1 tool result in the final answer.',
    explanationSummary: 'The answer combined retrieved evidence, live tool data, and recent conversation context.',
    narrativeFocus: 'evidence-synthesis',
    nextStep: undefined,
    conflictSummary: undefined,
  },
}

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
        trace={baseTrace}
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
    expect(screen.getByText('Uncertainty')).toBeInTheDocument()
    expect(screen.getByText('Live systems are not wired in this slice.')).toBeInTheDocument()
  })

  it('renders contradiction-resolution details when the trace provides them', () => {
    render(
      <TracePanel
        trace={{
          ...baseTrace,
          citations: [
            {
              sourceId: 'doc-v2',
              title: 'api_reference_v2.md',
              excerpt: '1000 rpm',
              version: 'v2',
              recencyNote: undefined,
            },
          ],
          groundingNotes: ['Used the newest API document.'],
          uncertainty: null,
          conflictResolution: {
            chosenSource: 'api_reference_v2.md',
            rationale: 'v2 supersedes archived v1.',
            competingSources: ['api_reference_v1_archived.md'],
          },
        }}
        error={null}
        traceLabel="Response 2"
        activeTab="observability"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('Conflict resolution')).toBeInTheDocument()
    expect(screen.getByText('api_reference_v2.md')).toBeInTheDocument()
    expect(screen.getByText('v2 supersedes archived v1.')).toBeInTheDocument()
  })

  it('renders curated narrative steps when the thinking-process tab is active', () => {
    render(
      <TracePanel
        trace={{
          ...baseTrace,
          citations: [
            {
              sourceId: 'doc-monitoring',
              title: 'monitoring.md',
              excerpt: 'PaymentGW latency p95 is 185 ms.',
              version: undefined,
              recencyNote: undefined,
            },
          ],
          memoryWindow: ['Who owns the Notifications service?'],
          groundingNotes: ['Used live monitoring data.'],
          uncertainty: null,
          conflictResolution: {
            chosenSource: 'monitoring.md',
            rationale: 'Live metrics were newer than the archived dashboard note.',
            competingSources: ['dashboard_archive.md'],
          },
          reasoning: {
            ...baseTrace.reasoning,
            selectedSources: ['monitoring.md'],
            sourceSummary: 'Selected 1 source that directly shaped the answer.',
            conflictSummary: 'Preferred monitoring.md because live metrics were newer than the archived dashboard note.',
          },
        }}
        error={null}
        traceLabel="Response 2"
        activeTab="thinking"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('How the answer was formed')).toBeInTheDocument()
    expect(screen.getByText('Generated response')).toBeInTheDocument()
    expect(screen.getByText('Synthesized evidence')).toBeInTheDocument()
    expect(screen.getByText('Selected answer-shaping sources')).toBeInTheDocument()
    expect(screen.getByText('Applied tool results')).toBeInTheDocument()
    expect(screen.getByText('Reused recent context')).toBeInTheDocument()
    expect(screen.getByText('Resolved conflicting evidence')).toBeInTheDocument()
    expect(screen.getByText('Included caveats')).toBeInTheDocument()
    expect(screen.getByText('Live systems are not wired in this slice.')).toBeInTheDocument()
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
