# Inline Numbered Citations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured backend inline citation anchors and clickable frontend numbered inline citations like `[1]` and `[2]` while preserving the existing referenced-documents list, citation-detail modal, and always-visible observability panel.

**Architecture:** Extend the backend `ChatResponse.message.trace` contract with normalized `inline_citations` metadata keyed by `source_id`, then render answer text through a focused frontend helper that injects marker buttons from that metadata. Keep numbering derived from `trace.citations` order, keep modal ownership in `ChatPage.tsx`, and fail safe to plain text plus citation list whenever inline metadata is absent or malformed.

**Tech Stack:** FastAPI, Pydantic, Python, React 19, TypeScript, Vite, Vitest, React Testing Library, Docker Compose.

---

## Planned File Structure

### Backend contract and trace shaping
- Modify: `backend/src/hexarag_api/models/chat.py` — add the backend trace model for inline citation anchors.
- Modify: `backend/src/hexarag_api/services/trace_formatter.py` — normalize citations and inline anchors into a stable per-answer ordering.
- Modify: `backend/src/hexarag_api/api/chat.py` — make the stub runtime emit inline citation anchors and keep degraded responses compatible.
- Modify: `backend/tests/services/test_trace_formatter.py` — lock ordering, dedupe, multi-source, and invalid-anchor behavior.
- Modify: `backend/tests/api/test_chat_contract.py` — lock the chat API contract for both success and degraded responses.

### Frontend types, mapping, and renderer
- Modify: `frontend/src/types/chat.ts` — add the frontend inline-citation type to `TracePayload`.
- Modify: `frontend/src/lib/api.ts` — map backend `inline_citations` to camelCase frontend types.
- Create: `frontend/src/features/chat/InlineCitationText.tsx` — render plain text plus inline marker buttons from structured citation anchors.
- Create: `frontend/src/features/chat/InlineCitationText.test.tsx` — lock repeated-source numbering, multi-source spans, and fallback rendering.

### Frontend page integration
- Modify: `frontend/src/features/chat/ChatPage.tsx` — replace raw assistant answer text with the renderer, keep list/modal behavior, and focus/highlight matching citation rows on marker click.
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — lock integration behavior for marker clicks, numbering reset per answer, and fallback answers without inline metadata.
- Modify: `frontend/src/styles.css` — style inline markers and highlighted citation rows.

### Tracking and docs
- Modify: `TASKS.md` — add this implementation plan to the plan index.
- Modify: `docs/superpowers/plans/2026-05-07-citation-list-modal.md` — add a refinement note that inline markers now drive the same row-by-row citation list and modal.
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` — update the refinement note so the transcript description includes inline numbered citations.
- Review: `docs/local-dev.md` — keep unchanged unless verification commands need to change.

---

### Task 1: Add backend inline-citation models and trace normalization

**Files:**
- Modify: `backend/tests/services/test_trace_formatter.py`
- Modify: `backend/src/hexarag_api/models/chat.py`
- Modify: `backend/src/hexarag_api/services/trace_formatter.py`

- [ ] **Step 1: Add failing trace-formatter coverage for dedupe, first-appearance ordering, and invalid-source filtering**

Append these tests to `backend/tests/services/test_trace_formatter.py` after the existing test:

```python
from hexarag_api.services.trace_formatter import build_trace_payload


def test_build_trace_payload_orders_citations_by_first_inline_appearance() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
            {'sourceId': 'doc-escalation', 'title': 'escalation.md', 'excerpt': 'Escalation excerpt'},
        ],
        'inline_citations': [
            {'start': 32, 'end': 61, 'source_ids': ['doc-escalation']},
            {'start': 0, 'end': 31, 'source_ids': ['doc-ownership']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership', 'doc-escalation']
    assert trace.inline_citations[0].source_ids == ['doc-ownership']
    assert trace.inline_citations[1].source_ids == ['doc-escalation']


def test_build_trace_payload_reuses_sources_and_keeps_multi_source_order() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
            {'sourceId': 'doc-escalation', 'title': 'escalation.md', 'excerpt': 'Escalation excerpt'},
        ],
        'inline_citations': [
            {'start': 0, 'end': 24, 'source_ids': ['doc-ownership']},
            {'start': 25, 'end': 56, 'source_ids': ['doc-ownership', 'doc-escalation']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership', 'doc-escalation']
    assert trace.inline_citations[1].source_ids == ['doc-ownership', 'doc-escalation']


def test_build_trace_payload_drops_inline_anchors_for_unknown_sources() -> None:
    raw = {
        'citations': [
            {'sourceId': 'doc-ownership', 'title': 'ownership.md', 'excerpt': 'Ownership excerpt'},
        ],
        'inline_citations': [
            {'start': 0, 'end': 24, 'source_ids': ['doc-unknown']},
            {'start': 25, 'end': 56, 'source_ids': ['doc-ownership']},
        ],
    }

    trace = build_trace_payload(raw, memory_window=[])

    assert [citation.source_id for citation in trace.citations] == ['doc-ownership']
    assert len(trace.inline_citations) == 1
    assert trace.inline_citations[0].source_ids == ['doc-ownership']
```

- [ ] **Step 2: Run the targeted backend formatter tests and verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py -q
```

Expected: FAIL because `TracePayload` does not expose `inline_citations` yet and `build_trace_payload()` does not normalize or reorder inline citation anchors.

- [ ] **Step 3: Add the backend inline-citation model to `chat.py`**

In `backend/src/hexarag_api/models/chat.py`, insert the new model after `Citation` and extend `TracePayload`:

```python
class InlineCitationAnchor(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    source_ids: list[str] = Field(default_factory=list)


class TracePayload(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    inline_citations: list[InlineCitationAnchor] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    memory_window: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)
    uncertainty: str | None = None
    conflict_resolution: ConflictResolution | None = None
```

- [ ] **Step 4: Implement inline-citation normalization in `trace_formatter.py`**

Replace `backend/src/hexarag_api/services/trace_formatter.py` with:

```python
from hexarag_api.models.chat import Citation, InlineCitationAnchor, TracePayload


def _build_citation_lookup(raw: dict) -> dict[str, Citation]:
    citations: dict[str, Citation] = {}

    for item in raw.get('citations', []):
        source_id = item.get('source_id') or item.get('sourceId', '')
        if not source_id:
            continue

        citations[source_id] = Citation(
            source_id=source_id,
            title=item['title'],
            excerpt=item['excerpt'],
            version=item.get('version'),
            recency_note=item.get('recency_note') or item.get('recencyNote'),
        )

    return citations


def _normalize_inline_citations(raw: dict, citation_lookup: dict[str, Citation]) -> tuple[list[Citation], list[InlineCitationAnchor]]:
    normalized_anchors: list[InlineCitationAnchor] = []
    ordered_source_ids: list[str] = []

    raw_anchors = sorted(raw.get('inline_citations', []), key=lambda item: (item.get('start', 0), item.get('end', 0)))

    for item in raw_anchors:
        start = item.get('start')
        end = item.get('end')
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
            continue

        source_ids = [source_id for source_id in item.get('source_ids', []) if source_id in citation_lookup]
        if not source_ids:
            continue

        deduped_source_ids: list[str] = []
        for source_id in source_ids:
            if source_id not in deduped_source_ids:
                deduped_source_ids.append(source_id)
            if source_id not in ordered_source_ids:
                ordered_source_ids.append(source_id)

        normalized_anchors.append(
            InlineCitationAnchor(
                start=start,
                end=end,
                source_ids=deduped_source_ids,
            )
        )

    ordered_citations = [citation_lookup[source_id] for source_id in ordered_source_ids]
    return ordered_citations, normalized_anchors


def build_trace_payload(raw: dict, memory_window: list[str]) -> TracePayload:
    citation_lookup = _build_citation_lookup(raw)
    citations, inline_citations = _normalize_inline_citations(raw, citation_lookup)

    return TracePayload(
        citations=citations,
        inline_citations=inline_citations,
        tool_calls=raw.get('tool_calls', []),
        memory_window=memory_window,
        grounding_notes=raw.get('grounding_notes', []),
        uncertainty=raw.get('uncertainty'),
        conflict_resolution=raw.get('conflict_resolution'),
    )
```

- [ ] **Step 5: Run the targeted backend formatter tests and verify they pass**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit the backend trace-model work**

```bash
git add backend/src/hexarag_api/models/chat.py backend/src/hexarag_api/services/trace_formatter.py backend/tests/services/test_trace_formatter.py
git commit -m "feat: add inline citation trace metadata"
```

---

### Task 2: Extend the stub chat contract to emit inline citation anchors

**Files:**
- Modify: `backend/tests/api/test_chat_contract.py`
- Modify: `backend/src/hexarag_api/api/chat.py`

- [ ] **Step 1: Add failing API-contract assertions for success and degraded responses**

In `backend/tests/api/test_chat_contract.py`, update the existing success test and degraded test to include:

```python
def test_chat_returns_stubbed_message_and_trace() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 'phase1-session',
            'message': 'What is PaymentGW latency?',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['session_id'] == 'phase1-session'
    assert payload['message']['role'] == 'assistant'
    assert 'trace' in payload['message']
    assert payload['message']['trace']['citations'][0]['source_id'] == 'doc-architecture'
    assert payload['message']['trace']['inline_citations'] == [
        {
            'start': 0,
            'end': len(payload['message']['content']),
            'source_ids': ['doc-architecture'],
        }
    ]


def test_chat_returns_grounded_failure_when_runtime_errors() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 's-1',
            'message': 'What is NotificationSvc status?',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 'could not complete the live tool step' in payload['message']['content'].lower()
    assert payload['message']['trace']['citations'] == []
    assert payload['message']['trace']['inline_citations'] == []
```

- [ ] **Step 2: Run the targeted chat-contract tests and verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py -q
```

Expected: FAIL because the stub runtime does not emit `inline_citations` and the degraded trace does not guarantee an empty `inline_citations` list.

- [ ] **Step 3: Emit inline citation anchors from the stub runtime in `chat.py`**

In `backend/src/hexarag_api/api/chat.py`, replace the success branch in `StubAgentRuntime.answer()` with:

```python
class StubAgentRuntime:
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        if message in {FAILURE_TRIGGER_MESSAGE, 'What is NotificationSvc status?'}:
            raise RuntimeError('live tool unavailable')

        answer = f'Stub answer for: {message}'

        return {
            'answer': answer,
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-architecture',
                        'title': 'architecture.md',
                        'excerpt': 'Current p95 latency sits below the alert threshold.',
                        'recency_note': 'Stubbed knowledge base note.',
                    }
                ],
                'inline_citations': [
                    {
                        'start': 0,
                        'end': len(answer),
                        'source_ids': ['doc-architecture'],
                    }
                ],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'success',
                        'summary': 'Prepared stub observability data',
                        'input': {'question': message},
                        'output': {'mode': 'stub', 'latency_p95_ms': 185},
                    }
                ],
                'grounding_notes': ['This is a deterministic stub response for the Phase 2 runtime slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        }
```

Also update the degraded `build_trace_payload()` input in the exception branch so it passes an empty inline-citation list explicitly:

```python
        trace = build_trace_payload(
            {
                'citations': [],
                'inline_citations': [],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'error',
                        'summary': 'Live monitoring call failed.',
                        'input': {'question': request.message},
                        'output': None,
                    }
                ],
                'grounding_notes': ['Returned fallback answer because the live tool step failed.'],
                'uncertainty': 'Live monitoring data is temporarily unavailable.',
            },
            memory_window,
        )
```

- [ ] **Step 4: Run the targeted backend contract tests and verify they pass**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the chat-contract changes**

```bash
git add backend/src/hexarag_api/api/chat.py backend/tests/api/test_chat_contract.py
git commit -m "feat: return inline citations from chat api"
```

---

### Task 3: Add frontend inline-citation types, mapping, and renderer

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/features/chat/InlineCitationText.tsx`
- Create: `frontend/src/features/chat/InlineCitationText.test.tsx`

- [ ] **Step 1: Add failing renderer tests for repeated numbering, multi-source spans, and fallback rendering**

Create `frontend/src/features/chat/InlineCitationText.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { Citation, InlineCitationAnchor } from '../../types/chat'
import { InlineCitationText } from './InlineCitationText'

const citations: Citation[] = [
  {
    sourceId: 'doc-ownership',
    title: 'ownership.md',
    excerpt: 'Notifications is owned by Team Mercury.',
  },
  {
    sourceId: 'doc-escalation',
    title: 'escalation.md',
    excerpt: 'Mercury handles after-hours escalations.',
  },
]

function buildAnchors(content: string): InlineCitationAnchor[] {
  const firstClaim = 'Team Mercury owns Notifications.'
  const secondClaim = 'Mercury also handles escalations.'
  const firstStart = content.indexOf(firstClaim)
  const secondStart = content.indexOf(secondClaim)

  return [
    {
      start: firstStart,
      end: firstStart + firstClaim.length,
      sourceIds: ['doc-ownership'],
    },
    {
      start: secondStart,
      end: secondStart + secondClaim.length,
      sourceIds: ['doc-ownership', 'doc-escalation'],
    },
  ]
}

describe('InlineCitationText', () => {
  it('reuses the same number for repeated source references and renders multi-source markers', () => {
    const content = 'Team Mercury owns Notifications. Mercury also handles escalations.'

    render(
      <InlineCitationText
        content={content}
        citations={citations}
        inlineCitations={buildAnchors(content)}
        onCitationClick={() => undefined}
      />,
    )

    expect(screen.getAllByRole('button', { name: '[1]' })).toHaveLength(2)
    expect(screen.getAllByRole('button', { name: '[2]' })).toHaveLength(1)
  })

  it('calls back with the clicked source id', async () => {
    const content = 'Team Mercury owns Notifications. Mercury also handles escalations.'
    const handleCitationClick = vi.fn()
    const user = userEvent.setup()

    render(
      <InlineCitationText
        content={content}
        citations={citations}
        inlineCitations={buildAnchors(content)}
        onCitationClick={handleCitationClick}
      />,
    )

    await user.click(screen.getAllByRole('button', { name: '[1]' })[1])
    await user.click(screen.getByRole('button', { name: '[2]' }))

    expect(handleCitationClick).toHaveBeenNthCalledWith(1, 'doc-ownership')
    expect(handleCitationClick).toHaveBeenNthCalledWith(2, 'doc-escalation')
  })

  it('falls back to plain text when inline citations are absent', () => {
    render(
      <InlineCitationText
        content="Team Mercury owns Notifications."
        citations={citations}
        inlineCitations={[]}
        onCitationClick={() => undefined}
      />,
    )

    expect(screen.getByText('Team Mercury owns Notifications.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '[1]' })).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the renderer test and verify it fails**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/InlineCitationText.test.tsx --run
```

Expected: FAIL because the inline-citation type and component do not exist yet.

- [ ] **Step 3: Extend frontend trace types with inline citation anchors**

In `frontend/src/types/chat.ts`, insert the new type and extend `TracePayload`:

```ts
export interface InlineCitationAnchor {
  start: number
  end: number
  sourceIds: string[]
}

export interface TracePayload {
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
}
```

- [ ] **Step 4: Map backend `inline_citations` in `api.ts`**

In `frontend/src/lib/api.ts`, add the API type and update `mapTrace()`:

```ts
interface ApiInlineCitationAnchor {
  start: number
  end: number
  source_ids: string[]
}

interface ApiTracePayload {
  citations: ApiCitation[]
  inline_citations?: ApiInlineCitationAnchor[]
  tool_calls: ApiToolCallTrace[]
  memory_window: string[]
  grounding_notes: string[]
  uncertainty: string | null
}

function mapTrace(trace: ApiTracePayload): TracePayload {
  return {
    citations: trace.citations.map((citation) => ({
      sourceId: citation.source_id,
      title: citation.title,
      excerpt: citation.excerpt,
      version: citation.version ?? undefined,
      recencyNote: citation.recency_note ?? undefined,
    })),
    inlineCitations: (trace.inline_citations ?? []).map((anchor) => ({
      start: anchor.start,
      end: anchor.end,
      sourceIds: anchor.source_ids,
    })),
    toolCalls: trace.tool_calls,
    memoryWindow: trace.memory_window,
    groundingNotes: trace.grounding_notes,
    uncertainty: trace.uncertainty,
  }
}
```

- [ ] **Step 5: Create the citation-aware answer renderer**

Create `frontend/src/features/chat/InlineCitationText.tsx` with:

```tsx
import type { Citation, InlineCitationAnchor } from '../../types/chat'

interface InlineCitationTextProps {
  content: string
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  onCitationClick: (sourceId: string) => void
}

function isRenderableAnchor(anchor: InlineCitationAnchor, contentLength: number): boolean {
  return anchor.start >= 0 && anchor.end > anchor.start && anchor.end <= contentLength
}

export function InlineCitationText({ content, citations, inlineCitations, onCitationClick }: InlineCitationTextProps) {
  if (inlineCitations.length === 0) {
    return <p>{content}</p>
  }

  const citationNumbers = new Map(citations.map((citation, index) => [citation.sourceId, index + 1]))
  const anchors = [...inlineCitations].sort((left, right) => left.start - right.start)

  if (anchors.some((anchor) => !isRenderableAnchor(anchor, content.length))) {
    return <p>{content}</p>
  }

  const parts: JSX.Element[] = []
  let cursor = 0

  anchors.forEach((anchor, anchorIndex) => {
    if (cursor < anchor.start) {
      parts.push(<span key={`text-${anchorIndex}-${cursor}`}>{content.slice(cursor, anchor.start)}</span>)
    }

    parts.push(
      <span key={`anchor-${anchorIndex}`}>
        {content.slice(anchor.start, anchor.end)}
        {anchor.sourceIds.map((sourceId) => {
          const number = citationNumbers.get(sourceId)
          if (!number) {
            return null
          }

          return (
            <button
              key={`${anchor.start}-${sourceId}`}
              type="button"
              className="citation-inline-marker"
              onClick={() => onCitationClick(sourceId)}
            >
              [{number}]
            </button>
          )
        })}
      </span>,
    )

    cursor = anchor.end
  })

  if (cursor < content.length) {
    parts.push(<span key={`tail-${cursor}`}>{content.slice(cursor)}</span>)
  }

  return <p className="assistant-answer">{parts}</p>
}
```

- [ ] **Step 6: Run the renderer test and verify it passes**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/InlineCitationText.test.tsx --run
```

Expected: PASS.

- [ ] **Step 7: Commit the frontend renderer layer**

```bash
git add frontend/src/types/chat.ts frontend/src/lib/api.ts frontend/src/features/chat/InlineCitationText.tsx frontend/src/features/chat/InlineCitationText.test.tsx
git commit -m "feat: render inline citation markers"
```

---

### Task 4: Integrate inline citations into the chat page, list focus, and modal flow

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add failing chat-page integration tests for marker clicks, numbering reset, and plain-text fallback**

In `frontend/src/features/chat/ChatPage.test.tsx`, add these tests after the existing live citation-modal test:

```tsx
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
```

- [ ] **Step 2: Run the targeted chat-page tests and verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx --run
```

Expected: FAIL because `ChatPage.tsx` still renders assistant answers as plain `<p>{message.content}</p>` and does not track active citation rows or marker clicks.

- [ ] **Step 3: Integrate the renderer and row-focus logic into `ChatPage.tsx`**

In `frontend/src/features/chat/ChatPage.tsx`, add the renderer import and page-level citation-target state:

```tsx
import { useRef, useState, type FormEvent } from 'react'

import type { AssistantChatMessage, Citation, TracePanelTab, TracePayload } from '../../types/chat'
import { TracePanel } from '../trace/TracePanel'
import { CitationDetailModal } from './CitationDetailModal'
import { InlineCitationText } from './InlineCitationText'
import { sampleQuestions } from './sampleQuestions'
import { useChatSession } from './useChatSession'
```

```tsx
  const [activeCitationTarget, setActiveCitationTarget] = useState<{ messageId: string; sourceId: string } | null>(null)
  const [mockupActiveCitationTarget, setMockupActiveCitationTarget] = useState<{ messageId: string; sourceId: string } | null>(null)
  const citationRowRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  const citationRowKey = (messageId: string, sourceId: string) => `${messageId}:${sourceId}`

  const openCitation = (
    messageId: string,
    sourceId: string,
    citations: Citation[],
    setSelected: (citation: Citation | null) => void,
    setActiveTarget: (target: { messageId: string; sourceId: string } | null) => void,
  ) => {
    const citation = citations.find((item) => item.sourceId === sourceId)
    if (!citation) {
      return
    }

    setActiveTarget({ messageId, sourceId })
    setSelected(citation)

    queueMicrotask(() => {
      citationRowRefs.current[citationRowKey(messageId, sourceId)]?.focus()
    })
  }
```

Replace `renderCitationList` with a version that knows the message id and active row:

```tsx
  const renderCitationList = (
    messageId: string,
    citations: Citation[],
    activeSourceId: string | null,
    onSelect: (sourceId: string) => void,
  ) => (
    <section className="message-sources">
      <h4>Referenced documents</h4>
      <ul className="message-sources__list">
        {citations.map((citation) => (
          <li key={citation.sourceId}>
            <button
              type="button"
              ref={(node) => {
                citationRowRefs.current[citationRowKey(messageId, citation.sourceId)] = node
              }}
              className={`citation-row${activeSourceId === citation.sourceId ? ' citation-row--active' : ''}`}
              onClick={() => onSelect(citation.sourceId)}
            >
              {citation.title}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
```

Replace the live assistant answer block inside the transcript loop:

```tsx
                    <InlineCitationText
                      content={message.content}
                      citations={message.trace.citations}
                      inlineCitations={message.trace.inlineCitations}
                      onCitationClick={(sourceId) =>
                        openCitation(
                          message.id,
                          sourceId,
                          message.trace.citations,
                          setSelectedCitation,
                          setActiveCitationTarget,
                        )
                      }
                    />

                    {message.trace.citations.length > 0
                      ? renderCitationList(
                          message.id,
                          message.trace.citations,
                          activeCitationTarget?.messageId === message.id ? activeCitationTarget.sourceId : null,
                          (sourceId) =>
                            openCitation(
                              message.id,
                              sourceId,
                              message.trace.citations,
                              setSelectedCitation,
                              setActiveCitationTarget,
                            ),
                        )
                      : null}
```

Update the mock preview trace at the top of the file so the mockup uses inline markers too:

```tsx
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
      end: 'Team Mercury owns the Notifications service.'.length,
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
}
```

Replace the mock assistant content and citation list block with the renderer plus active-row handling:

```tsx
                          <InlineCitationText
                            content={message.content}
                            citations={message.trace.citations}
                            inlineCitations={message.trace.inlineCitations}
                            onCitationClick={(sourceId) =>
                              openCitation(
                                message.id,
                                sourceId,
                                message.trace.citations,
                                setMockupSelectedCitation,
                                setMockupActiveCitationTarget,
                              )
                            }
                          />

                          {renderCitationList(
                            message.id,
                            message.trace.citations,
                            mockupActiveCitationTarget?.messageId === message.id
                              ? mockupActiveCitationTarget.sourceId
                              : null,
                            (sourceId) =>
                              openCitation(
                                message.id,
                                sourceId,
                                message.trace.citations,
                                setMockupSelectedCitation,
                                setMockupActiveCitationTarget,
                              ),
                          )}
```

- [ ] **Step 4: Add inline marker and active-row styling in `styles.css`**

In `frontend/src/styles.css`, add the following block after `.message-card--assistant`:

```css
.assistant-answer {
  display: inline;
}

.citation-inline-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
  padding: 0;
  border: none;
  background: none;
  color: #9a3412;
  font-size: 0.92em;
  font-weight: 700;
  line-height: inherit;
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: rgba(154, 52, 18, 0.3);
  text-underline-offset: 2px;
}

.citation-inline-marker:hover,
.citation-inline-marker:focus-visible {
  color: #c2410c;
  text-decoration-color: currentColor;
}
```

Add the active citation-row styling after the existing `.citation-row:hover, .citation-row:focus-visible` rule:

```css
.citation-row--active {
  color: #115e59;
  text-decoration-color: currentColor;
  font-weight: 700;
}
```

- [ ] **Step 5: Run targeted frontend tests and the frontend build**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/InlineCitationText.test.tsx src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit the chat-page integration work**

```bash
git add frontend/src/features/chat/InlineCitationText.tsx frontend/src/features/chat/InlineCitationText.test.tsx frontend/src/features/chat/ChatPage.tsx frontend/src/features/chat/ChatPage.test.tsx frontend/src/styles.css frontend/src/types/chat.ts frontend/src/lib/api.ts
git commit -m "feat: wire inline citations into chat ui"
```

---

### Task 5: Update tracking/docs and run final verification

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-07-citation-list-modal.md`
- Modify: `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`
- Review: `docs/local-dev.md`

- [ ] **Step 1: Add this plan to the `TASKS.md` plan index**

In `TASKS.md`, add this line under the existing 2026-05-07 plan entries:

```md
- `docs/superpowers/plans/2026-05-07-inline-numbered-citations.md` — backend inline citation anchors plus frontend numbered inline citation rendering
```

- [ ] **Step 2: Update the citation-list-modal plan note so it reflects inline markers too**

Near the top of `docs/superpowers/plans/2026-05-07-citation-list-modal.md`, add this refinement note directly under the goal section:

```md
**Refinement note:** The current citation experience now includes inline numbered markers inside assistant answers. Those markers map to the same deduplicated referenced-documents list, reuse the same per-answer source number for repeated references, and open the existing citation detail modal through the same page-level citation-selection flow.
```

- [ ] **Step 3: Update the transcript-plan refinement note to mention inline markers**

In `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`, replace the current refinement note line with:

```md
**Refinement note:** The current frontend now uses the follow-up light theme variant with a full-viewport three-panel layout, warm orange-to-white gradient background, a bottom-of-panel frontend mockup trigger, inline numbered citation markers inside assistant answers, row-by-row clickable citation titles that open a citation detail modal, and an interactive mockup dialog that can switch inspection tabs and preview citation details while keeping the same transcript and inspection behavior.
```

- [ ] **Step 4: Review `docs/local-dev.md` and keep it unchanged if the commands already cover the work**

Review the backend and frontend verification sections in `docs/local-dev.md`.

Expected outcome: no edit needed, because the existing Docker Compose commands already cover `tests/api/test_chat_contract.py`, `tests/services/test_trace_formatter.py`, `src/features/chat/ChatPage.test.tsx`, `src/features/trace/TracePanel.test.tsx`, and `npm run build`.

- [ ] **Step 5: Run final verification for backend and frontend**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_trace_formatter.py -q && docker compose run --rm frontend npm run test -- src/features/chat/InlineCitationText.test.tsx src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit the docs and tracking updates**

```bash
git add TASKS.md docs/superpowers/plans/2026-05-07-inline-numbered-citations.md docs/superpowers/plans/2026-05-07-citation-list-modal.md docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md
git commit -m "docs: track inline citation implementation"
```

---

## Spec Coverage Check

- **Structured backend anchors** → Task 1 adds `InlineCitationAnchor` and trace normalization, Task 2 emits anchors from the chat API.
- **Per-answer numbering and reused source numbers** → Task 1 normalizes source ordering by first appearance, Task 3 derives numbers from `trace.citations`, Task 4 verifies numbering reset in the chat UI.
- **Multi-source cited spans** → Task 1 preserves ordered multi-source anchors, Task 3 renders adjacent markers, Task 4 verifies marker clicks in the page integration.
- **Referenced-documents list stays deduplicated** → Task 1 filters `trace.citations` to anchored sources only, Task 4 keeps the existing list and active-row focus flow.
- **Marker click focuses/highlights the row and opens the modal** → Task 4 adds the page-level `openCitation()` flow and locks it with integration tests.
- **Fallback to plain text when inline metadata is absent or malformed** → Task 3 falls back in `InlineCitationText`, Task 4 adds the page-level fallback test.
- **Docs and tracking updates** → Task 5 updates the plan index and both active frontend plan notes while reviewing `docs/local-dev.md`.

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Every code-changing step includes the code to add or replace.
- Every verification step includes an exact Docker Compose command and expected result.

## Type Consistency Check

Use these names consistently across the implementation:
- `InlineCitationAnchor` in `backend/src/hexarag_api/models/chat.py`
- `inline_citations` at the backend API boundary
- `InlineCitationAnchor` in `frontend/src/types/chat.ts`
- `inlineCitations` in `frontend/src/lib/api.ts` and the renderer props
- `InlineCitationText` in `frontend/src/features/chat/InlineCitationText.tsx`
- `citation-inline-marker` and `citation-row--active` in `frontend/src/styles.css`
- `openCitation()` in `frontend/src/features/chat/ChatPage.tsx`

---

Plan complete and saved to `docs/superpowers/plans/2026-05-07-inline-numbered-citations.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?