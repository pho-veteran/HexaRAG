# Phase 1 Vertical Slice Design

## Goal
Build the next Phase 1 end-to-end slice by adding a stubbed FastAPI backend contract and wiring the existing frontend shell to it. The slice should validate the app shape from user input through API response and observability rendering without pulling in multi-turn memory, retrieval, or AgentCore orchestration.

## Scope
This slice includes:
- a FastAPI app skeleton with `GET /health` and `POST /chat`
- backend request/response/trace models shaped for the frontend
- a stubbed chat response that echoes the submitted prompt and returns a realistic sample trace payload
- frontend request handling for one synchronous request/response interaction
- a form plus latest-result UI instead of a transcript view
- success and failure rendering in the result area and observability panel
- tests for the backend contract and frontend behavior
- tracking/doc updates required by repository workflow

This slice does not include:
- multi-turn chat history
- session memory behavior beyond keeping the `session_id` field in the contract
- real retrieval, tool execution, structured data, or monitoring integrations
- AgentCore invocation
- authentication

## Product Decisions
The approved behavior for this slice is:
- backend and frontend are delivered together as one vertical slice
- backend success behavior is echo plus sample trace
- the interaction is single request/response only
- the main pane is a form plus latest result panel, not a chat transcript
- on failure the form stays enabled, an inline error is shown, and the latest-result area switches to an error state
- the observability panel shows request and error details after a failed submission instead of remaining empty

## Architecture
### Backend
Add the FastAPI package under `backend/src/hexarag_api/`.

Modules:
- `config.py` for environment-backed settings needed by the app shell
- `models/chat.py` for request, response, trace, and error models
- `api/health.py` for a simple readiness route
- `api/chat.py` for the stubbed chat contract route
- `main.py` for app creation and router registration
- `handler.py` for the Lambda-compatible Mangum entrypoint

`POST /chat` remains the composition boundary for later phases, but for now it returns deterministic stub data. The route accepts a prompt and `session_id`, validates the request, and returns a single assistant message plus `message.trace` in the response shape required by `CLAUDE.md`.

The success payload includes:
- one assistant message derived from the user prompt
- citations
- tool calls
- memory window notes
- grounding notes
- optional uncertainty text when appropriate for the stub

The failure payload should be structured enough for the frontend to surface an inline error and populate the observability panel with request/error details.

### Frontend
Keep the existing two-pane layout. Replace the placeholder chat transcript shell with:
- a prompt form
- a send action
- a latest-result region that shows either the most recent assistant answer, an empty state, or an error state

Add a small API client in `frontend/src/lib/api.ts` and a focused request state helper in `frontend/src/features/chat/useChatSession.ts`. Even though this slice is single-turn, the request shape still sends `session_id` so the Phase 1 contract stays aligned with later work.

`TracePanel` remains always visible. It renders:
- the existing empty guidance before first submission
- trace sections from a successful response
- request/error details from a failed submission

## Contract Shape
### Request
`POST /chat`

```json
{
  "session_id": "phase1-session",
  "message": "<user prompt>"
}
```

### Success response
```json
{
  "session_id": "phase1-session",
  "message": {
    "role": "assistant",
    "content": "<stubbed assistant reply>",
    "trace": {
      "citations": [],
      "tool_calls": [],
      "memory_window": [],
      "grounding_notes": [],
      "uncertainty": null
    }
  }
}
```

Field naming should follow the repo rules from `CLAUDE.md`: keep backend snake_case, keep `session_id`, and keep the core response shape at `ChatResponse.message.trace`. If the frontend prefers camelCase internally, conversion should live in one centralized API boundary rather than scattered component logic.

### Error response
Return a non-2xx response with a body that includes:
- a user-facing error message
- request context useful to the trace pane
- error detail useful to the trace pane

The exact schema can stay minimal as long as the frontend can render both the inline error and the observability error panel from the same response.

## UI Behavior
### Idle
- form is enabled
- latest-result area shows an empty prompt state
- observability panel shows the current empty guidance

### Submitting
- form submit triggers one network request
- duplicate submission prevention can be handled by a temporary loading state on the button
- no chat history is rendered

### Success
- latest-result area shows the returned assistant content
- inline error is cleared
- observability panel shows citations, tool calls, memory, grounding, and uncertainty sections from the response trace

### Failure
- form remains enabled after the failed request completes
- inline error appears near the form
- latest-result area switches to an error state instead of preserving stale success output
- observability panel shows request details and error details for the failed attempt

## Testing Strategy
This work should follow TDD.

### Backend tests first
Create failing tests for:
- `GET /health` returns success
- `POST /chat` returns the expected response contract for a valid request
- invalid or error-triggering requests return the expected failure shape

Then add only enough backend code to satisfy those tests.

### Frontend tests first
Create failing tests for:
- idle shell shows form, latest-result empty state, and observability empty state
- successful submit renders the assistant reply and trace content
- failed submit renders an inline error, switches the latest-result area to an error state, and shows request/error details in the trace pane

Then add only enough frontend code to satisfy those tests.

## File Plan
### Backend
Create:
- `backend/src/hexarag_api/config.py`
- `backend/src/hexarag_api/models/chat.py`
- `backend/src/hexarag_api/api/health.py`
- `backend/src/hexarag_api/api/chat.py`
- `backend/src/hexarag_api/main.py`
- `backend/src/hexarag_api/handler.py`
- `backend/tests/test_health.py`
- `backend/tests/api/test_chat_contract.py`

### Frontend
Create:
- `frontend/src/lib/api.ts`
- `frontend/src/features/chat/useChatSession.ts`

Modify:
- `frontend/src/features/chat/ChatPage.tsx`
- `frontend/src/features/chat/ChatPage.test.tsx`
- `frontend/src/features/trace/TracePanel.tsx`
- `frontend/src/features/trace/TracePanel.test.tsx`
- `frontend/src/types/chat.ts`

### Tracking and docs
Review and update as needed:
- `TASKS.md`
- `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- `docs/local-dev.md`
- `docs/requirements.md`

## Verification
Use the existing Docker Compose workflow only.

Expected verification commands for this slice:
- `docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- broader frontend/backend verification may be rerun if the final implementation touches shared scaffolding

## Constraints
- do not introduce a host-native Node or Python workflow
- do not add multi-turn memory behavior yet
- do not add retrieval or tool integrations beyond stubbed trace content
- keep the response contract aligned with later AgentCore-oriented phases
- keep changes surgical and limited to this vertical slice

## Open Decisions Resolved
- deliver backend and frontend together: yes
- stub behavior: echo plus sample trace
- conversation model: single request/response only
- main pane UI: form plus latest-result panel
- failed-submit UI: inline error plus result error state
- failed-submit observability: show request/error details

## Implementation Handoff
After spec review, the next step is to write an implementation plan for this slice and then execute it with TDD, updating code, tests, and tracking files together.