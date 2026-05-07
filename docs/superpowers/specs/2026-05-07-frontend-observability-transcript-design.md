# Frontend Observability Transcript Design

## Goal
Improve the HexaRAG frontend for demos and explainability by turning the current single latest-result view into a lightweight chat transcript, adding L1-L5 sample questions that fill the composer, showing compact referenced-document lists under assistant replies, and making the right observability panel inspect the trace for whichever assistant reply is selected.

## Scope
This slice includes:
- a transcript-style chat pane with user and assistant messages in chronological order
- a sample-question strip for L1, L2, L3, L4, and L5 demonstrations
- fill-only sample question behavior that updates the composer without auto-sending
- compact referenced-document lists under assistant replies when citations exist
- a per-reply trace selection action that updates the right observability panel
- selected-reply state shared between the chat pane and observability panel
- frontend tests for transcript rendering, trace selection, and sample-question behavior
- tracking and documentation updates required by repository workflow

This slice does not include:
- backend retrieval or trace schema expansion unless the existing contract is proven insufficient
- new orchestration or AgentCore behavior
- streaming response changes
- authentication
- full L5 investigation workflows

## Product Decisions
The approved behavior for this slice is:
- the chat pane becomes a true transcript instead of a single latest-result panel
- sample questions are shown for L1-L5 near the top of the left pane
- clicking a sample question fills the composer but does not send it
- referenced documents appear under each assistant reply as a compact title-only list
- each assistant reply exposes a trace action
- clicking a reply's trace action switches the right panel to that reply's trace, even for older replies
- new assistant replies become selected automatically when they arrive
- the right panel remains always visible and continues to show the same evidence categories

## Architecture
### Frontend state model
The current frontend state centers on one latest assistant message plus one implicitly active trace. That model no longer fits the desired UX because trace inspection must work per response and older answers must remain visible.

Replace it with a turn-oriented state model in `frontend/src/features/chat/useChatSession.ts`:
- one ordered message list containing both user and assistant turns
- assistant turns retain their trace payload in the message object
- one selected assistant message id tracks which trace the right panel shows
- error state remains supported for failed requests and can still drive the observability error rendering

This model keeps the transcript, referenced documents, and selected trace all derived from one coherent source of truth.

### Chat pane
`frontend/src/features/chat/ChatPage.tsx` should render:
- the existing page header
- a sample-question strip above or near the composer
- the transcript area in the main body of the left pane
- the composer anchored below the transcript

Transcript rules:
- render user and assistant messages in chronological order
- assistant messages show answer content plus optional referenced documents and a trace action
- referenced documents render only when `message.trace.citations` is non-empty
- the selected assistant message receives a visible selected state so users can see which trace is active in the right pane

### Observability panel
`frontend/src/features/trace/TracePanel.tsx` should shift from "latest answer" semantics to "selected answer" semantics.

Panel rules:
- if a new assistant reply arrives, its trace becomes selected by default
- if the user clicks the trace action on an older assistant reply, the panel switches to that reply's trace
- the panel header indicates that it is showing the selected reply's trace
- the existing sections remain intact: sources, tool calls, memory, grounding, and uncertainty
- failed submissions continue to use the existing error-details mode when there is no successful selected trace for that failed turn

This preserves the always-visible observability requirement while making the panel useful across multiple turns.

## Contract Shape
The preferred outcome is no backend contract change.

If the existing `ChatResponse.message.trace` payload already includes citations, tool calls, memory window entries, grounding notes, and uncertainty, then the frontend can implement this work without changing the API shape. The frontend may need local type updates only if current TypeScript definitions are too narrow for transcript-specific identifiers.

Two naming constraints remain fixed:
- keep `session_id` at the API boundary
- keep the core trace payload at `ChatResponse.message.trace`

If the frontend needs stable client-side ids for rendered transcript items and the backend does not provide them, the client may synthesize ids locally when normalizing the response as long as that logic is centralized.

## UI Behavior
### Idle
- the sample-question strip is visible
- the composer is empty and enabled
- the transcript is empty or shows a light empty-state prompt
- the observability panel shows its current empty guidance

### Sample-question click
- clicking an L1-L5 sample fills the composer with that prompt
- no request is sent automatically
- the user can edit the prompt before sending

### Submit success
- the user prompt is appended to the transcript
- the assistant reply is appended after the response returns
- the new assistant reply becomes the selected trace by default
- the assistant reply shows a compact referenced-documents block if citations exist
- the right panel updates to the new selected reply's trace

### Trace selection
- clicking the trace action on any assistant reply updates the selected assistant message id
- the clicked reply gets a selected visual treatment
- the right panel switches to that reply's trace without affecting transcript order

### Failure
- failed requests preserve the transcript history that already exists
- the failed user prompt should still appear in the transcript because the request was attempted
- no synthetic assistant error message should be inserted into the transcript unless implementation testing proves the current UI needs one
- the composer becomes enabled again after the request completes
- the inline form error remains visible near the composer
- the right panel can still render request and error details for the failed attempt using the existing failure pattern

## Sample Questions
Provide one curated example per level:
- L1: a single-document retrieval question
- L2: a contradiction or multi-source synthesis question
- L3: a numeric or live-state grounded question
- L4: a follow-up style question that demonstrates session continuity
- L5: a stretch-readiness investigation-style prompt for demo purposes only

These should be presented as clearly labeled demo helpers rather than hard-coded workflows. Their job is to accelerate demonstrations, not replace freeform chat.

The exact wording should be chosen from realistic W4-style prompts already consistent with the repo's evaluation model. Keep them short enough to fit comfortably in the left pane.

To keep the implementation deterministic, the prompts should be stored in one frontend constant list with fixed labels and fixed prompt text rather than being generated dynamically.

Recommended starter prompts:
- L1: "Who owns the Notifications service?"
- L2: "What changed in the on-call escalation policy, and which document is newer?"
- L3: "What is PaymentGW current latency right now?"
- L4: "Why did its costs spike last month?"
- L5: "Investigate whether Checkout is healthy enough for a product launch today."

## Testing Strategy
This work should follow TDD.

Create failing frontend tests first for:
- rendering the sample-question strip with L1-L5 labels
- clicking a sample question fills the composer without sending a request
- submitting multiple turns renders transcript items in chronological order
- assistant replies render a referenced-documents section only when citations exist
- clicking a trace action on an older assistant reply updates the right panel to that reply's trace
- a newly received assistant reply becomes selected automatically
- failure behavior still renders inline error state and observability error details correctly

If implementation reveals a real backend gap, add the narrowest possible contract test before changing backend code.

## File Plan
### Frontend
Modify:
- `frontend/src/features/chat/ChatPage.tsx`
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/features/chat/useChatSession.ts`
- `frontend/src/features/trace/TracePanel.tsx`
- `frontend/src/features/trace/TracePanel.test.tsx`
- `frontend/src/types/chat.ts`
- `frontend/src/styles.css`

Potentially modify only if required by test-driven discovery:
- `frontend/src/lib/api.ts`

### Backend
Modify only if required by a confirmed contract gap:
- backend chat response typing or normalization boundary

### Tracking and docs
Review and update as needed:
- `TASKS.md`
- the active plan or spec reference that still describes the chat UI as a latest-result panel
- `docs/local-dev.md` only if verification commands change
- `docs/requirements.md` only if implementation forces a real requirement clarification

## Verification
Use Docker Compose only.

Expected verification commands for implementation of this slice:
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`
- rerun targeted backend tests only if the backend contract changes

If the final implementation changes shared behavior beyond these files, expand verification to the relevant existing frontend or backend suites.

## Constraints
- do not add a host-native workflow
- keep the app as a single-screen chat with an always-visible right observability panel
- do not turn sample questions into a forced canned flow
- do not duplicate full trace details in the left pane; only compact referenced documents belong under assistant replies
- do not expand this task into full L5 capability delivery
- keep API naming and trace-shape consistency aligned with `CLAUDE.md`

## Open Decisions Resolved
- priority outcomes: referenced documents and clickable trace inspection
- chat layout direction: transcript-based left pane
- sample-question behavior: fill composer only
- referenced-document detail level: compact title-only list
- trace interaction: clicking a reply shows that reply's trace in the right panel

## Implementation Handoff
After spec review, the next step is to write an implementation plan for this slice and then implement it with TDD, updating frontend code, tests, and required tracking/docs together.