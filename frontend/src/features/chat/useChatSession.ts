import { useState } from 'react'

import { postChatMessage } from '../../lib/api'
import type { ChatErrorState, ChatMessage } from '../../types/chat'

const SESSION_ID = 'phase1-session'

interface ChatSessionState {
  prompt: string
  latestMessage: ChatMessage | null
  error: ChatErrorState | null
  isSubmitting: boolean
  canSubmit: boolean
  setPrompt: (value: string) => void
  submitPrompt: () => Promise<void>
}

export function useChatSession(): ChatSessionState {
  const [prompt, setPrompt] = useState('')
  const [latestMessage, setLatestMessage] = useState<ChatMessage | null>(null)
  const [error, setError] = useState<ChatErrorState | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const canSubmit = !isSubmitting && prompt.trim().length > 0

  const submitPrompt = async () => {
    if (!canSubmit) {
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await postChatMessage(SESSION_ID, prompt.trim())
      setLatestMessage(response.message)
      setPrompt('')
    } catch (requestError) {
      const mappedError = requestError as ChatErrorState
      setLatestMessage(null)
      setError(mappedError)
    } finally {
      setIsSubmitting(false)
    }
  }

  return {
    prompt,
    latestMessage,
    error,
    isSubmitting,
    canSubmit,
    setPrompt,
    submitPrompt,
  }
}
