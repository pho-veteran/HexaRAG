import { buildTraceNarrative } from './buildTraceNarrative'

describe('buildTraceNarrative', () => {
  it('builds an ordered narrative from sources, tools, memory, grounding, and uncertainty', () => {
    expect(
      buildTraceNarrative({
        citations: [
          {
            sourceId: 'doc-ownership',
            title: 'ownership.md',
            excerpt: 'Notifications is owned by Team Mercury.',
            version: undefined,
            recencyNote: undefined,
          },
        ],
        inlineCitations: [],
        toolCalls: [
          {
            name: 'knowledge_base_lookup',
            status: 'success',
            summary: 'Retrieved ownership document',
            input: { question: 'Who owns the Notifications service?' },
            output: { source: 'ownership.md' },
          },
        ],
        memoryWindow: ['Prior question about latency'],
        groundingNotes: ['Used the ownership document.'],
        uncertainty: 'Live monitoring was not needed for this answer.',
      }),
    ).toEqual([
      {
        id: 'sources',
        title: 'Checked sources',
        detail: 'Reviewed 1 retrieved source: ownership.md.',
      },
      {
        id: 'tools',
        title: 'Ran tools',
        detail: 'Used 1 tool call to validate the answer: knowledge_base_lookup.',
      },
      {
        id: 'memory',
        title: 'Used session context',
        detail: 'Considered 1 recent context item from the conversation.',
      },
      {
        id: 'grounding',
        title: 'Grounded answer',
        detail: 'Used the ownership document.',
      },
      {
        id: 'uncertainty',
        title: 'Called out uncertainty',
        detail: 'Live monitoring was not needed for this answer.',
      },
    ])
  })

  it('still produces a grounded-answer step when the trace is sparse', () => {
    expect(
      buildTraceNarrative({
        citations: [],
        inlineCitations: [],
        toolCalls: [],
        memoryWindow: [],
        groundingNotes: [],
        uncertainty: null,
      }),
    ).toEqual([
      {
        id: 'grounding',
        title: 'Grounded answer',
        detail: 'Built the final answer from the available evidence in this turn.',
      },
    ])
  })
})
