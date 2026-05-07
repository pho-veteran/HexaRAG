# Frontend UI Remake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the HexaRAG frontend into the approved dark-first Executive Console design while preserving the current three-column layout, transcript behavior, and backend wiring.

**Architecture:** Keep the current Vite + React transcript flow and API contract, but add a small amount of UI state for the right-side inspection tabs and extract a trace-narrative helper so the Thinking process tab stays derived from the existing trace payload instead of inventing new backend fields. Implement the redesign in focused layers: first lock the behavior with failing tests, then add tab/narrative state, then update the React components, then replace the visual system in CSS, and finally update tracking/docs and rerun Docker-based verification.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, React Testing Library, CSS, Docker Compose.

---

## Planned File Structure

### Frontend chat shell and state
- Modify: `frontend/src/features/chat/ChatPage.tsx` — render the Executive Console shell, add the status pill, upgrade the left rail prompt cards, rename the trace action, and pass the right-panel tab state into `TracePanel`.
- Modify: `frontend/src/features/chat/useChatSession.ts` — track the selected right-panel tab, reset it to Observability on failed requests, and keep the selected reply stable while tabs switch.
- Modify: `frontend/src/features/chat/sampleQuestions.ts` — add short capability titles so the L1-L5 rail can render more professional prompt cards without changing behavior.

### Trace console and derived narrative
- Modify: `frontend/src/features/trace/TracePanel.tsx` — render the sticky tab bar, the Observability tab, and the Thinking process tab.
- Create: `frontend/src/features/trace/buildTraceNarrative.ts` — derive the curated Thinking process narrative from the existing trace payload.
- Modify: `frontend/src/types/chat.ts` — add shared types for the trace tab and narrative steps.

### Styling
- Modify: `frontend/src/styles.css` — replace the current flat light styling with the dark-first Executive Console theme, Inter typography, refined spacing, tab states, selected-reply styling, and right-panel cards.

### Frontend tests
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — cover the tabbed inspection console, the upgraded left rail, the renamed inspect action, selection persistence, and failure behavior.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — cover the always-visible tabs, the Observability view, and the Thinking process narrative view.
- Create: `frontend/src/features/trace/buildTraceNarrative.test.ts` — verify the curated narrative stays deterministic and grounded in the trace payload.

### Tracking and docs
- Modify: `TASKS.md` — add this Executive Console implementation plan to the plan index.
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` — note that transcript and trace-selection behavior remain owned there, while the visual refresh is implemented by this plan.
- Review: `docs/local-dev.md` — keep it unchanged if the existing Docker Compose frontend test/build commands remain accurate.

---

### Task 1: Lock the Executive Console behavior with failing tests

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`
- Create: `frontend/src/features/trace/buildTraceNarrative.test.ts`

- [ ] **Step 1: Replace the chat page tests with Executive Console expectations**

Replace `frontend/src/features/chat/ChatPage.test.tsx` with:

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
  it('renders the question ladder, chat workspace, and inspection tabs before the first answer', () => {
    render(<ChatPage />)

    const demoPanel = screen.getByRole('complementary', { name: 'Quick demo questions' })
    const chatPanel = screen.getByRole('region', { name: 'Chat conversation' })
    const inspectionPanel = screen.getByRole('complementary', { name: 'Inspection console' })

    expect(within(demoPanel).getByText('Question ladder')).toBeInTheDocument()
    expect(
      within(demoPanel).getByText('Explore the L1-L5 progression before writing your own prompt.'),
    ).toBeInTheDocument()
    expect(within(demoPanel).getByRole('button', { name: /L1/i })).toBeInTheDocument()
    expect(within(demoPanel).getByRole('button', { name: /L5/i })).toBeInTheDocument()
    expect(within(chatPanel).getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
    expect(within(chatPanel).getByText('Grounded workspace')).toBeInTheDocument()
    expect(within(inspectionPanel).getByRole('tab', { name: 'Observability' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(within(inspectionPanel).getByRole('tab', { name: 'Thinking process' })).toHaveAttribute(
      'aria-selected',
      'false',
    )
    expect(within(inspectionPanel).getByText('Select a response to inspect evidence and explanation.')).toBeInTheDocument()
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

  it('renders transcript turns, referenced documents, and auto-selects the newest reply in observability mode', async () => {
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
    expect(within(screen.getByRole('article', { name: 'Response 1' })).getByText('ownership.md')).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Response 1' })).getByRole('button', { name: 'Inspect response' })).toBeInTheDocument()
    expect(screen.getByText('Inspecting Response 1.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /L3/i }))
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('PaymentGW current latency is 185 ms.')).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Response 2' })).getByText('monitoring.md')).toBeInTheDocument()
    expect(screen.getByText('Inspecting Response 2.')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Fetched current PaymentGW metrics')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('lets the user switch to the thinking-process tab without losing the selected reply', async () => {
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

    await user.click(screen.getByRole('tab', { name: 'Thinking process' }))

    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('How the answer was formed')).toBeInTheDocument()
    expect(screen.getByText('Checked sources')).toBeInTheDocument()
    expect(screen.getByText('Ran tools')).toBeInTheDocument()
    expect(screen.getByText('Used session context')).toBeInTheDocument()
    expect(screen.getByText('Grounded answer')).toBeInTheDocument()

    const responseOne = screen.getByRole('article', { name: 'Response 1' })
    await user.click(within(responseOne).getByRole('button', { name: 'Inspect response' }))

    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')
    expect(responseOne).toHaveClass('message-card--selected')
    expect(screen.getByText('Reviewed 1 retrieved source: ownership.md.')).toBeInTheDocument()
  })

  it('returns the inspection console to observability when a request fails after the user was reading thinking-process details', async () => {
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

    await user.click(screen.getByRole('tab', { name: 'Thinking process' }))
    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')

    await user.clear(screen.getByPlaceholderText('Ask GeekBrain anything...'))
    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'trigger failure')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate stub response.')
    expect(screen.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Replace the trace panel tests with tabbed-console coverage**

Replace `frontend/src/features/trace/TracePanel.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('renders inspection tabs and empty-state guidance before the first answer', () => {
    render(
      <TracePanel
        trace={null}
        error={null}
        traceLabel={null}
        activeTab="observability"
        onTabChange={() => undefined}
      />,
    )

    expect(screen.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByText('Select a response to inspect evidence and explanation.')).toBeInTheDocument()
  })

  it('renders observability sections when the observability tab is active', () => {
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
        activeTab="observability"
        onTabChange={() => undefined}
      />,
    )

    expect(screen.getByText('Inspecting Response 2.')).toBeInTheDocument()
    expect(screen.getByText('architecture.md')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
  })

  it('renders curated narrative steps when the thinking-process tab is active', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-monitoring',
              title: 'monitoring.md',
              excerpt: 'PaymentGW latency p95 is 185 ms.',
              version: undefined,
              recencyNote: undefined,
            },
          ],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'success',
              summary: 'Fetched current PaymentGW metrics',
              input: { question: 'What is PaymentGW latency?' },
              output: { latency_p95_ms: 185 },
            },
          ],
          memoryWindow: ['Who owns the Notifications service?'],
          groundingNotes: ['Used live monitoring data.'],
          uncertainty: null,
        }}
        error={null}
        traceLabel="Response 2"
        activeTab="thinking"
        onTabChange={() => undefined}
      />,
    )

    expect(screen.getByText('How the answer was formed')).toBeInTheDocument()
    expect(screen.getByText('Checked sources')).toBeInTheDocument()
    expect(screen.getByText('Ran tools')).toBeInTheDocument()
    expect(screen.getByText('Used session context')).toBeInTheDocument()
    expect(screen.getByText('Grounded answer')).toBeInTheDocument()
  })

  it('renders failed-request details on the observability tab', () => {
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
        activeTab="observability"
        onTabChange={() => undefined}
      />,
    )

    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Add a focused unit test for the Thinking process narrative builder**

Create `frontend/src/features/trace/buildTraceNarrative.test.ts`:

```ts
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
```

- [ ] **Step 4: Run the targeted frontend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Expected: FAIL because the current UI still uses the old light styling/copy, `TracePanel` has no tab props, there is no `buildTraceNarrative.ts`, and the chat action still says `View trace`.

- [ ] **Step 5: Commit the failing tests**

```bash
git add frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/trace/TracePanel.test.tsx frontend/src/features/trace/buildTraceNarrative.test.ts
git commit -m "test: define executive console inspection behavior"
```

---

### Task 2: Add trace-tab state and the curated Thinking process builder

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/features/chat/useChatSession.ts`
- Modify: `frontend/src/features/chat/sampleQuestions.ts`
- Create: `frontend/src/features/trace/buildTraceNarrative.ts`

- [ ] **Step 1: Extend the shared frontend types for trace tabs and narrative steps**

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
```

- [ ] **Step 2: Add short capability titles to the L1-L5 sample questions**

Update `frontend/src/features/chat/sampleQuestions.ts` to:

```ts
export const sampleQuestions = [
  {
    level: 'L1',
    title: 'Single-source retrieval',
    prompt: 'Who owns the Notifications service?',
  },
  {
    level: 'L2',
    title: 'Contradiction handling',
    prompt: 'What changed in the on-call escalation policy, and which document is newer?',
  },
  {
    level: 'L3',
    title: 'Live operational metrics',
    prompt: 'What is PaymentGW current latency right now?',
  },
  {
    level: 'L4',
    title: 'Recent-turn continuity',
    prompt: 'Why did its costs spike last month?',
  },
  {
    level: 'L5',
    title: 'Launch-readiness investigation',
    prompt: 'Investigate whether Checkout is healthy enough for a product launch today.',
  },
] as const
```

- [ ] **Step 3: Add a deterministic narrative builder from the existing trace payload**

Create `frontend/src/features/trace/buildTraceNarrative.ts`:

```ts
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
```

- [ ] **Step 4: Track the active inspection tab in chat session state and reset it on errors**

Update `frontend/src/features/chat/useChatSession.ts` to:

```ts
import { useRef, useState } from 'react'

import { postChatMessage } from '../../lib/api'
import type {
  AssistantChatMessage,
  ChatErrorState,
  ConversationMessage,
  TracePanelTab,
  TracePayload,
} from '../../types/chat'

const SESSION_ID = 'phase1-session'

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

const selectedTrace = selectedTraceMessage?.trace ?? null
const selectedTraceLabel = selectedTraceMessage?.label ?? null
```

- [ ] **Step 5: Run the targeted tests again**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Expected: `buildTraceNarrative.test.ts` should PASS, but the UI tests should still FAIL because `ChatPage.tsx` and `TracePanel.tsx` do not yet render the new tabs, labels, or empty-state copy.

- [ ] **Step 6: Commit the state and narrative scaffolding**

```bash
git add frontend/src/types/chat.ts frontend/src/features/chat/sampleQuestions.ts frontend/src/features/chat/useChatSession.ts frontend/src/features/trace/buildTraceNarrative.ts
git commit -m "feat: add trace narrative state"
```

---

### Task 3: Implement the tabbed inspection console and upgraded chat shell

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/trace/TracePanel.tsx`

- [ ] **Step 1: Replace the trace panel with a tabbed inspection console**

Update `frontend/src/features/trace/TracePanel.tsx` to:

```tsx
import type { ChatErrorState, TracePanelTab, TracePayload } from '../../types/chat'

import { buildTraceNarrative } from './buildTraceNarrative'

interface TracePanelProps {
  trace: TracePayload | null
  error: ChatErrorState | null
  traceLabel: string | null
  activeTab: TracePanelTab
  onTabChange: (tab: TracePanelTab) => void
}

export function TracePanel({ trace, error, traceLabel, activeTab, onTabChange }: TracePanelProps) {
  const headerCopy = error
    ? 'Showing request error details.'
    : traceLabel
      ? `Inspecting ${traceLabel}.`
      : 'Always visible for every answer.'

  const isObservability = activeTab === 'observability'
  const narrativeSteps = trace ? buildTraceNarrative(trace) : []

  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Inspection console</h2>
        <p>{headerCopy}</p>
      </header>

      <div className="trace-tabs" role="tablist" aria-label="Inspection views">
        <button
          type="button"
          role="tab"
          aria-selected={isObservability}
          className={`trace-tab${isObservability ? ' trace-tab--active' : ''}`}
          onClick={() => onTabChange('observability')}
        >
          Observability
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isObservability}
          className={`trace-tab${!isObservability ? ' trace-tab--active' : ''}`}
          onClick={() => onTabChange('thinking')}
        >
          Thinking process
        </button>
      </div>

      {isObservability ? (
        error ? (
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
          <p className="trace-empty">Select a response to inspect evidence and explanation.</p>
        )
      ) : trace ? (
        <section className="trace-section trace-section--narrative">
          <h3>How the answer was formed</h3>
          <ol className="trace-narrative">
            {narrativeSteps.map((step) => (
              <li key={step.id} className="trace-step">
                <span className="trace-step__title">{step.title}</span>
                <p>{step.detail}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : (
        <p className="trace-empty">Select a response to inspect evidence and explanation.</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Update the chat page to pass tab state, add the status pill, and rename the inspection action**

Update `frontend/src/features/chat/ChatPage.tsx` to:

```tsx
import type { FormEvent } from 'react'

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
    selectedTraceTab,
    error,
    isSubmitting,
    canSubmit,
    setPrompt,
    applySampleQuestion,
    selectTraceMessage,
    selectTraceTab,
    submitPrompt,
  } = useChatSession()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await submitPrompt()
  }

  return (
    <main className="app-shell">
      <aside className="sample-pane" aria-label="Quick demo questions">
        <div className="sample-pane__content">
          <span className="sample-pane__eyebrow">Question ladder</span>
          <h2>Quick demo questions</h2>
          <p>Explore the L1-L5 progression before writing your own prompt.</p>
          <div className="sample-strip__list">
            {sampleQuestions.map((question) => {
              const isActive = prompt.trim() === question.prompt

              return (
                <button
                  key={question.level}
                  type="button"
                  className={`sample-strip__button${isActive ? ' sample-strip__button--active' : ''}`}
                  onClick={() => applySampleQuestion(question.prompt)}
                >
                  <span className="sample-strip__level">{question.level}</span>
                  <span className="sample-strip__title">{question.title}</span>
                  <span className="sample-strip__prompt">{question.prompt}</span>
                </button>
              )
            })}
          </div>
        </div>
      </aside>

      <section className="chat-pane" aria-label="Chat conversation">
        <header className="chat-header">
          <div>
            <h1>HexaRAG</h1>
            <p>Ask GeekBrain anything.</p>
          </div>
          <span className="chat-status-pill">Grounded workspace</span>
        </header>

        <section className="conversation-thread" aria-live="polite">
          {messages.length === 0 ? (
            <p className="result-empty">Start with a sample question or type your own prompt.</p>
          ) : (
            messages.map((message) => {
              if (message.role === 'assistant') {
                const isSelected = message.id === selectedTraceMessageId

                return (
                  <article
                    key={message.id}
                    aria-label={message.label}
                    className={`message-card message-card--assistant${
                      isSelected ? ' message-card--selected' : ''
                    }`}
                  >
                    <h3>{message.label}</h3>
                    <p>{message.content}</p>

                    {message.trace.citations.length > 0 ? (
                      <section className="message-sources">
                        <h4>Referenced documents</h4>
                        <ul className="message-sources__list">
                          {message.trace.citations.map((citation) => (
                            <li key={citation.sourceId}>{citation.title}</li>
                          ))}
                        </ul>
                      </section>
                    ) : null}

                    <button
                      type="button"
                      className="trace-link"
                      aria-pressed={isSelected}
                      onClick={() => selectTraceMessage(message.id)}
                    >
                      Inspect response
                    </button>
                  </article>
                )
              }

              return (
                <article key={message.id} aria-label="User message" className="message-card message-card--user">
                  <h3>You</h3>
                  <p>{message.content}</p>
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

      <aside className="trace-pane" aria-label="Inspection console">
        <TracePanel
          trace={selectedTrace}
          error={selectedTraceMessageId === null ? error : null}
          traceLabel={selectedTraceLabel}
          activeTab={selectedTraceTab}
          onTabChange={selectTraceTab}
        />
      </aside>
    </main>
  )
}
```

- [ ] **Step 3: Run the targeted tests to make sure the new component behavior passes before touching CSS**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Expected: PASS. At this point, the behavior and copy should be correct even though the visuals are still the old light scaffold.

- [ ] **Step 4: Commit the tabbed console and chat-shell behavior**

```bash
git add frontend/src/features/chat/ChatPage.tsx frontend/src/features/trace/TracePanel.tsx
git commit -m "feat: add tabbed inspection console"
```

---

### Task 4: Apply the Executive Console theme, typography, and interaction styling

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Replace the global stylesheet with the dark-first Executive Console system**

Replace `frontend/src/styles.css` with:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
  color-scheme: dark;
  --bg-app: #0b1020;
  --surface-primary: #12192b;
  --surface-elevated: #17233a;
  --surface-subtle: #0f1627;
  --border-subtle: #26324a;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --accent-primary: #6366f1;
  --accent-observability: #0891b2;
  --accent-success: #10b981;
  --accent-warning: #d97706;
  --accent-error: #dc2626;
  --shadow-panel: 0 18px 48px rgba(2, 6, 23, 0.36);
  --shadow-selected: 0 0 0 1px rgba(99, 102, 241, 0.7), 0 18px 48px rgba(37, 99, 235, 0.16);
  --radius-panel: 20px;
  --radius-card: 18px;
  --radius-pill: 999px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.5;
  color: var(--text-primary);
  background: radial-gradient(circle at top, #15203a 0%, var(--bg-app) 42%);
}

button,
textarea {
  font: inherit;
}

.app-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 380px;
  height: 100vh;
  gap: 0;
  padding: 20px;
}

.sample-pane,
.chat-pane,
.trace-pane {
  min-height: 0;
}

.sample-pane {
  background: rgba(18, 25, 43, 0.94);
  border: 1px solid var(--border-subtle);
  border-right: none;
  border-radius: var(--radius-panel) 0 0 var(--radius-panel);
  box-shadow: var(--shadow-panel);
  overflow-y: auto;
}

.sample-pane__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.sample-pane__eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-observability);
}

.sample-pane__content h2 {
  font-size: 18px;
  font-weight: 600;
}

.sample-pane__content p {
  color: var(--text-secondary);
  font-size: 14px;
}

.sample-strip__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sample-strip__button {
  display: flex;
  min-height: 72px;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  background: rgba(15, 22, 39, 0.9);
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease;
}

.sample-strip__button:hover {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.72);
  background: rgba(23, 35, 58, 0.96);
}

.sample-strip__button--active {
  border-color: rgba(99, 102, 241, 0.9);
  background: linear-gradient(180deg, rgba(23, 35, 58, 0.98), rgba(18, 25, 43, 0.98));
  box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.34);
}

.sample-strip__level {
  font-size: 12px;
  font-weight: 700;
  color: #c7d2fe;
}

.sample-strip__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.sample-strip__prompt {
  font-size: 13px;
  color: var(--text-secondary);
}

.chat-pane {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 0;
  background: rgba(9, 15, 31, 0.92);
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-panel);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 28px 20px;
  border-bottom: 1px solid rgba(38, 50, 74, 0.8);
}

.chat-header h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}

.chat-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.chat-status-pill {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(8, 145, 178, 0.35);
  background: rgba(8, 145, 178, 0.14);
  padding: 0 14px;
  font-size: 13px;
  font-weight: 600;
  color: #bae6fd;
}

.conversation-thread {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
  padding: 24px 28px;
}

.result-empty {
  color: var(--text-secondary);
  font-size: 15px;
}

.message-card {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  padding: 18px;
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.22);
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.message-card h3 {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.message-card--user {
  align-self: flex-end;
  max-width: 72%;
  background: rgba(18, 25, 43, 0.96);
}

.message-card--assistant {
  max-width: 82%;
  background: rgba(23, 35, 58, 0.98);
}

.message-card--selected {
  border-color: rgba(99, 102, 241, 0.78);
  box-shadow: var(--shadow-selected);
}

.message-sources {
  margin-top: 14px;
}

.message-sources h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.message-sources__list {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.message-sources__list li {
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  background: rgba(8, 145, 178, 0.14);
  border: 1px solid rgba(8, 145, 178, 0.2);
  font-size: 12px;
  color: #d7efff;
}

.trace-link {
  margin-top: 14px;
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(99, 102, 241, 0.26);
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.12);
  color: #e0e7ff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0 14px;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease;
}

.trace-link:hover {
  transform: translateY(-1px);
  border-color: rgba(99, 102, 241, 0.6);
  background: rgba(99, 102, 241, 0.18);
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 28px 24px;
  border-top: 1px solid rgba(38, 50, 74, 0.8);
  background: rgba(15, 22, 39, 0.92);
}

.composer textarea {
  width: 100%;
  min-height: 108px;
  padding: 16px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  background: rgba(9, 15, 31, 0.88);
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
}

.composer textarea::placeholder {
  color: #74839f;
}

.composer button {
  align-self: flex-start;
  min-height: 44px;
  padding: 0 18px;
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 180ms ease,
    filter 180ms ease,
    opacity 180ms ease;
}

.composer button:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.composer button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.form-error {
  color: #fecaca;
  font-size: 14px;
}

.trace-pane {
  background: rgba(18, 25, 43, 0.96);
  border: 1px solid var(--border-subtle);
  border-left: none;
  border-radius: 0 var(--radius-panel) var(--radius-panel) 0;
  box-shadow: var(--shadow-panel);
  overflow-y: auto;
  padding: 24px;
}

.trace-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.trace-header h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.trace-header p {
  color: var(--text-secondary);
  font-size: 13px;
}

.trace-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.trace-tab {
  min-height: 44px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: rgba(15, 22, 39, 0.9);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background-color 180ms ease,
    color 180ms ease;
}

.trace-tab:hover {
  transform: translateY(-1px);
  color: var(--text-primary);
}

.trace-tab--active {
  border-color: rgba(99, 102, 241, 0.72);
  background: rgba(99, 102, 241, 0.16);
  color: #e0e7ff;
}

.trace-empty {
  color: var(--text-secondary);
  font-size: 14px;
}

.trace-section {
  background: rgba(15, 22, 39, 0.92);
  padding: 18px;
  border-radius: 18px;
  border: 1px solid var(--border-subtle);
}

.trace-section h3 {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #cbd5e1;
  margin-bottom: 12px;
}

.trace-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trace-list li {
  font-size: 14px;
  color: var(--text-primary);
  padding-left: 14px;
  position: relative;
}

.trace-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--accent-observability);
}

.trace-section--narrative {
  padding-bottom: 14px;
}

.trace-narrative {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trace-step {
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(38, 50, 74, 0.9);
  background: rgba(23, 35, 58, 0.7);
}

.trace-step__title {
  display: inline-block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #e0e7ff;
}

.trace-step p {
  color: var(--text-secondary);
  font-size: 14px;
}

.sample-strip__button:focus-visible,
.trace-link:focus-visible,
.trace-tab:focus-visible,
.composer button:focus-visible,
.composer textarea:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(11, 16, 32, 0.96), 0 0 0 4px rgba(99, 102, 241, 0.78);
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

- [ ] **Step 2: Add responsive rules and reduced-motion handling**

Append this block to the bottom of `frontend/src/styles.css`:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition-duration: 0ms !important;
    scroll-behavior: auto !important;
  }
}

@media (max-width: 1200px) {
  .app-shell {
    grid-template-columns: 240px minmax(0, 1fr) 320px;
    padding: 16px;
  }
}

@media (max-width: 1024px) {
  .app-shell {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .trace-pane {
    border-left: 1px solid var(--border-subtle);
    border-radius: var(--radius-panel);
    margin-left: 16px;
  }
}
```

- [ ] **Step 3: Run the targeted tests and the frontend build**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run && docker compose run --rm frontend npm run build
```

Expected: PASS. The behavior tests should stay green and the new stylesheet should compile through the Vite build.

- [ ] **Step 4: Commit the Executive Console visual system**

```bash
git add frontend/src/styles.css
git commit -m "feat: restyle chat workspace as executive console"
```

---

### Task 5: Update tracking/docs and rerun final verification

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`
- Review: `docs/local-dev.md`

- [ ] **Step 1: Add the new UI-remake plan to the task tracker**

Update the plan index in `TASKS.md` to include:

```md
- `docs/superpowers/plans/2026-05-07-frontend-ui-remake.md` — Executive Console dark-first frontend redesign with tabbed inspection console
```

Place it below the existing `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` entry.

- [ ] **Step 2: Cross-link the older transcript plan to this visual refresh plan**

Add this note near the top of `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` after the Tech Stack line:

```md
**Visual note:** Transcript behavior, per-reply trace selection, and sample-question workflow remain defined here. The Executive Console visual refresh that preserves those behaviors is implemented in `docs/superpowers/plans/2026-05-07-frontend-ui-remake.md`.
```

- [ ] **Step 3: Review `docs/local-dev.md` and leave it unchanged if the Docker commands still match**

Review the frontend local-dev commands.

Expected outcome: no edit needed, because the existing Docker Compose test/build commands still cover the updated frontend flow.

- [ ] **Step 4: Run the final frontend verification commands**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run && docker compose run --rm frontend npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit the tracker and plan updates**

```bash
git add TASKS.md docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md docs/superpowers/plans/2026-05-07-frontend-ui-remake.md
git commit -m "docs: track executive console ui remake"
```

---

## Spec Coverage Check

- **Preserve three-column layout** → Task 4 keeps the grid as three columns on the primary desktop layout while restyling the shell.
- **Keep left rail as the L1-L5 progression** → Task 2 adds titles to `sampleQuestions.ts`, and Task 3 renders them in the upgraded question ladder.
- **Keep the chat center dominant** → Task 3 upgrades the status/header shell and Task 4 gives the center pane the strongest spacing and surface hierarchy.
- **Right panel with two tabs** → Task 3 adds the `Observability` and `Thinking process` tabs to `TracePanel.tsx`.
- **Thinking process must be a trace narrative, not raw reasoning** → Task 2 adds `buildTraceNarrative.ts`, and Task 3 renders it in product language.
- **Dark-first Executive Console theme** → Task 4 replaces the light scaffold with navy/indigo/cyan tokens, Inter typography, and dark surfaces.
- **Subtle motion and accessibility requirements** → Task 4 adds the focus states, transition limits, and reduced-motion block.
- **Error behavior stays integrated in the right panel** → Task 2 resets the active tab to Observability on failure, and Task 3 keeps the error sections in the right panel.
- **Tracking/docs update in the same task** → Task 5 updates `TASKS.md`, cross-links the transcript plan, and reviews `docs/local-dev.md`.

## Placeholder Scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Every code step includes the exact code to add or replace.
- Every verification step includes an exact Docker Compose command and an expected result.
- No step says “similar to Task N” without repeating the needed code.

## Type Consistency Check

Use these exact names throughout execution:
- `TracePanelTab` in `frontend/src/types/chat.ts`
- `TraceNarrativeStep` in `frontend/src/types/chat.ts`
- `selectedTraceTab` and `selectTraceTab` in `frontend/src/features/chat/useChatSession.ts`
- `buildTraceNarrative` in `frontend/src/features/trace/buildTraceNarrative.ts`
- `activeTab` and `onTabChange` props in `frontend/src/features/trace/TracePanel.tsx`
- `Inspect response` as the assistant-card action label in `frontend/src/features/chat/ChatPage.tsx`
- `Observability` and `Thinking process` as the exact tab labels

---

Plan complete and saved to `docs/superpowers/plans/2026-05-07-frontend-ui-remake.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
