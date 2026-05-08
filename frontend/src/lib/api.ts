import type { ChatErrorState, ChatResponse, TracePayload } from '../types/chat'

const API_BASE_URL =
  import.meta.env.MODE === 'test'
    ? 'http://localhost:8000'
    : (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000')

interface ApiCitation {
  source_id: string
  title: string
  excerpt: string
  version: string | null
  recency_note: string | null
}

interface ApiToolCallTrace {
  name: string
  status: 'success' | 'error'
  summary: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
}

interface ApiInlineCitationAnchor {
  start: number
  end: number
  source_ids: string[]
}

interface ApiConflictResolution {
  chosen_source: string
  rationale: string
  competing_sources: string[]
}

interface ApiRuntimeTrace {
  mode: string
  provider: string
  region: string | null
  agent_id: string | null
  agent_alias_id: string | null
  model: string | null
}

interface ApiReasoningTrace {
  evidence_types: string[]
  selected_sources: string[]
  tool_basis: string[]
  memory_applied: boolean
  memory_summary: string | null
  uncertainty_reason: string | null
  answer_strategy: string
  runtime_label: string | null
  caveat: string | null
  source_summary: string | null
  tool_summary: string | null
  explanation_summary: string | null
  narrative_focus: string
  next_step: string | null
  conflict_summary: string | null
}

interface ApiTracePayload {
  citations: ApiCitation[]
  inline_citations?: ApiInlineCitationAnchor[]
  tool_calls: ApiToolCallTrace[]
  memory_window: string[]
  grounding_notes: string[]
  uncertainty: string | null
  conflict_resolution?: ApiConflictResolution | null
  runtime: ApiRuntimeTrace
  reasoning: ApiReasoningTrace
}

interface ApiChatResponse {
  session_id: string
  message: {
    role: 'assistant'
    content: string
    trace: ApiTracePayload
  }
}

interface ApiChatErrorResponse {
  error: string
  trace?: {
    request?: {
      session_id?: string
      message?: string
    }
    details?: string[]
  }
}

function mapTrace(trace: ApiTracePayload): TracePayload {
  return {
    citations: trace.citations.map((citation) => ({
      sourceId: citation.source_id,
      title: citation.title,
      excerpt: citation.excerpt,
      version: citation.version ?? undefined,
      recencyNote: citation.recency_note ?? undefined,
    })),
    inlineCitations: (trace.inline_citations ?? []).map((anchor) => ({
      start: anchor.start,
      end: anchor.end,
      sourceIds: anchor.source_ids,
    })),
    toolCalls: trace.tool_calls,
    memoryWindow: trace.memory_window,
    groundingNotes: trace.grounding_notes,
    uncertainty: trace.uncertainty,
    conflictResolution: trace.conflict_resolution
      ? {
          chosenSource: trace.conflict_resolution.chosen_source,
          rationale: trace.conflict_resolution.rationale,
          competingSources: trace.conflict_resolution.competing_sources,
        }
      : undefined,
    runtime: {
      mode: trace.runtime.mode,
      provider: trace.runtime.provider,
      region: trace.runtime.region ?? undefined,
      agentId: trace.runtime.agent_id ?? undefined,
      agentAliasId: trace.runtime.agent_alias_id ?? undefined,
      model: trace.runtime.model ?? undefined,
    },
    reasoning: {
      evidenceTypes: trace.reasoning.evidence_types,
      selectedSources: trace.reasoning.selected_sources,
      toolBasis: trace.reasoning.tool_basis,
      memoryApplied: trace.reasoning.memory_applied,
      memorySummary: trace.reasoning.memory_summary ?? undefined,
      uncertaintyReason: trace.reasoning.uncertainty_reason ?? undefined,
      answerStrategy: trace.reasoning.answer_strategy,
      runtimeLabel: trace.reasoning.runtime_label ?? undefined,
      caveat: trace.reasoning.caveat ?? undefined,
      sourceSummary: trace.reasoning.source_summary ?? undefined,
      toolSummary: trace.reasoning.tool_summary ?? undefined,
      explanationSummary: trace.reasoning.explanation_summary ?? undefined,
      narrativeFocus: trace.reasoning.narrative_focus,
      nextStep: trace.reasoning.next_step ?? undefined,
      conflictSummary: trace.reasoning.conflict_summary ?? undefined,
    },
  }
}

function mapError(payload: ApiChatErrorResponse, sessionId: string, message: string, fallbackMessage: string): ChatErrorState {
  return {
    message: payload.error || fallbackMessage,
    request: {
      sessionId: payload.trace?.request?.session_id ?? sessionId,
      message: payload.trace?.request?.message ?? message,
    },
    details: payload.trace?.details ?? [],
  }
}

export async function postChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
  })

  const fallbackMessage = response.statusText || 'Request failed.'
  let responseText = ''
  let payload: ApiChatResponse | ApiChatErrorResponse | null = null

  if (typeof response.text === 'function') {
    responseText = await response.text()

    if (responseText) {
      try {
        payload = JSON.parse(responseText) as ApiChatResponse | ApiChatErrorResponse
      } catch {
        payload = null
      }
    }
  } else if (typeof response.json === 'function') {
    payload = (await response.json()) as ApiChatResponse | ApiChatErrorResponse
  }

  if (!response.ok) {
    if (payload && typeof payload === 'object' && 'error' in payload) {
      throw mapError(payload as ApiChatErrorResponse, sessionId, message, fallbackMessage)
    }

    throw mapError({ error: responseText || fallbackMessage }, sessionId, message, fallbackMessage)
  }

  const successPayload = payload as ApiChatResponse

  return {
    sessionId: successPayload.session_id,
    message: {
      role: successPayload.message.role,
      content: successPayload.message.content,
      trace: mapTrace(successPayload.message.trace),
    },
  }
}
