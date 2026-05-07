import type { FormEvent } from 'react'

import { TracePanel } from '../trace/TracePanel'
import { useChatSession } from './useChatSession'

export function ChatPage() {
  const { prompt, latestMessage, error, isSubmitting, canSubmit, setPrompt, submitPrompt } =
    useChatSession()

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

        <section className="latest-result" aria-live="polite">
          <h2>Latest result</h2>
          {latestMessage ? (
            <article className="result-card">
              <h3>Assistant</h3>
              <p>{latestMessage.content}</p>
            </article>
          ) : error ? (
            <article className="result-card result-card--error">
              <h3>Request failed</h3>
              <p>{error.message}</p>
            </article>
          ) : (
            <p className="result-empty">Send one question to inspect the stubbed backend response.</p>
          )}
        </section>
      </section>

      <aside className="trace-pane">
        <TracePanel trace={latestMessage?.trace ?? null} error={error} />
      </aside>
    </main>
  )
}
