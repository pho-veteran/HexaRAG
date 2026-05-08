import type { TraceNarrativeStep, TracePayload } from '../../types/chat'

export function buildTraceNarrative(trace: TracePayload): TraceNarrativeStep[] {
  const steps: TraceNarrativeStep[] = []

  if (trace.reasoning.runtimeLabel) {
    steps.push({
      id: 'runtime',
      title: 'Generated response',
      detail: `Generated with ${trace.reasoning.runtimeLabel}.`,
    })
  }

  if (trace.reasoning.explanationSummary) {
    steps.push({
      id: 'evidence',
      title: 'Synthesized evidence',
      detail: trace.reasoning.explanationSummary,
    })
  }

  if (trace.reasoning.sourceSummary) {
    const sourceSuffix =
      trace.reasoning.selectedSources.length > 0
        ? ` Key source${trace.reasoning.selectedSources.length === 1 ? '' : 's'}: ${trace.reasoning.selectedSources.join(', ')}.`
        : ''

    steps.push({
      id: 'sources',
      title: 'Selected answer-shaping sources',
      detail: `${trace.reasoning.sourceSummary}${sourceSuffix}`,
    })
  }

  if (trace.reasoning.toolSummary) {
    steps.push({
      id: 'tools',
      title: 'Applied tool results',
      detail: trace.reasoning.toolSummary,
    })
  }

  if (trace.reasoning.memoryApplied && trace.reasoning.memorySummary) {
    steps.push({
      id: 'memory',
      title: 'Reused recent context',
      detail: trace.reasoning.memorySummary,
    })
  }

  if (trace.reasoning.conflictSummary) {
    steps.push({
      id: 'contradiction',
      title: 'Resolved conflicting evidence',
      detail: trace.reasoning.conflictSummary,
    })
  }

  if (trace.reasoning.caveat) {
    steps.push({
      id: 'uncertainty',
      title: 'Included caveats',
      detail: trace.reasoning.caveat,
    })
  }

  return steps
}
