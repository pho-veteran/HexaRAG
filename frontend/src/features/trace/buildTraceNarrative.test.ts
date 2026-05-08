import { buildTraceNarrative } from './buildTraceNarrative'

describe('buildTraceNarrative', () => {
  it('builds a reasoning-first narrative from runtime, synthesis, selected evidence, memory, contradiction handling, and caveats', () => {
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
        conflictResolution: {
          chosenSource: 'api_reference_v2.md',
          rationale: 'v2 supersedes archived v1.',
          competingSources: ['api_reference_v1_archived.md'],
        },
        runtime: {
          mode: 'aws',
          provider: 'bedrock-agent',
          region: 'us-east-1',
          agentId: 'AGENT123456',
          agentAliasId: 'ALIAS12345',
          model: 'us.anthropic.claude-3-5-haiku-20241022-v1:0',
        },
        reasoning: {
          evidenceTypes: ['retrieval', 'tool', 'memory'],
          selectedSources: ['ownership.md'],
          toolBasis: ['knowledge_base_lookup'],
          memoryApplied: true,
          memorySummary: 'Used 1 recent conversation item to keep the answer on topic.',
          uncertaintyReason: 'Live monitoring was not needed for this answer.',
          answerStrategy: 'grounded-answer',
          runtimeLabel: 'us.anthropic.claude-3-5-haiku-20241022-v1:0 via bedrock-agent',
          caveat: 'Live monitoring was not needed for this answer.',
          sourceSummary: 'Selected 1 source that directly shaped the answer.',
          toolSummary: 'Used 1 tool result in the final answer.',
          explanationSummary: 'The answer combined retrieved evidence, live tool data, and recent conversation context.',
          narrativeFocus: 'evidence-synthesis',
          nextStep: undefined,
          conflictSummary: 'Preferred api_reference_v2.md because v2 supersedes archived v1.',
        },
      }),
    ).toEqual([
      {
        id: 'runtime',
        title: 'Generated response',
        detail: 'Generated with us.anthropic.claude-3-5-haiku-20241022-v1:0 via bedrock-agent.',
      },
      {
        id: 'evidence',
        title: 'Synthesized evidence',
        detail: 'The answer combined retrieved evidence, live tool data, and recent conversation context.',
      },
      {
        id: 'sources',
        title: 'Selected answer-shaping sources',
        detail: 'Selected 1 source that directly shaped the answer. Key source: ownership.md.',
      },
      {
        id: 'tools',
        title: 'Applied tool results',
        detail: 'Used 1 tool result in the final answer.',
      },
      {
        id: 'memory',
        title: 'Reused recent context',
        detail: 'Used 1 recent conversation item to keep the answer on topic.',
      },
      {
        id: 'contradiction',
        title: 'Resolved conflicting evidence',
        detail: 'Preferred api_reference_v2.md because v2 supersedes archived v1.',
      },
      {
        id: 'uncertainty',
        title: 'Included caveats',
        detail: 'Live monitoring was not needed for this answer.',
      },
    ])
  })

  it('still produces runtime and synthesis steps when the trace is sparse', () => {
    expect(
      buildTraceNarrative({
        citations: [],
        inlineCitations: [],
        toolCalls: [],
        memoryWindow: [],
        groundingNotes: [],
        uncertainty: null,
        conflictResolution: undefined,
        runtime: {
          mode: 'unknown',
          provider: 'unavailable',
          region: undefined,
          agentId: undefined,
          agentAliasId: undefined,
          model: undefined,
        },
        reasoning: {
          evidenceTypes: [],
          selectedSources: [],
          toolBasis: [],
          memoryApplied: false,
          memorySummary: undefined,
          uncertaintyReason: undefined,
          answerStrategy: 'fallback',
          runtimeLabel: 'Runtime unavailable',
          caveat: undefined,
          sourceSummary: 'No citations were available for this answer.',
          toolSummary: 'No tool calls were needed for this answer.',
          explanationSummary: 'The answer was formed from the evidence available in this turn.',
          narrativeFocus: 'degraded-mode',
          nextStep: undefined,
          conflictSummary: undefined,
        },
      }),
    ).toEqual([
      {
        id: 'runtime',
        title: 'Generated response',
        detail: 'Generated with Runtime unavailable.',
      },
      {
        id: 'evidence',
        title: 'Synthesized evidence',
        detail: 'The answer was formed from the evidence available in this turn.',
      },
    ])
  })
})
