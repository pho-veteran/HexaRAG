import { render, screen } from '@testing-library/react'
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
  it('renders the single-turn form with empty latest-result and observability states', () => {
    render(<ChatPage />)

    expect(screen.getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Latest result' })).toBeInTheDocument()
    expect(screen.getByText('Send one question to inspect the stubbed backend response.')).toBeInTheDocument()
    expect(screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.')).toBeInTheDocument()
  })

  it('submits a question and renders the assistant reply plus observability data', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'phase1-session',
        message: {
          role: 'assistant',
          content: 'Stub answer for: What is PaymentGW current latency?',
          trace: {
            citations: [
              {
                source_id: 'doc-architecture',
                title: 'architecture.md',
                excerpt: 'Current p95 latency sits below the alert threshold.',
                version: null,
                recency_note: 'Stubbed knowledge base note.',
              },
            ],
            tool_calls: [
              {
                name: 'monitoring_snapshot',
                status: 'success',
                summary: 'Prepared stub observability data',
                input: { question: 'What is PaymentGW current latency?' },
                output: { mode: 'stub', latency_p95_ms: 185 },
              },
            ],
            memory_window: ['No prior turns in Phase 1 single-turn mode.'],
            grounding_notes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
            uncertainty: 'Live systems are not wired in this slice.',
          },
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'What is PaymentGW current latency?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Stub answer for: What is PaymentGW current latency?')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/chat',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('renders inline error, latest-result error state, and observability error details', async () => {
    fetchMock.mockResolvedValue({
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

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'trigger failure')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate stub response.')
    expect(screen.getByText('Request failed')).toBeInTheDocument()
    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled()
    expect(screen.getByPlaceholderText('Ask GeekBrain anything...')).toHaveValue('trigger failure')
  })
})
