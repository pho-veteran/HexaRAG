# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current repository state

- HexaRAG is still in the requirements-and-plans stage. The implementation source of truth currently lives in:
  - `TASKS.md`
  - `docs/requirements.md`
  - `docs/superpowers/plans/2026-05-06-hexarag-v1.md`
  - `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
  - `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md`
  - `docs/superpowers/plans/2026-05-06-hexarag-infra.md`
  - `docs/superpowers/plans/2026-05-06-hexarag-testing.md`
- If a command or path from this file does not exist yet, do not invent a host-native workaround. Follow the relevant phase plan and keep Docker Compose as the local execution path.

## Fixed product decisions

- HexaRAG is an AWS-native W4 app, not a generic local demo.
- Primary orchestration is Amazon Bedrock + Bedrock AgentCore.
- Frontend is a Vite + React single-page app.
- Backend is a FastAPI API shaped for the UI and deployable behind Lambda/API Gateway.
- Local development, dependency installation, test execution, seeding, and evaluator runs must go through Docker Compose only.
- The UI is a single chat surface: chat on the left, always-visible observability panel on the right.
- Authentication is out of scope for v1.
- Memory is session-window only.
- L1-L4 are first-class requirements; L5 is stretch-readiness only.
- Contradiction handling must prefer the newest valid source and explain why it was chosen.

## Required workflow

- Start from `TASKS.md`, then execute the split phase plans in order.
- Treat the split plans as ownership boundaries:
  - foundation plan: local workspace + first frontend/backend slice
  - core runtime plan: W4 data services + AgentCore + memory + trace shaping
  - infra plan: Terraform + AWS + KB sync + `docs/aws.md`
  - testing plan: evaluator + regressions + final verification
- Do not collapse everything back into one monolithic plan.
- Do not add a host-installed Node/Python/Postgres workflow alongside Docker Compose.

## Documentation and tracking rule

Before considering any task complete, update the relevant docs and tracking files in the same task.

At minimum, review and update as needed:
- `TASKS.md` for progress state
- the active phase plan file if steps, file ownership, or execution order changed
- `docs/local-dev.md` when local commands or container workflow changes
- `docs/aws.md` when infrastructure or deployment wiring changes
- `docs/requirements.md` only when implementation decisions require a real requirements clarification

A task is not done if the code changed but the tracking/docs now misdescribe the repo.

## Common commands

Use these commands when the corresponding scaffold exists. If the repo has not reached that phase yet, use the phase plan rather than improvising.

### Local runtime
- `docker compose up --build frontend backend postgres`

### Frontend
- `docker compose run --rm frontend npm run test -- --run`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx --run`
- `docker compose run --rm frontend npm run test -- src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`

### Backend
- `docker compose run --rm backend uv run pytest -q`
- `docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm backend uv run pytest tests/services/test_session_store.py tests/services/test_trace_formatter.py -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py`
- `docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help`

### Evaluation
- `docker compose run --rm backend uv run python /workspace/scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l1 --limit 3`

### Terraform
Run from `infra/terraform`:
- `terraform fmt -check`
- `terraform validate`

## Architecture overview

### Product surface
- The app is a single-screen chat experience for trainers and team members.
- The assistant answer must be readable on its own, but the right-side observability panel is always visible and is part of the product, not an internal-only debug aid.
- The observability panel needs to surface citations, conflict resolution, tool calls, memory context used for the turn, grounding notes, and degraded-mode/uncertainty notes.

### Backend composition
- The FastAPI layer is responsible for shaping the UI contract, not for hiding system behavior.
- The chat endpoint is the composition point that combines:
  - recent-turn session memory
  - Bedrock AgentCore runtime invocation
  - tool/data access
  - trace formatting into a UI-facing structure
- Keep orchestration, tool adapters, memory storage, and trace formatting in separate modules so each concern stays inspectable.

### Source-of-truth boundaries
- Knowledge base markdown documents are the source of truth for qualitative information: policies, ownership, service descriptions, architecture context, postmortems, and planning/review notes.
- Structured data is the source of truth for exact historical/tabular values: monthly costs, incidents, SLA targets, daily metrics.
- The live monitoring path is the source of truth for current operational state: status, latency, error rate, request volume, CPU, memory.
- Recent session turns are the source of truth for follow-up references in L4 conversations.
- Do not answer exact numeric questions from retrieved docs when a structured or live source is required.

### Expected deployment shape
- Frontend: S3 + CloudFront
- API layer: FastAPI on Lambda behind API Gateway
- Monitoring API equivalent: Lambda/API route used as the live-state tool surface
- Structured historical data: PostgreSQL
- Session memory: DynamoDB
- Knowledge base source: S3-backed documents wired into Bedrock Knowledge Bases
- KB sync: schedule-driven via EventBridge
- Infrastructure: Terraform-managed

## W4-specific behavior to preserve

- L1: single-document retrieval with citation.
- L2: multi-source synthesis with explicit contradiction handling.
- L3: grounded numeric/live answers via tools and managed data integrations.
- L4: recent-turn continuity across retrieval and tool-backed follow-ups.
- L5: design traces and orchestration so multi-step investigation can be added later, but do not expand v1 scope into full L5 delivery.

## Contract and naming consistency

- Keep `session_id` as the JSON field for chat requests/responses.
- The core response shape is `ChatResponse.message.trace`.
- Do not mix frontend camelCase and backend snake_case ad hoc. If frontend and backend field names differ, use explicit centralized aliasing rather than one-off conversions.
- Keep these names aligned across code and docs:
  - `knowledge_base_id`
  - `knowledge_base_data_source_id`
  - `agent_runtime_arn`
  - trace/citation naming used by the chat contract

## When updating the architecture

If implementation forces a meaningful architecture change, update the matching plan/doc in the same task instead of letting `CLAUDE.md`, `TASKS.md`, and the phase plans drift apart.
