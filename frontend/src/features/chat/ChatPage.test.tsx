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

  it('shows a sending state while waiting for the backend', async () => {
    let resolveFetch: ((value: Response) => void) | undefined
    fetchMock.mockReturnValue(
      new Promise<Response>((resolve) => {
        resolveFetch = resolve
      }),
    )

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'Check PaymentGW SLA')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(screen.getByRole('button', { name: 'Sending...' })).toBeDisabled()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()

    resolveFetch?.({
      ok: true,
      json: async () => ({
        session_id: 'phase1-session',
        message: {
          role: 'assistant',
          content: 'done',
          trace: {
            citations: [],
            tool_calls: [],
            memory_window: [],
            grounding_notes: [],
            uncertainty: null,
          },
        },
      }),
    } as Response)

    expect(await screen.findByText('done')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled()
    expect(screen.getByPlaceholderText('Ask GeekBrain anything...')).toHaveValue('')
  })

  it('renders a degraded success response without switching into hard-failure UI', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'phase1-session',
        message: {
          role: 'assistant',
          content: 'Could not complete the live tool step. Here is the best grounded fallback available right now.',
          trace: {
            citations: [],
            tool_calls: [
              {
                name: 'monitoring_snapshot',
                status: 'error',
                summary: 'Live monitoring call failed.',
                input: { question: 'What is NotificationSvc status?' },
                output: null,
              },
            ],
            memory_window: ['What is PaymentGW latency?', 'Stub answer for: What is PaymentGW latency?'],
            grounding_notes: ['Returned fallback answer because the live tool step failed.'],
            uncertainty: 'Live monitoring data is temporarily unavailable.',
          },
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'What is NotificationSvc status?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(
      await screen.findByText(
        'Could not complete the live tool step. Here is the best grounded fallback available right now.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText('Request failed')).not.toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Live monitoring call failed.')).toBeInTheDocument()
    expect(screen.getByText('Live monitoring data is temporarily unavailable.')).toBeInTheDocument()
    expect(screen.getByText('Returned fallback answer because the live tool step failed.')).toBeInTheDocument()
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
