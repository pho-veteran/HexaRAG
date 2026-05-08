# HexaRAG App Functionality Tracker

This document tracks the expected product behavior across the frontend, backend, data/tool integrations, trace contract, and deployment-dependent runtime behavior.

For the AWS deployment runbook and operator steps, see `docs/aws.md`.

## Status vocabulary
- `working` — the expected capability is present and wired through the current app flow.
- `partial` — some of the capability works, but key behavior or coverage is incomplete.
- `mocked` — the UI or docs show the capability using non-production data or a static preview path.
- `unwired` — pieces exist, but the full end-to-end product behavior is not connected.
- `missing` — the capability is expected but not currently implemented.

## Current product shape
HexaRAG exposes a single-screen chat product with:
- quick demo questions on the left
- a chat conversation in the center
- an always-visible inspection console on the right

The backend responds through `POST /chat` and returns a UI-facing trace contract shaped as `ChatResponse.message.trace`.

## Current explainability contract
The checked-in trace contract now includes:
- citations
- inline citation anchors
- tool calls
- `memoryWindow`
- grounding notes
- uncertainty
- conflict resolution metadata
- explicit runtime metadata
- safe reasoning summaries for the Thinking tab

The backend owns this contract and normalizes Bedrock output before the frontend renders it.

## Runtime/model visibility
The product now exposes explicit runtime metadata per answer.

Backend trace payloads include:
- `runtime.mode`
- `runtime.provider`
- `runtime.region`
- `runtime.agent_id`
- `runtime.agent_alias_id`
- `runtime.model` when Bedrock trace data exposes the invoked foundation model

This makes the producing runtime visible without changing the overall `/chat` response shape.

## Thinking process behavior
The Thinking tab no longer duplicates the Observability inventory with generic source-checking language.

Instead, it explains how the answer was formed through curated steps such as:
- Generated response
- Synthesized evidence
- Selected answer-shaping sources
- Applied tool results
- Reused recent context
- Resolved conflicting evidence
- Included caveats

This is safe, user-visible reasoning metadata rather than hidden chain-of-thought.

## Session memory behavior
Session memory is now temporary per page load.

Implemented behavior:
- the frontend generates a new `session_id` on page load
- that `session_id` stays stable for multiple sends within the same page instance
- refreshing the page or opening a new tab creates a different `session_id`
- the frontend does not persist the session ID in localStorage, cookies, or the URL

That means the intended memory model is temporary browser-window continuity rather than durable client memory.

## Bedrock runtime instruction ownership
The repo now owns a reusable instruction contract in `backend/src/hexarag_api/services/agent_runtime.py`.

The runtime input explicitly guides Bedrock Agents to:
- use recent conversation context only when it helps answer the latest question
- answer from grounded evidence instead of guesswork
- prefer the newest valid source when sources disagree
- keep answers concise
- surface uncertainty when evidence is incomplete or a live step fails

This behavior is no longer implicit only in Bedrock-side configuration.

| Area | Functionality | Expected behavior | Current state | Current implementation notes | Known gap or blocker |
| --- | --- | --- | --- | --- | --- |
| Chat | Freeform chat submit | Users can send arbitrary questions to the backend. | working | The composer posts `session_id` and `message` to `POST /chat`. | Real answer quality still depends on runtime wiring and data sources. |
| Chat | Conversation history rendering | User and assistant turns render in one readable thread. | working | Messages append locally and assistant turns carry trace data for inspection. | No streamed rendering yet. |
| Chat | Per-response inspection | Users can inspect a specific assistant reply in the console. | working | The selected assistant message ID drives the visible trace. | Value depends on the completeness of the backend trace. |
| Chat | Temporary per-page session continuity | Follow-up questions within one page instance reuse one active session window. | working | `useChatSession.ts` generates a new session ID per mount and reuses it within that instance. | Refresh/new-tab continuity is intentionally not preserved. |
| Chat | Error-state rendering | Failed requests show explicit request and detail information. | working | The inspection console renders the backend error payload. | Degraded backend paths must keep honoring the error contract. |
| Inspection console | Observability tab | Users can inspect sources, tools, memory, grounding, uncertainty, and conflict resolution. | working | `TracePanel.tsx` renders the stable observability sections when the trace provides them. | Completeness still depends on backend trace population. |
| Inspection console | Thinking tab | Users can inspect a synthesis-oriented explanation of how the answer was formed. | working | `buildTraceNarrative.ts` builds curated reasoning steps from structured trace fields. | Narrative quality depends on the runtime populating reasoning metadata well. |
| Inspection console | Runtime/model visibility | Users can see what runtime produced an answer. | working | Runtime metadata is normalized by the backend and available in the UI contract. | `runtime.model` still depends on what Bedrock trace metadata exposes. |
| Citations | Inline citations | Assistant answers show clickable inline citation anchors. | partial | The frontend supports inline citation rendering and interaction. | The backend must consistently return inline citation anchors for grounded answers. |
| Citations | Referenced document list | Each grounded answer lists the cited source documents. | working | The UI renders one clickable row per citation when present. | Completeness depends on trace normalization. |
| Citations | Citation detail modal | Users can inspect excerpt and source metadata in a focused modal. | working | Clicking a citation row or inline citation opens the modal. | Quality depends on excerpt and metadata completeness. |
| Grounding | Conflict resolution visibility | When sources disagree, the chosen source and rationale are surfaced. | working | The trace supports `conflict_resolution`, and the observability panel renders it. | Live runtime consistency still needs ongoing verification. |
| Grounding | Uncertainty visibility | Partial evidence or degraded paths should surface caveats instead of false certainty. | partial | The contract supports `uncertainty` and reasoning caveat summaries. | The live runtime must populate these consistently in every degraded path. |
| Tooling | Live monitoring answers | Users can ask for current service metrics grounded in monitoring data. | partial | The monitoring API exposes `/services` and `/metrics/{service_name}` and the deployed app has verified tool-backed answers. | The live monitoring surface is still narrower than the full W4 package. |
| Tooling | Historical structured answers | Users can ask for exact historical numeric values grounded in structured data. | partial | The repo currently loads monthly costs. | Incident, SLA, and daily metrics structured coverage is still incomplete. |
| Tooling | Mixed-source synthesis | One answer can combine retrieval, structured data, and live tool output. | unwired | The trace contract is ready for this composition. | End-to-end mixed-source coverage is not yet fully proven across all W4 cases. |
| Memory | Memory context visibility | Users can see which recent turns influenced the current answer. | working | The trace includes `memoryWindow`, and the observability tab renders it. | Value depends on meaningful backend session-memory shaping. |
| Memory | Follow-up reference resolution | Users can ask pronoun-based follow-ups within one active page session. | partial | The frontend and backend session contract support this shape. | Live quality still depends on Bedrock and session-store behavior. |
| Deployment | Frontend API URL correctness | The deployed frontend must call the deployed backend over HTTPS. | working | The production build now requires an explicit `VITE_API_BASE_URL` and no longer relies on the Docker-local default path. | Future deploys must keep that explicit build step. |
| Deployment | Browser CORS compatibility | Browser requests from the CloudFront frontend must succeed. | working | The backend allowlist and API Gateway HTTP API CORS config were both wired for the deployed CloudFront origin. | Any new frontend domain must be added in both places. |
| Deployment | KB upload and ingestion ordering | Retrieval should only be trusted after upload and completed ingestion. | partial | The repo includes upload and sync scripts, and deployment tracking records a completed ingestion run. | Operators must still execute the sequence correctly. |
| Deployment | AWS output discoverability | Operators can retrieve the deployed endpoints and bucket names without guesswork. | working | Terraform outputs expose the backend, monitoring, CloudFront, bucket, session-table, and database endpoints. | Bedrock resource IDs remain external inputs, not Terraform-managed resources. |

## Verified current behavior
- The backend and frontend now agree on the expanded runtime/reasoning trace contract.
- The Thinking tab has focused tests for richer synthesis steps.
- The chat session hook has focused tests that prove one page instance reuses one session ID while a remount creates a new one.
- The deployed browser flow has already been verified to reach the HTTPS backend successfully after the API base URL and CORS fixes.

## Known current gaps
- The structured-data loader still only covers monthly costs.
- The monitoring surface is narrower than the full W4 live-data expectation.
- Retrieval-backed deployed answers can still miss normalized citations even when retrieval succeeds.
- Haiku 4.5 readiness for Bedrock Agents is not yet fully verified end to end in deployment.
