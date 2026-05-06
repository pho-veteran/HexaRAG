# Task 3 Frontend Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Vite starter UI with the HexaRAG chat shell and always-visible observability panel, keeping the conversation area blank and deferring all API/session behavior to later tasks.

**Architecture:** Build the shell as a small set of focused frontend files: `ChatPage` owns layout, `TracePanel` owns observability presentation, and `chat.ts` owns the trace type boundary. Keep the implementation intentionally static for this task so the UI shape is stable before Task 5 adds chat state and backend wiring.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library, Docker Compose.

---

**Execution note:** The current user explicitly asked not to create git commits unless they later request them. This plan intentionally omits commit steps.

## Planned File Structure

### Frontend runtime and test files
- Modify: `frontend/package.json` — add the missing `test` script needed by the phase plan’s Docker Compose test commands.
- Create: `frontend/src/types/chat.ts` — minimal trace-oriented frontend types for the shell.
- Create: `frontend/src/features/chat/ChatPage.tsx` — two-pane shell with blank conversation area and inert composer.
- Create: `frontend/src/features/chat/ChatPage.test.tsx` — layout test for heading, composer placeholder, and observability panel presence.
- Create: `frontend/src/features/trace/TracePanel.tsx` — observability panel with null-state guidance and minimal non-null section rendering.
- Create: `frontend/src/features/trace/TracePanel.test.tsx` — empty-state trace panel test.
- Modify: `frontend/src/App.tsx` — thin wrapper that renders `ChatPage`.
- Modify: `frontend/src/main.tsx` — switch the app-wide stylesheet import to `styles.css`.
- Create: `frontend/src/styles.css` — dark two-pane shell styling that stays side-by-side.
- Verify: `frontend/src/test/setup.ts` — keep only `import '@testing-library/jest-dom'`.

### Tracking files
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` — add `frontend/package.json` to Task 3 file ownership, since the generated scaffold does not yet define a `test` script.
- Modify: `TASKS.md` — mark the Phase 1 frontend shell line complete after implementation and verification succeed.

---

### Task 1: Enable targeted frontend tests and write the failing shell tests

**Files:**
- Modify: `frontend/package.json`
- Verify: `frontend/src/test/setup.ts`
- Create: `frontend/src/features/chat/ChatPage.test.tsx`
- Create: `frontend/src/features/trace/TracePanel.test.tsx`

- [ ] **Step 1: Add the frontend test script**

Update the `scripts` block in `frontend/package.json` to include `test`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest",
    "lint": "eslint .",
    "preview": "vite preview"
  }
}
```

- [ ] **Step 2: Confirm the Vitest setup file stays minimal**

`frontend/src/test/setup.ts` should contain only:

```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 3: Write the failing chat shell test**

Create `frontend/src/features/chat/ChatPage.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { ChatPage } from './ChatPage'

describe('ChatPage', () => {
  it('renders the chat shell and observability panel', () => {
    render(<ChatPage />)

    expect(screen.getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask GeekBrain anything...')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Observability' })).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Write the failing trace panel test**

Create `frontend/src/features/trace/TracePanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('shows empty-state guidance before the first answer', () => {
    render(<TracePanel trace={null} />)

    expect(
      screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.'),
    ).toBeInTheDocument()
  })
})
```

- [ ] **Step 5: Run the targeted frontend tests and verify they fail for the expected reason**

Run from `C:\Users\thanh\Desktop\workspace\xbrain\hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: FAIL because `./ChatPage` and `./TracePanel` do not exist yet.

---

### Task 2: Implement the minimal shell components and type boundary

**Files:**
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/features/trace/TracePanel.tsx`
- Create: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create the shared trace types**

Create `frontend/src/types/chat.ts`:

```ts
export type ChatRole = 'user' | 'assistant'

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
  conflictResolution?: {
    chosenSource: string
    rationale: string
    competingSources: string[]
  }
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty?: string
}
```

- [ ] **Step 2: Create the trace panel component**

Create `frontend/src/features/trace/TracePanel.tsx`:

```tsx
import type { TracePayload } from '../../types/chat'

interface TracePanelProps {
  trace: TracePayload | null
}

export function TracePanel({ trace }: TracePanelProps) {
  if (!trace) {
    return (
      <div className="trace-panel">
        <header className="trace-header">
          <h2>Observability</h2>
          <p>Always visible for every answer.</p>
        </header>

        <p className="trace-empty">
          Send a question to inspect retrieval, tools, memory, and grounding.
        </p>
      </div>
    )
  }

  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Observability</h2>
        <p>Always visible for every answer.</p>
      </header>

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
          {trace.toolCalls.map((tool) => (
            <li key={tool.name}>
              {tool.name}: {tool.summary}
            </li>
          ))}
        </ul>
      </section>

      <section className="trace-section">
        <h3>Memory</h3>
        <ul className="trace-list">
          {trace.memoryWindow.map((entry) => (
            <li key={entry}>{entry}</li>
          ))}
        </ul>
      </section>

      <section className="trace-section">
        <h3>Grounding</h3>
        <ul className="trace-list">
          {trace.groundingNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      {trace.uncertainty ? (
        <section className="trace-section">
          <h3>Uncertainty</h3>
          <p>{trace.uncertainty}</p>
        </section>
      ) : null}
    </div>
  )
}
```

- [ ] **Step 3: Create the chat shell component**

Create `frontend/src/features/chat/ChatPage.tsx`:

```tsx
import { TracePanel } from '../trace/TracePanel'

export function ChatPage() {
  return (
    <main className="app-shell">
      <section className="chat-pane">
        <header className="chat-header">
          <h1>HexaRAG</h1>
          <p>Ask GeekBrain anything.</p>
        </header>

        <div className="message-thread" aria-label="Conversation history" />

        <form className="composer">
          <textarea placeholder="Ask GeekBrain anything..." rows={3} />
          <button type="button">Send</button>
        </form>
      </section>

      <aside className="trace-pane">
        <TracePanel trace={null} />
      </aside>
    </main>
  )
}
```

- [ ] **Step 4: Simplify the app wrapper**

Replace `frontend/src/App.tsx` with:

```tsx
import { ChatPage } from './features/chat/ChatPage'

export default function App() {
  return <ChatPage />
}
```

- [ ] **Step 5: Run the targeted tests and verify the new components go green before styling work**

Run from `C:\Users\thanh\Desktop\workspace\xbrain\hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: PASS.

---

### Task 3: Replace the Vite starter styling with the HexaRAG shell styling

**Files:**
- Create: `frontend/src/styles.css`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Create the app-wide shell stylesheet**

Create `frontend/src/styles.css`:

```css
:root {
  color: #e5e7eb;
  background: #020617;
  font-family: Inter, system-ui, sans-serif;
  line-height: 1.5;
  font-weight: 400;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}

html,
body,
#root {
  min-height: 100%;
}

body {
  margin: 0;
  min-height: 100vh;
  background: #020617;
}

button,
textarea {
  font: inherit;
}

#root {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  min-width: 840px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
}

.chat-pane {
  min-width: 0;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-header {
  display: grid;
  gap: 8px;
}

.chat-header h1 {
  margin: 0;
  font-size: 2.5rem;
  line-height: 1.1;
  color: #f8fafc;
}

.chat-header p {
  margin: 0;
  color: #94a3b8;
}

.message-thread {
  flex: 1;
  min-height: 320px;
  border: 1px dashed #334155;
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.72);
}

.composer {
  display: grid;
  gap: 12px;
}

.composer textarea {
  width: 100%;
  min-height: 96px;
  resize: vertical;
  border: 1px solid #334155;
  border-radius: 18px;
  background: #0f172a;
  color: #e5e7eb;
  padding: 16px;
}

.composer textarea::placeholder {
  color: #64748b;
}

.composer button {
  justify-self: end;
  border: 0;
  border-radius: 999px;
  background: #7c3aed;
  color: #f8fafc;
  padding: 10px 18px;
  font-weight: 600;
}

.trace-pane {
  min-width: 0;
  padding: 32px 24px;
  border-left: 1px solid #1e293b;
  background: #0b1120;
}

.trace-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.trace-header {
  display: grid;
  gap: 8px;
}

.trace-header h2 {
  margin: 0;
  color: #f8fafc;
  font-size: 1.5rem;
}

.trace-header p {
  margin: 0;
  color: #94a3b8;
}

.trace-empty,
.trace-section {
  border-radius: 20px;
  background: rgba(15, 23, 42, 0.72);
  padding: 18px;
}

.trace-empty {
  border: 1px dashed #334155;
  color: #94a3b8;
}

.trace-section {
  border: 1px solid #1e293b;
}

.trace-section h3 {
  margin: 0 0 12px;
  font-size: 1rem;
  color: #cbd5e1;
}

.trace-section p {
  margin: 0;
  color: #94a3b8;
}

.trace-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px;
}

.trace-list li {
  color: #94a3b8;
}

@media (max-width: 980px) {
  .app-shell {
    min-width: 760px;
    grid-template-columns: minmax(0, 1fr) 320px;
  }

  .chat-pane {
    padding: 24px;
  }

  .trace-pane {
    padding: 24px 20px;
  }

  .chat-header h1 {
    font-size: 2rem;
  }
}
```

- [ ] **Step 2: Point the entrypoint at the new stylesheet**

Replace the stylesheet import in `frontend/src/main.tsx` so the file becomes:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 3: Run the targeted tests again after styling changes**

Run from `C:\Users\thanh\Desktop\workspace\xbrain\hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: PASS.

- [ ] **Step 4: Run the frontend build and verify the shell compiles cleanly**

Run from `C:\Users\thanh\Desktop\workspace\xbrain\hexarag`:

```bash
docker compose run --rm frontend npm run build
```

Expected: PASS and Vite emits the production bundle with no build errors.

---

### Task 4: Align the phase tracking files with the implemented Task 3 work

**Files:**
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Add `frontend/package.json` to the foundation plan’s Task 3 file list**

Update the Task 3 file list in `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` so it includes:

```md
- Modify: `frontend/package.json`
```

Place it with the other Task 3 frontend files.

- [ ] **Step 2: Mark the Phase 1 frontend shell item complete in `TASKS.md`**

Change this line in `TASKS.md`:

```md
- [ ] Build the frontend shell with the persistent observability panel
```

To:

```md
- [x] Build the frontend shell with the persistent observability panel
```

- [ ] **Step 3: Re-read the changed tracking files to verify they match the implementation**

Check that:
- `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` now acknowledges the `frontend/package.json` change
- `TASKS.md` shows Task 3 complete
- no unrelated tracking lines changed

---

## Spec Coverage Check

- **Replace starter UI with HexaRAG shell** → Tasks 2 and 3
- **Blank conversation area** → Task 2
- **Persistent right-side observability panel** → Tasks 2 and 3
- **Low-fidelity skeleton only** → Tasks 2 and 3
- **Strict TDD with failing layout tests first** → Task 1, then Task 2 verification
- **Docker Compose-only verification** → Task 1 Step 5, Task 2 Step 5, Task 3 Steps 3-4
- **Docs/tracking update before completion** → Task 4

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each code-changing step includes the exact code to add or replace.
- Commit steps are intentionally omitted because the current user has not asked for commits.

## Type Consistency Check

Keep these names aligned during implementation:
- `TracePayload.citations`
- `TracePayload.toolCalls`
- `TracePayload.memoryWindow`
- `TracePayload.groundingNotes`
- `trace: TracePayload | null`
- the empty-state copy `Send a question to inspect retrieval, tools, memory, and grounding.`

Do not introduce camelCase/snake_case drift inside the frontend shell task.
