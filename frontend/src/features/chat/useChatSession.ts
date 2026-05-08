import { useRef, useState } from 'react'

import { postChatMessage } from '../../lib/api'
import type {
  AssistantChatMessage,
  ChatErrorState,
  ConversationMessage,
  TracePanelTab,
  TracePayload,
} from '../../types/chat'

function createSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `session-${Math.random().toString(36).slice(2)}-${Date.now()}`
}

interface ChatSessionState {
  prompt: string
  messages: ConversationMessage[]
  selectedTraceMessageId: string | null
  selectedTrace: TracePayload | null
  selectedTraceLabel: string | null
  selectedTraceTab: TracePanelTab
  error: ChatErrorState | null
  isSubmitting: boolean
  canSubmit: boolean
  setPrompt: (value: string) => void
  applySampleQuestion: (value: string) => void
  selectTraceMessage: (messageId: string) => void
  selectTraceTab: (tab: TracePanelTab) => void
  submitPrompt: () => Promise<void>
}

export function useChatSession(): ChatSessionState {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [selectedTraceMessageId, setSelectedTraceMessageId] = useState<string | null>(null)
  const [selectedTraceTab, setSelectedTraceTab] = useState<TracePanelTab>('observability')
  const [error, setError] = useState<ChatErrorState | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const nextMessageIdRef = useRef(0)
  const nextAssistantNumberRef = useRef(1)
  const sessionIdRef = useRef(createSessionId())

  const canSubmit = !isSubmitting && prompt.trim().length > 0

  const createMessageId = (role: 'user' | 'assistant') => `${role}-${nextMessageIdRef.current++}`

  const applySampleQuestion = (value: string) => {
    setPrompt(value)
    setError(null)
  }

  const selectTraceMessage = (messageId: string) => {
    setSelectedTraceMessageId(messageId)
    setError(null)
  }

  const selectTraceTab = (tab: TracePanelTab) => {
    setSelectedTraceTab(tab)
  }

  const submitPrompt = async () => {
    const submittedPrompt = prompt.trim()

    if (!submittedPrompt || isSubmitting) {
      return
    }

    const userMessage = {
      id: createMessageId('user'),
      role: 'user' as const,
      content: submittedPrompt,
    }

    setMessages((current) => [...current, userMessage])
    setIsSubmitting(true)
    setError(null)

    try {
      const response = await postChatMessage(sessionIdRef.current, submittedPrompt)
      const assistantMessage: AssistantChatMessage = {
        id: createMessageId('assistant'),
        role: 'assistant',
        content: response.message.content,
        trace: response.message.trace,
        label: `Response ${nextAssistantNumberRef.current++}`,
      }

      setMessages((current) => [...current, assistantMessage])
      setSelectedTraceMessageId(assistantMessage.id)
      setPrompt('')
    } catch (requestError) {
      setSelectedTraceMessageId(null)
      setSelectedTraceTab('observability')
      setError(requestError as ChatErrorState)
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedTraceMessage =
    selectedTraceMessageId === null
      ? null
      : (messages.find(
          (message): message is AssistantChatMessage =>
            message.role === 'assistant' && message.id === selectedTraceMessageId,
        ) ?? null)

  const selectedTrace = selectedTraceMessage?.trace ?? null
  const selectedTraceLabel = selectedTraceMessage?.label ?? null

  return {
    prompt,
    messages,
    selectedTraceMessageId,
    selectedTrace,
    selectedTraceLabel,
    selectedTraceTab,
    error,
    isSubmitting,
    canSubmit,
    setPrompt,
    applySampleQuestion,
    selectTraceMessage,
    selectTraceTab,
    submitPrompt,
  }
}
