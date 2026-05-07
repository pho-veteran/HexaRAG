export interface Citation {
  sourceId: string
  title: string
  excerpt: string
  version?: string
  recencyNote?: string
}

export interface InlineCitationAnchor {
  start: number
  end: number
  sourceIds: string[]
}

export interface ToolCallTrace {
  name: string
  status: 'success' | 'error'
  summary: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
}

export interface TracePayload {
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
}

export type TracePanelTab = 'observability' | 'thinking'

export interface TraceNarrativeStep {
  id: 'sources' | 'tools' | 'memory' | 'grounding' | 'uncertainty'
  title: string
  detail: string
}

export interface UserChatMessage {
  id: string
  role: 'user'
  content: string
}

export interface AssistantChatMessage {
  id: string
  role: 'assistant'
  content: string
  trace: TracePayload
  label: string
}

export type ConversationMessage = UserChatMessage | AssistantChatMessage

export interface ChatResponse {
  sessionId: string
  message: {
    role: 'assistant'
    content: string
    trace: TracePayload
  }
}

export interface ChatErrorState {
  message: string
  request: {
    sessionId: string
    message: string
  }
  details: string[]
}
