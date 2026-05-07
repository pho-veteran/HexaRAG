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
  it('renders the question ladder, chat workspace, inspection tabs, and mockup trigger before the first answer', () => {
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
    expect(
      within(inspectionPanel).getByText('Select a response to inspect evidence and explanation.'),
    ).toBeInTheDocument()
    expect(within(inspectionPanel).getByRole('button', { name: 'Open frontend mockup' })).toBeInTheDocument()
  })

  it('lets the frontend mockup open and switch from observability to thinking process and back', async () => {
    const user = userEvent.setup()
    render(<ChatPage />)

    await user.click(screen.getByRole('button', { name: 'Open frontend mockup' }))

    const dialog = screen.getByRole('dialog', { name: 'Frontend mockup' })
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()

    await user.click(within(dialog).getByRole('tab', { name: 'Thinking process' }))
    expect(within(dialog).getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')
    expect(within(dialog).getByText('How the answer was formed')).toBeInTheDocument()

    await user.click(within(dialog).getByRole('tab', { name: 'Observability' }))
    expect(within(dialog).getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
  })

  it('lets the frontend mockup open citation details from response 1, close the modal, and then close the mockup', async () => {
    const user = userEvent.setup()
    render(<ChatPage />)

    await user.click(screen.getByRole('button', { name: 'Open frontend mockup' }))

    const dialog = screen.getByRole('dialog', { name: 'Frontend mockup' })
    const responseOne = within(dialog).getByRole('article', { name: 'Response 1' })
    await user.click(within(responseOne).getByRole('button', { name: 'ownership.md' }))

    const citationModal = within(dialog).getByRole('dialog', { name: 'Citation details' })
    expect(within(citationModal).getByRole('heading', { name: 'ownership.md' })).toBeInTheDocument()
    expect(within(citationModal).getByText('Notifications is owned by Team Mercury.')).toBeInTheDocument()
    expect(within(citationModal).getByText('Updated 2026-04-30.')).toBeInTheDocument()

    await user.click(within(citationModal).getByRole('button', { name: 'Close citation details' }))
    expect(within(dialog).queryByRole('dialog', { name: 'Citation details' })).not.toBeInTheDocument()

    await user.click(within(dialog).getByRole('button', { name: 'Close mockup' }))
    expect(screen.queryByRole('dialog', { name: 'Frontend mockup' })).not.toBeInTheDocument()
  })

  it('fills the composer when a sample prompt is clicked without sending a request', async () => {
    const user = userEvent.setup()
    render(<ChatPage />)

    await user.click(screen.getByRole('button', { name: /L3/i }))

    expect(screen.getByRole('textbox', { name: 'Question' })).toHaveValue(
      'What is PaymentGW current latency right now?',
    )
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('opens citation details from a live assistant reply and closes them cleanly', async () => {
    fetchMock.mockResolvedValueOnce({
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
                version: '2026-04-30',
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

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    const responseOne = await screen.findByRole('article', { name: 'Response 1' })
    await user.click(within(responseOne).getByRole('button', { name: 'ownership.md' }))

    const modal = screen.getByRole('dialog', { name: 'Citation details' })
    expect(within(modal).getByRole('heading', { name: 'ownership.md' })).toBeInTheDocument()
    expect(within(modal).getByText('Notifications is owned by Team Mercury.')).toBeInTheDocument()
    expect(within(modal).getByText('2026-04-30')).toBeInTheDocument()
    expect(within(modal).getByText('Updated 2026-04-30.')).toBeInTheDocument()

    await user.click(within(modal).getByRole('button', { name: 'Close citation details' }))

    expect(screen.queryByRole('dialog', { name: 'Citation details' })).not.toBeInTheDocument()
  })

  it('focuses the matching citation row and opens the modal when an inline marker is clicked', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session_id: 'phase1-session',
        message: {
          role: 'assistant',
          content: 'Team Mercury owns the Notifications service. Mercury also handles escalations.',
          trace: {
            citations: [
              {
                source_id: 'doc-ownership',
                title: 'ownership.md',
                excerpt: 'Notifications is owned by Team Mercury.',
                version: '2026-04-30',
                recency_note: 'Updated 2026-04-30.',
              },
              {
                source_id: 'doc-escalation',
                title: 'escalation.md',
                excerpt: 'Mercury handles after-hours escalations.',
                version: null,
                recency_note: null,
              },
            ],
            inline_citations: [
              { start: 0, end: 42, source_ids: ['doc-ownership'] },
              { start: 43, end: 76, source_ids: ['doc-ownership', 'doc-escalation'] },
            ],
            tool_calls: [],
            memory_window: [],
            grounding_notes: ['Grounded in ownership and escalation documents.'],
            uncertainty: null,
          },
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns Notifications and escalations?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    const responseOne = await screen.findByRole('article', { name: 'Response 1' })
    await user.click(within(responseOne).getAllByRole('button', { name: '[1]' })[1])

    const ownershipRow = within(responseOne).getByRole('button', { name: 'ownership.md' })
    expect(ownershipRow).toHaveFocus()
    expect(ownershipRow).toHaveClass('citation-row--active')
    expect(screen.getByRole('dialog', { name: 'Citation details' })).toBeInTheDocument()

    await user.click(within(responseOne).getByRole('button', { name: '[2]' }))
    expect(within(responseOne).getByRole('button', { name: 'escalation.md' })).toHaveFocus()
  })

  it('restarts citation numbering for each assistant response', async () => {
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
              inline_citations: [{ start: 0, end: 42, source_ids: ['doc-ownership'] }],
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
              inline_citations: [{ start: 0, end: 35, source_ids: ['doc-monitoring'] }],
              tool_calls: [],
              memory_window: [],
              grounding_notes: ['Used live monitoring data.'],
              uncertainty: null,
            },
          },
        }),
      } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByRole('article', { name: 'Response 1' })

    await user.click(screen.getByRole('button', { name: /L3/i }))
    await user.click(screen.getByRole('button', { name: 'Send' }))

    const responseTwo = await screen.findByRole('article', { name: 'Response 2' })
    expect(within(responseTwo).getByRole('button', { name: '[1]' })).toBeInTheDocument()
  })

  it('renders plain text and the citation list when inline citation metadata is absent', async () => {
    fetchMock.mockResolvedValueOnce({
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
            tool_calls: [],
            memory_window: [],
            grounding_notes: ['Grounded in the ownership document.'],
            uncertainty: null,
          },
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    const responseOne = await screen.findByRole('article', { name: 'Response 1' })
    expect(within(responseOne).getByText('Team Mercury owns the Notifications service.')).toBeInTheDocument()
    expect(within(responseOne).queryByRole('button', { name: '[1]' })).not.toBeInTheDocument()
    expect(within(responseOne).getByRole('button', { name: 'ownership.md' })).toBeInTheDocument()
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

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Team Mercury owns the Notifications service.')).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Response 1' })).getByText('ownership.md')).toBeInTheDocument()
    expect(
      within(screen.getByRole('article', { name: 'Response 1' })).getByRole('button', {
        name: 'Inspect response',
      }),
    ).toBeInTheDocument()
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

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
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

    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'Who owns the Notifications service?')
    await user.click(screen.getByRole('button', { name: 'Send' }))
    await screen.findByText('Team Mercury owns the Notifications service.')

    await user.click(screen.getByRole('tab', { name: 'Thinking process' }))
    expect(screen.getByRole('tab', { name: 'Thinking process' })).toHaveAttribute('aria-selected', 'true')

    await user.clear(screen.getByRole('textbox', { name: 'Question' }))
    await user.type(screen.getByRole('textbox', { name: 'Question' }), 'trigger failure')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate stub response.')
    expect(screen.getByRole('tab', { name: 'Observability' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
