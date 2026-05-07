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

interface ApiTracePayload {
  citations: ApiCitation[]
  tool_calls: ApiToolCallTrace[]
  memory_window: string[]
  grounding_notes: string[]
  uncertainty: string | null
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
  trace: {
    request: {
      session_id: string
      message: string
    }
    details: string[]
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
    toolCalls: trace.tool_calls,
    memoryWindow: trace.memory_window,
    groundingNotes: trace.grounding_notes,
    uncertainty: trace.uncertainty,
  }
}

function mapError(payload: ApiChatErrorResponse): ChatErrorState {
  return {
    message: payload.error,
    request: {
      sessionId: payload.trace.request.session_id,
      message: payload.trace.request.message,
    },
    details: payload.trace.details,
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

  const payload = (await response.json()) as ApiChatResponse | ApiChatErrorResponse

  if (!response.ok) {
    throw mapError(payload as ApiChatErrorResponse)
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
