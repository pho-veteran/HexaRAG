# Inline Numbered Citations Design

## Goal
Add true inline numbered citations to HexaRAG assistant answers so the transcript can show claims annotated with markers like `[1]` and `[2]`, while keeping citation numbering stable per assistant response, preserving the existing referenced-documents list and citation-detail modal, and extending the backend/frontend contract in a way that can evolve toward markdown or rich-text rendering later.

## Scope
This slice includes:
- backend trace-contract expansion for structured inline citation anchors
- frontend rendering of clickable inline citation markers inside assistant answers
- stable per-answer citation numbering derived from unique sources
- support for repeated same-source references reusing the same number
- support for multi-source cited spans rendering as adjacent markers like `[1][2]`
- synchronization between inline marker clicks, the referenced-documents list, and the citation-detail modal
- targeted backend and frontend tests for the new contract and UI behavior
- required tracking and documentation updates for the repo workflow

This slice does not include:
- streaming response changes
- a full markdown renderer in the current UI
- new retrieval/orchestration behavior in AgentCore
- changes to authentication or session model
- a redesign of the right-side observability panel beyond any minimal compatibility changes

## Product Decisions
The approved behavior for this slice is:
- citation numbering restarts for every assistant response
- each unique source in one response gets exactly one number
- repeated references to the same source reuse that source number
- one cited span may reference multiple sources
- the referenced-documents list stays deduplicated to one row per unique source
- referenced-documents ordering follows first appearance in the answer
- clicking an inline marker should both focus or highlight the matching cited source row and support opening the existing citation-detail modal
- the backend should return structured citation anchors and the frontend should render `[n]` markers from that structure
- the contract should be designed for future markdown or rich-text-safe rendering even if the first UI implementation still renders plain text

## Architecture
### Contract direction
Keep `ChatResponse.message.content` as the answer text and extend `ChatResponse.message.trace` with a new citation-anchor field rather than inserting literal markers into the backend text.

High-level response model:
- `message.content`: clean assistant answer text without literal citation markers injected by the backend
- `message.trace.citations`: deduplicated per-answer source metadata list
- `message.trace.inline_citations`: ordered list of citation anchors pointing into the answer content

Each inline citation anchor should describe:
- where the cited span occurs in the rendered answer
- which one or more sources from `trace.citations` support that span

For the first implementation, anchors may use plain-text character ranges over `message.content`. The field should still be documented as presentation-oriented citation anchors so the same concept can later evolve to markdown or rich-text segment anchors without redesigning the full trace model.

### Number assignment model
The backend should determine the stable order of unique sources by first appearance across the inline citation anchors in a single assistant response. That ordering becomes the order of `trace.citations`.

The frontend should derive displayed numbers from that order:
- first citation source in `trace.citations` renders as `[1]`
- second citation source in `trace.citations` renders as `[2]`
- repeated references to the same `source_id` render the same number again
- multi-source spans render adjacent markers based on the referenced source order, such as `[1][2]`

This keeps numbering deterministic without storing display integers in the API contract.

### Backend responsibilities
The backend should:
1. Produce the final assistant answer text.
2. Collect source support for cited claims within that final answer.
3. Deduplicate sources by stable source identity, normally `source_id`.
4. Order unique sources by first appearance in the answer.
5. Emit `trace.citations` in that stable order.
6. Emit `trace.inline_citations` as ordered anchors referencing one or more `source_id` values.

Backend rules:
- `trace.citations` must only include sources that appear in at least one inline citation anchor.
- repeated same-source references must reuse the same `source_id`.
- one inline anchor may reference multiple `source_id` values.
- malformed, overlapping, or contradictory anchors should be normalized or dropped before returning the response.
- if reliable anchors cannot be produced for a response, the backend should return no inline anchors for that answer rather than emit broken offsets.

### Frontend responsibilities
The frontend should:
- render assistant answers through a citation-aware renderer rather than a raw text node
- convert `message.content` plus `trace.inline_citations` into display segments
- inject clickable inline markers after cited spans
- keep the existing referenced-documents list and detail modal
- derive marker numbers from `trace.citations` ordering
- synchronize marker clicks with the list row and modal state

The recommended frontend boundary is:
- keep `ChatPage.tsx` responsible for page-level layout and citation selection state
- add a focused helper or small component that renders assistant text with inline citations
- keep `CitationDetailModal.tsx` as the detail surface for source metadata and excerpt

This keeps the inline-citation logic isolated so a later markdown-aware renderer can replace the plain-text offset implementation without restructuring the whole page.

## Contract Shape
### Backend API
Keep the existing API boundary names:
- `session_id`
- `ChatResponse.message.trace`

Extend the trace payload with a new field conceptually shaped like:

```json
{
  "citations": [
    {
      "source_id": "doc-ownership",
      "title": "ownership.md",
      "excerpt": "Notifications is owned by Team Mercury.",
      "version": "2026-04-30",
      "recency_note": "Updated 2026-04-30."
    },
    {
      "source_id": "doc-escalation",
      "title": "escalation.md",
      "excerpt": "Mercury handles after-hours escalations.",
      "version": null,
      "recency_note": null
    }
  ],
  "inline_citations": [
    {
      "start": 0,
      "end": 39,
      "source_ids": ["doc-ownership"]
    },
    {
      "start": 68,
      "end": 108,
      "source_ids": ["doc-ownership", "doc-escalation"]
    }
  ]
}
```

Field naming may use the repo's existing snake_case API convention. The important contract behavior is:
- anchors reference `source_id` values, not display numbers
- citation list stays deduplicated
- first appearance determines numbering order

### Frontend types
The frontend should extend its local trace typing to include an inline-citation model carrying:
- span location information for the current plain-text implementation
- referenced source IDs in display order

The API normalization layer should map snake_case backend fields into the existing frontend type style in one centralized place.

## UI Behavior
### Assistant answer rendering
- assistant answers should still read as normal prose
- inline markers should appear immediately after cited spans
- a single-source span renders one marker like `[1]`
- a multi-source span renders adjacent markers like `[1][2]`
- the same source may appear with the same number multiple times in one answer
- answers with no inline anchors should continue to render as plain text

### Referenced-documents list
- the list remains below the assistant reply
- there is one row per unique source
- ordering matches first appearance in the answer
- numbering displayed in the answer and list must stay aligned through `trace.citations` ordering

### Marker click behavior
Clicking an inline marker should:
1. locate the matching source row in the referenced-documents list for that assistant answer
2. move focus to that row or otherwise make it the active cited row
3. apply a visible highlight or selected state to that row
4. open the citation-detail modal for the clicked source

For multi-source cited spans, each rendered marker should be clickable independently so `[1]` and `[2]` remain deterministic and map to separate source rows and modal targets.

### Fallback behavior
- if `trace.citations` exists but `inline_citations` does not, keep the current referenced-documents list behavior
- if an inline anchor references an unknown `source_id`, skip rendering that marker rather than crash
- if an anchor range is malformed on the client, fail safe by rendering plain answer text and the citation list

These fallbacks preserve compatibility with older or partially migrated responses.

## Backend Design Details
### Model and formatter changes
Likely backend files:
- `backend/src/hexarag_api/models/chat.py`
- `backend/src/hexarag_api/services/trace_formatter.py`
- `backend/src/hexarag_api/api/chat.py`
- backend tests for the chat contract and trace formatter

Expected backend changes:
- add a trace model for inline citation anchors
- extend trace formatting to normalize raw inline-citation data into the API model
- ensure stubbed and runtime-backed chat responses can include inline-citation metadata
- keep existing trace fields intact

### Normalization rules
The backend should normalize citation data so:
- duplicate source records collapse to one `trace.citations` entry
- source ordering follows first appearance among anchors
- anchors preserve source ordering for multi-source spans
- anchors with invalid source references or invalid ranges are removed or corrected deterministically

## Frontend Design Details
### Rendering helper
Likely frontend files:
- `frontend/src/types/chat.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/features/chat/ChatPage.tsx`
- a new focused assistant-answer renderer component or helper
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/styles.css`

Recommended renderer behavior:
- sort or trust normalized inline anchors in answer order
- slice `message.content` into uncited and cited text segments
- render cited segments with trailing marker buttons
- map source IDs to display numbers via `trace.citations`

### Interaction state
Page-level state should support:
- selected citation for the modal
- active highlighted citation row per assistant message or a minimal equivalent that allows focus and visual confirmation after clicking an inline marker

The existing citation-detail modal can remain the detail surface, with only minimal changes if it needs to support being opened from inline markers instead of only from list rows.

## Accessibility
- inline markers must be keyboard reachable
- marker styling must not rely on color alone to show clickability or active state
- focused or highlighted cited-source rows must remain visually clear
- modal dialog semantics and close behavior must remain accessible
- answer rendering should preserve readable prose flow even with repeated markers

## Testing Strategy
This work should follow TDD.

### Backend tests
Add or extend targeted tests for:
- repeated same-source references produce one citation entry and one stable number assignment
- multi-source anchors preserve the expected source order
- citation list ordering follows first appearance in the answer
- uncited sources are omitted from `trace.citations`
- malformed anchors are normalized, dropped, or otherwise handled deterministically
- chat API responses include the new field without breaking existing trace fields

### Frontend tests
Add or extend targeted tests for:
- one source cited multiple times reuses the same rendered number
- one span can render multiple markers for multiple sources
- clicking an inline marker highlights or focuses the matching referenced-documents row
- clicking an inline marker opens the correct citation-detail modal
- numbering restarts on the next assistant response
- responses without inline-citation metadata still render correctly

### Verification
Use Docker Compose only.

Expected verification commands for implementation of this slice:
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_trace_formatter.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`

If implementation changes additional frontend or backend behavior outside these boundaries, expand verification to the relevant existing suites.

## Documentation and Tracking
Review and update as needed:
- `TASKS.md`
- `docs/superpowers/plans/2026-05-07-citation-list-modal.md`
- `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md`
- `docs/local-dev.md` only if verification commands change
- `docs/requirements.md` only if implementation forces a real clarification beyond the current requirement that citations surface in the answer and or observability panel

## Constraints
- do not add a host-native workflow
- keep the app as a single-screen chat with an always-visible right observability panel
- keep `session_id` as the API field name
- keep the core response shape rooted at `ChatResponse.message.trace`
- do not collapse answer text and presentation markers into one backend-rendered string
- do not expand this task into full markdown rendering yet
- do not break compatibility with answers that only have the existing citation list

## Open Decisions Resolved
- numbering scope: per assistant answer
- repeated same-source references: reuse the same number
- multi-source cited spans: supported
- referenced-documents list: deduplicated, one row per unique source
- numbering source: frontend derives numbers from backend-provided source ordering
- contract strategy: backend returns structured anchors, frontend renders markers
- future direction: design for markdown or rich text evolution, implement current UI with plain-text anchors first

## Implementation Handoff
After spec review, the next step is to write an implementation plan for this slice and then implement it with TDD across the backend contract, frontend rendering, tests, and required tracking/docs together.