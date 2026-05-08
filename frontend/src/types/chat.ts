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

export interface ConflictResolution {
  chosenSource: string
  rationale: string
  competingSources: string[]
}

export interface RuntimeTrace {
  mode: string
  provider: string
  region?: string
  agentId?: string
  agentAliasId?: string
  model?: string
}

export interface ReasoningTrace {
  evidenceTypes: string[]
  selectedSources: string[]
  toolBasis: string[]
  memoryApplied: boolean
  memorySummary?: string
  uncertaintyReason?: string
  answerStrategy: string
  runtimeLabel?: string
  caveat?: string
  sourceSummary?: string
  toolSummary?: string
  explanationSummary?: string
  narrativeFocus: string
  nextStep?: string
  conflictSummary?: string
}

export interface TracePayload {
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
  conflictResolution?: ConflictResolution
  runtime: RuntimeTrace
  reasoning: ReasoningTrace
}

export type TracePanelTab = 'observability' | 'thinking'

export interface TraceNarrativeStep {
  id: 'runtime' | 'evidence' | 'sources' | 'tools' | 'memory' | 'contradiction' | 'uncertainty'
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
