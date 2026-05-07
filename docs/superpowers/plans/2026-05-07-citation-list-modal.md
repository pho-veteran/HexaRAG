# Citation List + Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace assistant citation chips with a row-by-row clickable document list, show excerpt/metadata in a citation modal, and make the frontend mockup interactive enough to validate tab switching and citation modal behavior.

**Refinement note:** The current citation experience now includes inline numbered markers inside assistant answers. Those markers map to the same deduplicated referenced-documents list, reuse the same per-answer source number for repeated references, and open the existing citation detail modal through the same page-level citation-selection flow.

**Architecture:** Keep citation selection state in `ChatPage.tsx` so the live chat and the mockup dialog can each control their own citation-detail modal without changing the backend contract. Introduce one small presentational modal component for citation details, reuse the existing `Citation` model from `frontend/src/types/chat.ts`, and keep `TracePanel.tsx` focused on tab rendering rather than teaching it about citation selection.

**Tech Stack:** React 19, TypeScript, Vite, Vitest, React Testing Library, Docker Compose.

---

## Planned File Structure

### Frontend chat UI
- Create: `frontend/src/features/chat/CitationDetailModal.tsx` — focused presentational modal for title, excerpt, and optional citation metadata.
- Modify: `frontend/src/features/chat/ChatPage.tsx` — live citation selection state, mockup interactive state, vertical citation-row rendering, and modal wiring.
- Modify: `frontend/src/styles.css` — citation-row list styling, modal styling, and mockup interactivity overrides.

### Frontend tests
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — live citation modal behavior and interactive mockup coverage.

### Tracking and docs
- Modify: `TASKS.md` — index this refinement plan alongside the existing frontend plans.
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` — extend the refinement note so it matches the row-by-row citation list and interactive mockup behavior.
- Review: `docs/local-dev.md` — keep unchanged unless the verification commands changed.

---

### Task 1: Lock the citation-row and modal behavior with failing tests

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`

- [ ] **Step 1: Add a failing live citation-modal test**

Update `frontend/src/features/chat/ChatPage.test.tsx` by inserting this test after the existing “fills the composer” test:

```tsx
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

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'Who owns the Notifications service?')
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
```

- [ ] **Step 2: Replace the mockup-dialog test with interactive mockup coverage**

Replace the current “opens and closes the frontend mockup dialog for visual review” test with:

```tsx
  it('lets the frontend mockup switch tabs and open citation details', async () => {
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
```

- [ ] **Step 3: Run the targeted test to verify it fails**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx --run
```

Expected: FAIL because live citations are plain list text rather than buttons, no citation-detail modal exists, and the mockup keeps tabs and chat internals non-interactive.

- [ ] **Step 4: Commit the failing test coverage**

```bash
git add frontend/src/features/chat/ChatPage.test.tsx
git commit -m "test: define citation modal ui behavior"
```

---

### Task 2: Add the citation-detail modal and wire live/mockup state

**Files:**
- Create: `frontend/src/features/chat/CitationDetailModal.tsx`
- Modify: `frontend/src/features/chat/ChatPage.tsx`

- [ ] **Step 1: Create the focused citation modal component**

Create `frontend/src/features/chat/CitationDetailModal.tsx`:

```tsx
import type { Citation } from '../../types/chat'

interface CitationDetailModalProps {
  citation: Citation | null
  onClose: () => void
}

export function CitationDetailModal({ citation, onClose }: CitationDetailModalProps) {
  if (citation === null) {
    return null
  }

  const hasMetadata = Boolean(citation.version || citation.recencyNote)

  return (
    <div
      className="citation-modal-backdrop"
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <section className="citation-modal" role="dialog" aria-modal="true" aria-label="Citation details">
        <div className="citation-modal__header">
          <div>
            <p className="citation-modal__eyebrow">Source document</p>
            <h2>{citation.title}</h2>
          </div>
          <button type="button" className="citation-modal__close" onClick={onClose}>
            Close citation details
          </button>
        </div>

        <section className="citation-modal__section">
          <h3>Excerpt</h3>
          <p>{citation.excerpt}</p>
        </section>

        {hasMetadata ? (
          <section className="citation-modal__section citation-modal__section--meta">
            <h3>Metadata</h3>
            <ul className="citation-modal__meta">
              {citation.version ? (
                <li>
                  <strong>Version:</strong> {citation.version}
                </li>
              ) : null}
              {citation.recencyNote ? (
                <li>
                  <strong>Recency:</strong> {citation.recencyNote}
                </li>
              ) : null}
            </ul>
          </section>
        ) : null}
      </section>
    </div>
  )
}
```

- [ ] **Step 2: Add live and mockup citation-selection state to `ChatPage.tsx`**

Update the import block and top-level state in `frontend/src/features/chat/ChatPage.tsx` to:

```tsx
import { useState, type FormEvent } from 'react'

import type { AssistantChatMessage, Citation, TracePanelTab, TracePayload } from '../../types/chat'
import { TracePanel } from '../trace/TracePanel'
import { CitationDetailModal } from './CitationDetailModal'
import { sampleQuestions } from './sampleQuestions'
import { useChatSession } from './useChatSession'
```

```tsx
export function ChatPage() {
  const [isMockupOpen, setIsMockupOpen] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [mockupSelectedCitation, setMockupSelectedCitation] = useState<Citation | null>(null)
  const [mockupTraceTab, setMockupTraceTab] = useState<TracePanelTab>('observability')
```

- [ ] **Step 3: Replace plain citation titles with clickable rows and wire the modal**

Inside `frontend/src/features/chat/ChatPage.tsx`, add this helper inside `ChatPage()` before `handleSubmit`:

```tsx
  const renderCitationList = (citations: Citation[], onSelect: (citation: Citation) => void) => (
    <section className="message-sources">
      <h4>Referenced documents</h4>
      <ul className="message-sources__list">
        {citations.map((citation) => (
          <li key={citation.sourceId}>
            <button type="button" className="citation-row" onClick={() => onSelect(citation)}>
              {citation.title}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
```

Replace the live assistant citation block:

```tsx
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
```

with:

```tsx
                    {message.trace.citations.length > 0
                      ? renderCitationList(message.trace.citations, setSelectedCitation)
                      : null}
```

Insert the live modal just before the mockup dialog block:

```tsx
      <CitationDetailModal citation={selectedCitation} onClose={() => setSelectedCitation(null)} />
```

- [ ] **Step 4: Make the mockup dialog interactive enough for tab switching and citation inspection**

In `frontend/src/features/chat/ChatPage.tsx`, update the mockup open/close handlers and mockup shell blocks:

```tsx
          onOpenMockup={() => {
            setMockupTraceTab('observability')
            setMockupSelectedCitation(null)
            setIsMockupOpen(true)
          }}
```

```tsx
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
```

Replace the mock assistant citation block:

```tsx
                          <section className="message-sources">
                            <h4>Referenced documents</h4>
                            <ul className="message-sources__list">
                              {message.trace.citations.map((citation) => (
                                <li key={citation.sourceId}>{citation.title}</li>
                              ))}
                            </ul>
                          </section>
```

with:

```tsx
                          {renderCitationList(message.trace.citations, setMockupSelectedCitation)}
```

Update the mockup `TracePanel` props:

```tsx
                <TracePanel
                  trace={mockPreviewTrace}
                  error={null}
                  traceLabel="Response 1"
                  activeTab={mockupTraceTab}
                  onTabChange={setMockupTraceTab}
                  onOpenMockup={() => undefined}
                />
```

Render the mockup citation modal inside the mockup dialog after `</main>` and before `</section>`:

```tsx
            <CitationDetailModal citation={mockupSelectedCitation} onClose={() => setMockupSelectedCitation(null)} />
```

- [ ] **Step 5: Run the targeted chat-page test again**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx --run
```

Expected: FAIL more narrowly because the clickable rows and modal wiring now exist, but styles and mockup interactivity overrides still make some controls inert or visually incorrect.

- [ ] **Step 6: Commit the modal/state implementation**

```bash
git add frontend/src/features/chat/CitationDetailModal.tsx frontend/src/features/chat/ChatPage.tsx
git commit -m "feat: add citation detail modal"
```

---

### Task 3: Restyle the citation block and enable mockup interactions

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Replace chip styling with stacked citation rows**

In `frontend/src/styles.css`, replace:

```css
.message-sources__list {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.message-sources__list li {
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  background: rgba(240, 253, 250, 0.92);
  border: 1px solid rgba(15, 118, 110, 0.16);
  font-size: 12px;
  color: #115e59;
}
```

with:

```css
.message-sources__list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-sources__list li {
  min-width: 0;
}

.citation-row {
  width: 100%;
  display: inline-flex;
  justify-content: flex-start;
  padding: 0;
  border: none;
  background: none;
  color: #0f766e;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  text-decoration: underline;
  text-decoration-color: rgba(15, 118, 110, 0.22);
  text-underline-offset: 3px;
  cursor: pointer;
  transition:
    color 180ms ease,
    text-decoration-color 180ms ease;
}

.citation-row:hover,
.citation-row:focus-visible {
  color: #115e59;
  text-decoration-color: currentColor;
}
```

- [ ] **Step 2: Add citation modal styling**

Insert the following block after `.mockup-dialog__close` in `frontend/src/styles.css`:

```css
.citation-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(255, 247, 237, 0.58);
  backdrop-filter: blur(14px);
}

.citation-modal {
  width: min(640px, 100%);
  border-radius: 24px;
  border: 1px solid rgba(222, 203, 184, 0.72);
  background: linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(255, 255, 255, 0.98));
  box-shadow: 0 28px 70px rgba(234, 88, 12, 0.16);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.citation-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.citation-modal__eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #9a3412;
  margin-bottom: 6px;
}

.citation-modal__header h2 {
  font-size: 24px;
  line-height: 1.15;
}

.citation-modal__close {
  border: 1px solid rgba(222, 203, 184, 0.9);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--text-primary);
  min-height: 44px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.citation-modal__section {
  border: 1px solid rgba(222, 203, 184, 0.72);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  padding: 18px;
}

.citation-modal__section h3 {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9a3412;
  margin-bottom: 10px;
}

.citation-modal__section p,
.citation-modal__meta li {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
}

.citation-modal__meta {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 860px) {
  .citation-modal {
    padding: 20px;
  }

  .citation-modal__header {
    flex-direction: column;
  }

  .citation-modal__close {
    width: 100%;
  }
}
```

- [ ] **Step 3: Re-enable only the mockup controls needed for the design review**

In `frontend/src/styles.css`, replace the mockup interactivity overrides:

```css
.mockup-app-shell .trace-tab {
  pointer-events: none;
}

.mockup-app-shell .sample-strip__button,
.mockup-app-shell .trace-link,
.mockup-app-shell .trace-tab,
.mockup-app-shell .composer button,
.mockup-app-shell .composer textarea {
  cursor: default;
}
```

with:

```css
.mockup-app-shell .sample-strip__button,
.mockup-app-shell .trace-link,
.mockup-app-shell .composer button,
.mockup-app-shell .composer textarea {
  pointer-events: none;
  cursor: default;
}

.mockup-app-shell .trace-tab,
.mockup-app-shell .citation-row,
.mockup-dialog .citation-modal__close {
  pointer-events: auto;
  cursor: pointer;
}
```

Also replace:

```css
.mockup-app-shell .message-sources__list li {
  white-space: nowrap;
}
```

with:

```css
.mockup-app-shell .message-sources__list li {
  white-space: normal;
}
```

- [ ] **Step 4: Run the targeted tests and frontend build**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected: PASS. Citation rows should open details in both live and mockup flows, the mockup tabs should switch, and the frontend build should succeed.

- [ ] **Step 5: Commit the visual polish and mockup interaction changes**

```bash
git add frontend/src/styles.css
git commit -m "feat: refine citation list display"
```

---

### Task 4: Update tracking/docs and run final verification

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`
- Review: `docs/local-dev.md`

- [ ] **Step 1: Add the refinement plan to `TASKS.md`**

Update the plan index in `TASKS.md` to include:

```md
- `docs/superpowers/plans/2026-05-07-citation-list-modal.md` — row-by-row citation list, citation detail modal, and interactive mockup citation review
```

Place it directly after the existing `frontend-observability-transcript` and `frontend-ui-remake` plan entries.

- [ ] **Step 2: Update the transcript-plan refinement note so docs match the UI**

In `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`, replace the current refinement note line with:

```md
**Refinement note:** The current frontend now uses the follow-up light theme variant with a full-viewport three-panel layout, warm orange-to-white gradient background, a bottom-of-panel frontend mockup trigger, row-by-row clickable citation titles that open a citation detail modal, and an interactive mockup dialog that can switch inspection tabs and preview citation details while keeping the same transcript and inspection behavior.
```

- [ ] **Step 3: Review `docs/local-dev.md` and keep it unchanged if commands still match**

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
git add TASKS.md docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md docs/superpowers/plans/2026-05-07-citation-list-modal.md
git commit -m "docs: track citation modal refinement"
```

---

## Spec Coverage Check

- **Row-by-row citation list** → Task 1 locks the interaction with tests, Task 2 renders clickable rows, Task 3 replaces chip styling with vertical list styling.
- **Title-only rows with modal details** → Task 1 adds live and mockup modal tests, Task 2 introduces `CitationDetailModal.tsx`, Task 3 styles the modal and keeps metadata conditional.
- **No per-row detail button** → Task 2 renders citation titles directly as clickable rows, and Task 3 uses underline/pointer treatment instead of extra controls.
- **Interactive frontend mockup** → Task 1 adds tab-switching and mock citation-modal coverage, Task 2 introduces mockup tab/citation state, Task 3 re-enables only the needed mockup controls.
- **Preserve existing backend/data contract** → Task 2 reuses the existing `Citation` model and keeps changes inside the frontend page/component boundary.
- **Docs and tracking updates** → Task 4 updates `TASKS.md`, aligns the transcript plan note, and reviews `docs/local-dev.md`.

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each code-changing step includes the exact code to add or replace.
- Each verification step includes exact Docker Compose commands and expected outcomes.

## Type Consistency Check

Use these names consistently across the implementation:
- `CitationDetailModal` and `CitationDetailModalProps` in `frontend/src/features/chat/CitationDetailModal.tsx`
- `selectedCitation` and `mockupSelectedCitation` in `frontend/src/features/chat/ChatPage.tsx`
- `mockupTraceTab` with type `TracePanelTab` in `frontend/src/features/chat/ChatPage.tsx`
- `Citation` from `frontend/src/types/chat.ts`
- `citation-modal-*` and `citation-row` CSS selectors in `frontend/src/styles.css`

---

Plan complete and saved to `docs/superpowers/plans/2026-05-07-citation-list-modal.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
