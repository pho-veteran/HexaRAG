import type { TraceNarrativeStep, TracePayload } from '../../types/chat'

export function buildTraceNarrative(trace: TracePayload): TraceNarrativeStep[] {
  const steps: TraceNarrativeStep[] = []

  if (trace.citations.length > 0) {
    const titles = trace.citations.map((citation) => citation.title).join(', ')
    steps.push({
      id: 'sources',
      title: 'Checked sources',
      detail: `Reviewed ${trace.citations.length} retrieved source${trace.citations.length === 1 ? '' : 's'}: ${titles}.`,
    })
  }

  if (trace.toolCalls.length > 0) {
    const names = trace.toolCalls.map((tool) => tool.name).join(', ')
    steps.push({
      id: 'tools',
      title: 'Ran tools',
      detail: `Used ${trace.toolCalls.length} tool call${trace.toolCalls.length === 1 ? '' : 's'} to validate the answer: ${names}.`,
    })
  }

  if (trace.memoryWindow.length > 0) {
    steps.push({
      id: 'memory',
      title: 'Used session context',
      detail: `Considered ${trace.memoryWindow.length} recent context item${trace.memoryWindow.length === 1 ? '' : 's'} from the conversation.`,
    })
  }

  steps.push({
    id: 'grounding',
    title: 'Grounded answer',
    detail:
      trace.groundingNotes.length > 0
        ? trace.groundingNotes.join(' ')
        : 'Built the final answer from the available evidence in this turn.',
  })

  if (trace.uncertainty) {
    steps.push({
      id: 'uncertainty',
      title: 'Called out uncertainty',
      detail: trace.uncertainty,
    })
  }

  return steps
}
