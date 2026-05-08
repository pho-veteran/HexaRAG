import { useRef, useState, type FormEvent, type MutableRefObject } from 'react'

import type { AssistantChatMessage, Citation, TracePanelTab, TracePayload } from '../../types/chat'
import { TracePanel } from '../trace/TracePanel'
import { CitationDetailModal } from './CitationDetailModal'
import { InlineCitationText } from './InlineCitationText'
import { sampleQuestions } from './sampleQuestions'
import { useChatSession } from './useChatSession'

const mockPreviewAnswer = 'Team Mercury owns the Notifications service.'

const mockPreviewTrace: TracePayload = {
  citations: [
    {
      sourceId: 'doc-ownership',
      title: 'ownership.md',
      excerpt: 'Notifications is owned by Team Mercury.',
      version: '2026-04-30',
      recencyNote: 'Updated 2026-04-30.',
    },
  ],
  inlineCitations: [
    {
      start: 0,
      end: mockPreviewAnswer.length,
      sourceIds: ['doc-ownership'],
    },
  ],
  toolCalls: [
    {
      name: 'monitoring_snapshot',
      status: 'success',
      summary: 'Fetched current PaymentGW metrics',
      input: { question: 'What is PaymentGW current latency right now?' },
      output: { latency_p95_ms: 185, error_rate_pct: 0.12 },
    },
  ],
  memoryWindow: ['Who owns the Notifications service?'],
  groundingNotes: ['Used the ownership document and live monitoring snapshot.'],
  uncertainty: null,
  runtime: {
    mode: 'stub',
    provider: 'stub-runtime',
    model: 'deterministic-stub',
  },
  reasoning: {
    evidenceTypes: ['retrieval', 'tool', 'memory'],
    selectedSources: ['ownership.md'],
    toolBasis: ['monitoring_snapshot'],
    memoryApplied: true,
    memorySummary: 'Used 1 recent conversation item to keep the answer on topic.',
    uncertaintyReason: null,
    answerStrategy: 'grounded-answer',
    runtimeLabel: 'deterministic-stub via stub-runtime',
    caveat: null,
    sourceSummary: 'Selected 1 source that directly shaped the answer.',
    toolSummary: 'Used 1 tool result in the final answer.',
    explanationSummary: 'The answer combined retrieved evidence, live tool data, and recent conversation context.',
    narrativeFocus: 'evidence-synthesis',
    nextStep: undefined,
    conflictSummary: undefined,
  },
}

const mockPreviewMessages: Array<
  | {
      id: string
      role: 'user'
      content: string
    }
  | AssistantChatMessage
> = [
  {
    id: 'mock-user-1',
    role: 'user',
    content: 'Who owns the Notifications service?',
  },
  {
    id: 'mock-assistant-1',
    role: 'assistant',
    label: 'Response 1',
    content: mockPreviewAnswer,
    trace: mockPreviewTrace,
  },
  {
    id: 'mock-user-2',
    role: 'user',
    content: 'What is PaymentGW current latency right now?',
  },
]

export function ChatPage() {
  const [isMockupOpen, setIsMockupOpen] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [activeCitationKey, setActiveCitationKey] = useState<string | null>(null)
  const [mockupSelectedCitation, setMockupSelectedCitation] = useState<Citation | null>(null)
  const [mockupActiveCitationKey, setMockupActiveCitationKey] = useState<string | null>(null)
  const [mockupTraceTab, setMockupTraceTab] = useState<TracePanelTab>('observability')
  const citationRowRefs = useRef<Record<string, HTMLButtonElement | null>>({})
  const mockupCitationRowRefs = useRef<Record<string, HTMLButtonElement | null>>({})
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

  const buildCitationKey = (messageId: string, sourceId: string) => `${messageId}:${sourceId}`

  const handleCitationSelection = (
    messageId: string,
    citation: Citation,
    setCitation: (citation: Citation) => void,
    setActiveKey: (key: string) => void,
  ) => {
    setActiveKey(buildCitationKey(messageId, citation.sourceId))
    setCitation(citation)
  }

  const handleInlineCitationClick = (
    messageId: string,
    sourceId: string,
    citations: Citation[],
    refs: MutableRefObject<Record<string, HTMLButtonElement | null>>,
    setCitation: (citation: Citation) => void,
    setActiveKey: (key: string) => void,
  ) => {
    const citation = citations.find((item) => item.sourceId === sourceId)
    if (!citation) {
      return
    }

    const citationKey = buildCitationKey(messageId, sourceId)
    setActiveKey(citationKey)
    setCitation(citation)
    refs.current[citationKey]?.focus()
  }

  const renderCitationList = (
    messageId: string,
    citations: Citation[],
    activeCitationKey: string | null,
    refs: MutableRefObject<Record<string, HTMLButtonElement | null>>,
    onSelect: (citation: Citation) => void,
  ) => (
    <section className="message-sources">
      <h4>Referenced documents</h4>
      <ul className="message-sources__list">
        {citations.map((citation) => {
          const citationKey = buildCitationKey(messageId, citation.sourceId)

          return (
            <li key={citation.sourceId}>
              <button
                type="button"
                ref={(node) => {
                  refs.current[citationKey] = node
                }}
                className={`citation-row${activeCitationKey === citationKey ? ' citation-row--active' : ''}`}
                onClick={() => onSelect(citation)}
              >
                {citation.title}
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )

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
                    <InlineCitationText
                      content={message.content}
                      citations={message.trace.citations}
                      inlineCitations={message.trace.inlineCitations}
                      onCitationClick={(sourceId) =>
                        handleInlineCitationClick(
                          message.id,
                          sourceId,
                          message.trace.citations,
                          citationRowRefs,
                          setSelectedCitation,
                          setActiveCitationKey,
                        )
                      }
                    />

                    {message.trace.citations.length > 0
                      ? renderCitationList(
                          message.id,
                          message.trace.citations,
                          activeCitationKey,
                          citationRowRefs,
                          (citation) =>
                            handleCitationSelection(
                              message.id,
                              citation,
                              setSelectedCitation,
                              setActiveCitationKey,
                            ),
                        )
                      : null}

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
          onOpenMockup={() => {
            setMockupTraceTab('observability')
            setMockupSelectedCitation(null)
            setMockupActiveCitationKey(null)
            setIsMockupOpen(true)
          }}
        />
      </aside>

      <CitationDetailModal citation={selectedCitation} onClose={() => setSelectedCitation(null)} />

      {isMockupOpen ? (
        <div className="mockup-backdrop" role="presentation">
          <section className="mockup-dialog" role="dialog" aria-modal="true" aria-label="Frontend mockup">
            <div className="mockup-dialog__topbar">
              <p>Static visual testing surface using the real UI components.</p>
              <button
                type="button"
                className="mockup-dialog__close"
                onClick={() => {
                  setMockupSelectedCitation(null)
                  setMockupTraceTab('observability')
                  setIsMockupOpen(false)
                }}
              >
                Close mockup
              </button>
            </div>

            <main className="app-shell mockup-app-shell">
              <aside className="sample-pane" aria-label="Quick demo questions">
                <div className="sample-pane__content">
                  <span className="sample-pane__eyebrow">Question ladder</span>
                  <h2>Quick demo questions</h2>
                  <p>Explore the L1-L5 progression before writing your own prompt.</p>
                  <div className="sample-strip__list">
                    {sampleQuestions.map((question, index) => (
                      <button
                        key={`mockup-${question.level}`}
                        type="button"
                        className={`sample-strip__button${index === 2 ? ' sample-strip__button--active' : ''}`}
                      >
                        <span className="sample-strip__level">{question.level}</span>
                        <span className="sample-strip__title">{question.title}</span>
                        <span className="sample-strip__prompt">{question.prompt}</span>
                      </button>
                    ))}
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
                  {mockPreviewMessages.map((message) => {
                    if (message.role === 'assistant') {
                      return (
                        <article
                          key={message.id}
                          aria-label={message.label}
                          className="message-card message-card--assistant message-card--selected"
                        >
                          <h3>{message.label}</h3>
                          <InlineCitationText
                            content={message.content}
                            citations={message.trace.citations}
                            inlineCitations={message.trace.inlineCitations}
                            onCitationClick={(sourceId) =>
                              handleInlineCitationClick(
                                message.id,
                                sourceId,
                                message.trace.citations,
                                mockupCitationRowRefs,
                                setMockupSelectedCitation,
                                setMockupActiveCitationKey,
                              )
                            }
                          />

                          {renderCitationList(
                            message.id,
                            message.trace.citations,
                            mockupActiveCitationKey,
                            mockupCitationRowRefs,
                            (citation) =>
                              handleCitationSelection(
                                message.id,
                                citation,
                                setMockupSelectedCitation,
                                setMockupActiveCitationKey,
                              ),
                          )}

                          <button type="button" className="trace-link" aria-pressed="true">
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
                  })}
                </section>

                <form className="composer" onSubmit={(event) => event.preventDefault()}>
                  <label className="sr-only" htmlFor="mockup-chat-message">
                    Question
                  </label>
                  <textarea id="mockup-chat-message" placeholder="Ask GeekBrain anything..." rows={3} defaultValue="" />
                  <button type="submit">Send</button>
                </form>
              </section>

              <aside className="trace-pane" aria-label="Inspection console">
                <TracePanel
                  trace={mockPreviewTrace}
                  error={null}
                  traceLabel="Response 1"
                  activeTab={mockupTraceTab}
                  onTabChange={setMockupTraceTab}
                  onOpenMockup={() => undefined}
                />
              </aside>
            </main>

            <CitationDetailModal
              citation={mockupSelectedCitation}
              onClose={() => setMockupSelectedCitation(null)}
            />
          </section>
        </div>
      ) : null}
    </main>
  )
}
