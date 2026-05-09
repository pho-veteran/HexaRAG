# HexaRAG Local Development

## Rules
- Do not run Node, Python, PostgreSQL, or test commands directly on the host.
- Use Docker Compose for app runtime, tests, builds, and data seeding.

## Common commands
- `docker compose up --build frontend backend postgres`
- `docker compose run --rm frontend npm run test -- --run`
- `docker compose run --rm backend uv run pytest -q`
- `docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py tests/services/test_audit_scoring.py -q`
- `docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py`

## Frontend API base URL rule
- The `frontend` service now scopes `VITE_API_BASE_URL=http://backend:8000` to the dev-server command only, so local `docker compose up` still works without leaking that Docker-only URL into production builds.
- For AWS deployment builds, pass the deployed backend URL explicitly when building frontend assets. Example: `VITE_API_BASE_URL="https://your-backend-api-url" docker compose run --rm frontend sh -lc 'node node_modules/vite/bin/vite.js build'`.
- Do not rely on the frontend service definition to provide the production API URL during `docker compose run`; that path previously baked `http://backend:8000` into the shipped bundle.

## Phase 1 vertical slice verification
- `docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`

## Phase 2 core runtime verification
- `docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_session_store.py tests/services/test_trace_formatter.py -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py --help`

These focused analytics and monitoring checks now cover Q1 historical costs, SLA targets, incident summaries, daily-latency queries, and the `/status/{service_name}` plus `/incidents` monitoring endpoints used by the live audit.

## Focused runtime/trace verification
- `docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py tests/services/test_chat_service.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run`

These focused checks cover:
- backend-owned Bedrock instruction contract
- runtime/model metadata shaping
- richer Thinking-tab narrative fields
- per-page session ID behavior that resets on remount/refresh

## Phase 3 infrastructure and KB sync verification
- `docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help`
- `docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket <knowledge-base-bucket>`
- from `infra/terraform`: `terraform fmt -check`
- from `infra/terraform`: `terraform validate`

## Deploy-readiness verification
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_chat_service.py tests/services/test_session_store.py tests/test_cors.py tests/services/test_lambda_packaging.py tests/scripts/test_sync_knowledge_base.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm frontend npm run test -- src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run`
- `docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py`
- from `infra/terraform`: `terraform fmt -check`
- from `infra/terraform`: `terraform validate`

## Phase 4 evaluation and final verification
- `docker compose up -d --build backend postgres`
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_trace_formatter.py tests/services/test_evaluator_inputs.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`
- `docker compose run --rm backend uv run pytest -q`
- `docker compose exec backend uv run python scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l1 --mode replay --output /workspace/repo/backend/evaluate_w4_l1_replay.json --limit 3`
- `docker compose exec backend uv run python scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l5 --mode audit --output /workspace/repo/backend/evaluate_w4_l5_audit.json --limit 1`
- `docker compose down`

## Phase 5 UI audit coverage
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run audit:ui`

These UI audit checks now pin the contradiction, memory, and uncertainty surfaces that the live browser audit expects across the inspection console tabs.
