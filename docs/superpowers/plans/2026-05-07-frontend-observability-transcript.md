# Frontend Observability Transcript Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current latest-result chat UI with a transcript-based conversation view that supports L1-L5 sample prompts, compact referenced-document lists under assistant replies, and per-reply trace inspection in the always-visible observability panel.

**Architecture:** Keep the existing `/chat` API contract and move the frontend to a turn-oriented state model. Store user and assistant turns in one ordered transcript, let assistant turns carry their trace payload, and keep a selected assistant message id that drives the right-side panel. Preserve the current error-trace behavior by clearing the selected assistant trace on failed requests and allowing a later trace click to restore trace inspection.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, React Testing Library, Docker Compose.

**Visual note:** Transcript behavior, per-reply trace selection, and sample-question workflow remain defined here. The Executive Console visual refresh that preserves those behaviors is implemented in `docs/superpowers/plans/2026-05-07-frontend-ui-remake.md`.

**Refinement note:** The current frontend now uses the follow-up light theme variant with a full-viewport three-panel layout, warm orange-to-white gradient background, a bottom-of-panel frontend mockup trigger, inline numbered citation markers inside assistant answers, row-by-row clickable citation titles that open a citation detail modal, and an interactive mockup dialog that can switch inspection tabs and preview citation details while keeping the same transcript and inspection behavior.

---

## Planned File Structure

### Frontend chat state and constants
- Create: `frontend/src/features/chat/sampleQuestions.ts` — fixed L1-L5 demo prompt list with labels and prompt text.
- Modify: `frontend/src/types/chat.ts` — transcript message types and selected-trace-friendly frontend models.
- Modify: `frontend/src/features/chat/useChatSession.ts` — ordered transcript state, sample-question application, selected trace state, and failure behavior.

### Frontend UI
- Modify: `frontend/src/features/chat/ChatPage.tsx` — sample-question strip, transcript rendering, referenced-document list, per-reply trace buttons, and composer wiring.
- Modify: `frontend/src/features/trace/TracePanel.tsx` — selected-reply trace header copy while preserving sources, tools, memory, grounding, and error sections.
- Modify: `frontend/src/styles.css` — transcript layout, sample prompt strip, selected assistant reply styling, and compact citation list styling.

### Frontend tests
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — transcript, sample prompt, trace selection, and failure-path interaction coverage.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — selected-trace header and existing trace/error rendering coverage.

### Tracking and docs
- Modify: `TASKS.md` — index this enhancement plan alongside the existing plan set.
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` — mark the old latest-result execution note as superseded by this transcript-based enhancement.
- Review: `docs/local-dev.md` — commands should remain accurate; only edit if verification commands actually change.

---

### Task 1: Lock the new transcript UX with failing frontend tests

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`

- [ ] **Step 1: Replace the chat page tests with transcript, sample prompt, trace selection, and failure coverage**

Update `frontend/src/features/chat/ChatPage.test.tsx` to:

```tsx
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ChatPage } from './ChatPage'

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('ChatPage', () => {
  it('renders sample prompts and an empty transcript state', () => {
    render(<ChatPage />)

    expect(screen.getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /L1/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /L5/i })).toBeInTheDocument()
    expect(screen.getByText('Start with a sample question or type your own prompt.')).toBeInTheDocument()
    expect(screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.')).toBeInTheDocument()
  })

  it('fills the composer when a sample prompt is clicked without sending a request', async () => {
    const user = userEvent.setup()
    render(<ChatPage />)

    await user.click(screen.getByRole('button', { name: /L3/i }))

    expect(screen.getByPlaceholderText('Ask GeekBrain anything...')).toHaveValue(
      'What is PaymentGW current latency right now?',
    )
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('renders transcript turns, referenced documents, and auto-selects the newest trace', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'phase1-session',
          message: {
            role: 'assistant',
            content: 'Team Mercury owns the Notifications service.',
            trace: {
              citations: [
                {
                  source_id: 'doc-ownership',
                  title: 'ownership.md',
                  excerpt: 'Notifications is owned by Team Mercury.',
                  version: null,
                  recency_note: 'Updated 2026-04-30.',
                },
              ],
              tool_calls: [],
              memory_window: [],
              grounding_notes: ['Grounded in the ownership document.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'phase1-session',
          message: {
            role: 'assistant',
            content: 'PaymentGW current latency is 185 ms.',
            trace: {
              citations: [
                {
                  source_id: 'doc-monitoring',
                  title: 'monitoring.md',
                  excerpt: 'PaymentGW latency p95 is 185 ms.',
                  version: null,
                  recency_note: null,
                },
              ],
              tool_calls: [
                {
                  name: 'monitoring_snapshot',
                  status: 'success',
                  summary: 'Fetched current PaymentGW metrics',
                  input: { question: 'What is PaymentGW current latency right now?' },
                  output: { latency_p95_ms: 185 },
                },
              ],
              memory_window: ['Who owns the Notifications service?'],
              grounding_notes: ['Used live monitoring data.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Team Mercury owns the Notifications service.')).toBeInTheDocument()
    expect(screen.getByText('ownership.md')).toBeInTheDocument()
    expect(screen.getByText('Inspecting Response 1.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /L3/i }))
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('PaymentGW current latency is 185 ms.')).toBeInTheDocument()
    expect(screen.getByText('monitoring.md')).toBeInTheDocument()
    expect(screen.getByText('Inspecting Response 2.')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Fetched current PaymentGW metrics')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('switches the observability panel when an older reply trace is selected', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'phase1-session',
          message: {
            role: 'assistant',
            content: 'Team Mercury owns the Notifications service.',
            trace: {
              citations: [
                {
                  source_id: 'doc-ownership',
                  title: 'ownership.md',
                  excerpt: 'Notifications is owned by Team Mercury.',
                  version: null,
                  recency_note: null,
                },
              ],
              tool_calls: [
                {
                  name: 'knowledge_base_lookup',
                  status: 'success',
                  summary: 'Retrieved ownership document',
                  input: { question: 'Who owns the Notifications service?' },
                  output: { source: 'ownership.md' },
                },
              ],
              memory_window: [],
              grounding_notes: ['Used the ownership document.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'phase1-session',
          message: {
            role: 'assistant',
            content: 'PaymentGW current latency is 185 ms.',
            trace: {
              citations: [
                {
                  source_id: 'doc-monitoring',
                  title: 'monitoring.md',
                  excerpt: 'PaymentGW latency p95 is 185 ms.',
                  version: null,
                  recency_note: null,
                },
              ],
              tool_calls: [
                {
                  name: 'monitoring_snapshot',
                  status: 'success',
                  summary: 'Fetched current PaymentGW metrics',
                  input: { question: 'What is PaymentGW current latency right now?' },
                  output: { latency_p95_ms: 185 },
                },
              ],
              memory_window: ['Who owns the Notifications service?'],
              grounding_notes: ['Used live monitoring data.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText('Team Mercury owns the Notifications service.')

    await user.click(screen.getByRole('button', { name: /L3/i }))
    await user.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText('PaymentGW current latency is 185 ms.')

    const responseOne = screen.getByRole('article', { name: 'Response 1' })
    await user.click(within(responseOne).getByRole('button', { name: 'View trace' }))

    expect(screen.getByText('Inspecting Response 1.')).toBeInTheDocument()
    expect(screen.getByText('knowledge_base_lookup: Retrieved ownership document')).toBeInTheDocument()
    expect(responseOne).toHaveClass('message-card--selected')
  })

  it('preserves transcript history and shows observability error details after a failed request', async () => {
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          session_id: 'phase1-session',
          message: {
            role: 'assistant',
            content: 'Team Mercury owns the Notifications service.',
            trace: {
              citations: [],
              tool_calls: [],
              memory_window: [],
              grounding_notes: ['Grounded in the ownership document.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({
          error: 'Unable to generate stub response.',
          trace: {
            request: {
              session_id: 'phase1-session',
              message: 'trigger failure',
            },
            details: ['Stub failure requested for UI error-state coverage.'],
          },
        }),
      } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText('Team Mercury owns the Notifications service.')

    await user.clear(screen.getByPlaceholderText('Ask GeekBrain anything...'))
    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'trigger failure')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate stub response.')
    expect(screen.getByText('Who owns the Notifications service?')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
    expect(screen.queryByText('Request failed')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Update the trace panel test to cover selected-trace header text while preserving error-state coverage**

Update `frontend/src/features/trace/TracePanel.test.tsx` to:

```tsx
import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('shows empty-state guidance before the first answer', () => {
    render(<TracePanel trace={null} error={null} traceLabel={null} />)

    expect(
      screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.'),
    ).toBeInTheDocument()
  })

  it('renders a selected trace label and successful trace sections', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-architecture',
              title: 'architecture.md',
              excerpt: 'Current p95 latency sits below the alert threshold.',
              version: undefined,
              recencyNote: 'Stubbed knowledge base note.',
            },
          ],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'success',
              summary: 'Prepared stub observability data',
              input: { question: 'What is PaymentGW latency?' },
              output: { mode: 'stub', latency_p95_ms: 185 },
            },
          ],
          memoryWindow: ['No prior turns in Phase 1 single-turn mode.'],
          groundingNotes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
          uncertainty: 'Live systems are not wired in this slice.',
        }}
        error={null}
        traceLabel="Response 2"
      />,
    )

    expect(screen.getByText('Inspecting Response 2.')).toBeInTheDocument()
    expect(screen.getByText('architecture.md')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
  })

  it('renders failed-request details when the API call fails', () => {
    render(
      <TracePanel
        trace={null}
        error={{
          message: 'Unable to generate stub response.',
          request: {
            sessionId: 'phase1-session',
            message: 'trigger failure',
          },
          details: ['Stub failure requested for UI error-state coverage.'],
        }}
        traceLabel={null}
      />,
    )

    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Run the targeted frontend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: FAIL because `ChatPage` still renders the latest-result view, no sample prompt buttons exist, no transcript articles exist, and `TracePanel` does not accept a `traceLabel` prop yet.

- [ ] **Step 4: Commit the test changes**

```bash
git add frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/trace/TracePanel.test.tsx
git commit -m "test: define transcript observability ui behavior"
```

---

### Task 2: Introduce transcript models, sample prompts, and selected trace state

**Files:**
- Create: `frontend/src/features/chat/sampleQuestions.ts`
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/features/chat/useChatSession.ts`

- [ ] **Step 1: Expand the frontend chat types for transcript turns and assistant trace labels**

Update `frontend/src/types/chat.ts` to:

```ts
export interface Citation {
  sourceId: string
  title: string
  excerpt: string
  version?: string
  recencyNote?: string
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
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
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
```

- [ ] **Step 2: Add a fixed L1-L5 sample question list**

Create `frontend/src/features/chat/sampleQuestions.ts`:

```ts
export const sampleQuestions = [
  {
    level: 'L1',
    prompt: 'Who owns the Notifications service?',
  },
  {
    level: 'L2',
    prompt: 'What changed in the on-call escalation policy, and which document is newer?',
  },
  {
    level: 'L3',
    prompt: 'What is PaymentGW current latency right now?',
  },
  {
    level: 'L4',
    prompt: 'Why did its costs spike last month?',
  },
  {
    level: 'L5',
    prompt: 'Investigate whether Checkout is healthy enough for a product launch today.',
  },
] as const
```

- [ ] **Step 3: Replace latest-message state with transcript and selected-trace state**

Update `frontend/src/features/chat/useChatSession.ts` to:

```ts
import { useRef, useState } from 'react'

import { postChatMessage } from '../../lib/api'
import type {
  AssistantChatMessage,
  ChatErrorState,
  ConversationMessage,
  TracePayload,
} from '../../types/chat'

const SESSION_ID = 'phase1-session'

interface ChatSessionState {
  prompt: string
  messages: ConversationMessage[]
  selectedTraceMessageId: string | null
  selectedTrace: TracePayload | null
  selectedTraceLabel: string | null
  error: ChatErrorState | null
  isSubmitting: boolean
  canSubmit: boolean
  setPrompt: (value: string) => void
  applySampleQuestion: (value: string) => void
  selectTraceMessage: (messageId: string) => void
  submitPrompt: () => Promise<void>
}

export function useChatSession(): ChatSessionState {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [selectedTraceMessageId, setSelectedTraceMessageId] = useState<string | null>(null)
  const [error, setError] = useState<ChatErrorState | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const nextMessageIdRef = useRef(0)
  const nextAssistantNumberRef = useRef(1)

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
      const response = await postChatMessage(SESSION_ID, submittedPrompt)
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

  return {
    prompt,
    messages,
    selectedTraceMessageId,
    selectedTrace: selectedTraceMessage?.trace ?? null,
    selectedTraceLabel: selectedTraceMessage?.label ?? null,
    error,
    isSubmitting,
    canSubmit,
    setPrompt,
    applySampleQuestion,
    selectTraceMessage,
    submitPrompt,
  }
}
```

- [ ] **Step 4: Run the targeted frontend tests again**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: FAIL, but with narrower UI-level failures because the new state exists while `ChatPage.tsx`, `TracePanel.tsx`, and `styles.css` still render the old layout and props.

- [ ] **Step 5: Commit the state-model changes**

```bash
git add frontend/src/types/chat.ts frontend/src/features/chat/sampleQuestions.ts frontend/src/features/chat/useChatSession.ts
git commit -m "feat: add transcript chat session state"
```

---

### Task 3: Render the transcript UI, per-reply references, and selected trace panel

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/trace/TracePanel.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Replace the latest-result view with sample prompts, transcript cards, and trace buttons**

Update `frontend/src/features/chat/ChatPage.tsx` to:

```tsx
import type { FormEvent } from 'react'

import type { AssistantChatMessage } from '../../types/chat'
import { TracePanel } from '../trace/TracePanel'
import { sampleQuestions } from './sampleQuestions'
import { useChatSession } from './useChatSession'

export function ChatPage() {
  const {
    prompt,
    messages,
    selectedTraceMessageId,
    selectedTrace,
    selectedTraceLabel,
    error,
    isSubmitting,
    canSubmit,
    setPrompt,
    applySampleQuestion,
    selectTraceMessage,
    submitPrompt,
  } = useChatSession()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await submitPrompt()
  }

  return (
    <main className="app-shell">
      <section className="chat-pane">
        <header className="chat-header">
          <h1>HexaRAG</h1>
          <p>Ask GeekBrain anything.</p>
        </header>

        <section className="sample-strip" aria-label="Quick demo questions">
          <h2>Quick demo questions</h2>
          <div className="sample-strip__list">
            {sampleQuestions.map((question) => (
              <button
                key={question.level}
                type="button"
                className="sample-strip__button"
                onClick={() => applySampleQuestion(question.prompt)}
              >
                <span className="sample-strip__level">{question.level}</span>
                <span className="sample-strip__prompt">{question.prompt}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="conversation-thread" aria-live="polite">
          {messages.length === 0 ? (
            <p className="result-empty">Start with a sample question or type your own prompt.</p>
          ) : (
            messages.map((message) => {
              const isAssistant = message.role === 'assistant'
              const isSelected = isAssistant && message.id === selectedTraceMessageId
              const assistantMessage = isAssistant ? (message as AssistantChatMessage) : null

              return (
                <article
                  key={message.id}
                  aria-label={isAssistant ? assistantMessage.label : 'User message'}
                  className={`message-card message-card--${message.role}${
                    isSelected ? ' message-card--selected' : ''
                  }`}
                >
                  <h3>{isAssistant ? assistantMessage.label : 'You'}</h3>
                  <p>{message.content}</p>

                  {assistantMessage ? (
                    <>
                      {assistantMessage.trace.citations.length > 0 ? (
                        <section className="message-sources">
                          <h4>Referenced documents</h4>
                          <ul className="message-sources__list">
                            {assistantMessage.trace.citations.map((citation) => (
                              <li key={citation.sourceId}>{citation.title}</li>
                            ))}
                          </ul>
                        </section>
                      ) : null}

                      <button
                        type="button"
                        className="trace-link"
                        aria-pressed={isSelected}
                        onClick={() => selectTraceMessage(assistantMessage.id)}
                      >
                        View trace
                      </button>
                    </>
                  ) : null}
                </article>
              )
            })
          )}
        </section>

        <form className="composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-message">
            Question
          </label>
          <textarea
            id="chat-message"
            placeholder="Ask GeekBrain anything..."
            rows={3}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
          />
          {error ? (
            <p className="form-error" role="alert">
              {error.message}
            </p>
          ) : null}
          <button type="submit" disabled={!canSubmit}>
            {isSubmitting ? 'Sending...' : 'Send'}
          </button>
        </form>
      </section>

      <aside className="trace-pane">
        <TracePanel
          trace={selectedTrace}
          error={selectedTraceMessageId === null ? error : null}
          traceLabel={selectedTraceLabel}
        />
      </aside>
    </main>
  )
}
```

- [ ] **Step 2: Make the trace panel describe the selected reply while preserving existing sections**

Update `frontend/src/features/trace/TracePanel.tsx` to:

```tsx
import type { ChatErrorState, TracePayload } from '../../types/chat'

interface TracePanelProps {
  trace: TracePayload | null
  error: ChatErrorState | null
  traceLabel: string | null
}

export function TracePanel({ trace, error, traceLabel }: TracePanelProps) {
  const headerCopy = error
    ? 'Showing request error details.'
    : traceLabel
      ? `Inspecting ${traceLabel}.`
      : 'Always visible for every answer.'

  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Observability</h2>
        <p>{headerCopy}</p>
      </header>

      {error ? (
        <>
          <section className="trace-section">
            <h3>Last request</h3>
            <p>
              <strong>Session:</strong> {error.request.sessionId}
            </p>
            <p>
              <strong>Message:</strong> {error.request.message}
            </p>
          </section>

          <section className="trace-section">
            <h3>Error details</h3>
            <p>{error.message}</p>
            <ul className="trace-list">
              {error.details.map((detail, index) => (
                <li key={`${detail}-${index}`}>{detail}</li>
              ))}
            </ul>
          </section>
        </>
      ) : trace ? (
        <>
          <section className="trace-section">
            <h3>Sources</h3>
            <ul className="trace-list">
              {trace.citations.map((citation) => (
                <li key={citation.sourceId}>{citation.title}</li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Tool calls</h3>
            <ul className="trace-list">
              {trace.toolCalls.map((tool, index) => (
                <li key={`${tool.name}-${index}`}>
                  {tool.name}: {tool.summary}
                </li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Memory</h3>
            <ul className="trace-list">
              {trace.memoryWindow.map((entry, index) => (
                <li key={`${entry}-${index}`}>{entry}</li>
              ))}
            </ul>
          </section>

          <section className="trace-section">
            <h3>Grounding</h3>
            <ul className="trace-list">
              {trace.groundingNotes.map((note, index) => (
                <li key={`${note}-${index}`}>{note}</li>
              ))}
            </ul>
          </section>

          {trace.uncertainty ? (
            <section className="trace-section">
              <h3>Uncertainty</h3>
              <p>{trace.uncertainty}</p>
            </section>
          ) : null}
        </>
      ) : (
        <p className="trace-empty">Send a question to inspect retrieval, tools, memory, and grounding.</p>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Add the transcript, sample prompt, and selected-state styles**

Update `frontend/src/styles.css` by replacing the old latest-result styles with:

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  color: #1a1a1a;
  background: #f5f5f5;
}

.app-shell {
  display: grid;
  grid-template-columns: 1fr 400px;
  height: 100vh;
  gap: 0;
}

.chat-pane {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  min-height: 0;
  background: white;
  border-right: 1px solid #e0e0e0;
}

.chat-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.chat-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.chat-header p {
  color: #666;
  font-size: 0.875rem;
}

.sample-strip {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.sample-strip h2 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.sample-strip__list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.sample-strip__button {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  text-align: left;
}

.sample-strip__button:hover {
  border-color: #0066cc;
}

.sample-strip__level {
  font-size: 0.75rem;
  font-weight: 700;
  color: #0066cc;
}

.sample-strip__prompt {
  font-size: 0.875rem;
  color: #333;
}

.conversation-thread {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
  overflow-y: auto;
  padding: 1.5rem;
}

.result-empty {
  color: #666;
  font-size: 0.9375rem;
}

.message-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1rem;
  background: #fafafa;
}

.message-card h3 {
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.message-card--user {
  align-self: flex-end;
  max-width: 80%;
  background: #e8f1ff;
}

.message-card--assistant {
  max-width: 85%;
  background: white;
}

.message-card--selected {
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.12);
}

.message-sources {
  margin-top: 0.875rem;
}

.message-sources h4 {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #666;
  margin-bottom: 0.35rem;
}

.message-sources__list {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.message-sources__list li {
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  background: #f1f5f9;
  font-size: 0.8125rem;
  color: #334155;
}

.trace-link {
  margin-top: 0.875rem;
  border: none;
  background: none;
  color: #0066cc;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.composer textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.9375rem;
  resize: vertical;
}

.composer textarea:focus {
  outline: none;
  border-color: #0066cc;
}

.composer button {
  align-self: flex-start;
  padding: 0.625rem 1.25rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
}

.composer button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.form-error {
  color: #b91c1c;
  font-size: 0.875rem;
}

.trace-pane {
  background: #fafafa;
  overflow-y: auto;
  padding: 1.5rem;
}

.trace-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.trace-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.trace-header p {
  color: #666;
  font-size: 0.8125rem;
}

.trace-empty {
  color: #999;
  font-size: 0.875rem;
  font-style: italic;
}

.trace-section {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.trace-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  color: #666;
  margin-bottom: 0.75rem;
}

.trace-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.trace-list li {
  font-size: 0.875rem;
  color: #333;
  padding-left: 1rem;
  position: relative;
}

.trace-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #999;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

- [ ] **Step 4: Run the targeted frontend tests and build**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected: PASS. The transcript tests, selected-trace tests, and build should all succeed without backend changes.

- [ ] **Step 5: Commit the UI implementation**

```bash
git add frontend/src/features/chat/ChatPage.tsx frontend/src/features/trace/TracePanel.tsx frontend/src/styles.css
git commit -m "feat: add transcript-based observability chat ui"
```

---

### Task 4: Update tracking/docs and run final verification

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- Review: `docs/local-dev.md`

- [ ] **Step 1: Index the new enhancement plan in `TASKS.md`**

Update the plan index in `TASKS.md` to include:

```md
- `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` — transcript chat UI, sample demo prompts, referenced documents, per-reply trace selection
```

Place it under the existing plan index list so this enhancement is discoverable alongside the completed phase plans.

- [ ] **Step 2: Mark the old latest-result note in the foundation plan as superseded**

Update the execution note under Task 5 in `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` to:

```md
Execution note: The original Phase 1 UI shipped as a single-turn form plus latest-result panel. It has since been superseded by `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`, which keeps the same `/chat` contract while rendering a transcript, compact referenced documents, and per-reply trace selection.
```

This keeps the historical plan accurate without pretending the old UI description is still current.

- [ ] **Step 3: Review `docs/local-dev.md` and keep it unchanged if the commands still match**

Review the frontend verification commands in `docs/local-dev.md`.

Expected outcome: no edit needed, because the existing Docker Compose test and build commands still cover `src/features/chat/ChatPage.test.tsx`, `src/features/trace/TracePanel.test.tsx`, and the frontend build.

- [ ] **Step 4: Run the final verification commands**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit the tracking/doc updates**

```bash
git add TASKS.md docs/superpowers/plans/2026-05-06-hexarag-foundation.md docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md
git commit -m "docs: track transcript observability enhancement"
```

---

## Spec Coverage Check

- **Transcript-style chat pane** → Task 1 defines the failing transcript tests, Task 2 adds transcript-capable state, Task 3 renders transcript cards.
- **L1-L5 sample questions** → Task 1 locks the behavior in tests, Task 2 adds `sampleQuestions.ts`, Task 3 renders the prompt strip.
- **Fill-only sample question behavior** → Task 1 covers no-auto-send behavior, Task 2 adds `applySampleQuestion`, Task 3 wires the buttons.
- **Compact referenced documents under assistant replies** → Task 1 asserts document titles, Task 3 renders the compact citation chips.
- **Per-reply trace selection driving the right panel** → Task 1 adds the older-trace selection test, Task 2 adds `selectedTraceMessageId`, Task 3 wires `View trace` and `traceLabel`.
- **Failure behavior preserving transcript history** → Task 1 adds the failure-path transcript test, Task 2 clears selected trace on failure, Task 3 preserves the error-details panel.
- **Tracking/docs updates** → Task 4 updates `TASKS.md`, supersedes the outdated foundation-plan note, and reviews `docs/local-dev.md`.

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each code-changing step includes the exact code to add or replace.
- Each verification step includes exact Docker Compose commands and expected outcomes.

## Type Consistency Check

Use these names consistently across the implementation:
- `ConversationMessage`, `UserChatMessage`, and `AssistantChatMessage` in `frontend/src/types/chat.ts`
- `selectedTraceMessageId`, `selectedTrace`, and `selectedTraceLabel` in `frontend/src/features/chat/useChatSession.ts`
- `traceLabel` prop in `frontend/src/features/trace/TracePanel.tsx`
- `session_id` only at the API boundary and `sessionId` only after centralized mapping in `frontend/src/lib/api.ts`
- `TracePayload.citations`, `TracePayload.toolCalls`, `TracePayload.memoryWindow`, and `TracePayload.groundingNotes` in the frontend model

---

Plan complete and saved to `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?