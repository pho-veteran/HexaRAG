# HexaRAG Local Development

## Rules
- Do not run Node, Python, PostgreSQL, or test commands directly on the host.
- Use Docker Compose for app runtime, tests, and data seeding.

## Common commands
- `docker compose up --build frontend backend postgres`
- `docker compose run --rm frontend npm run test -- --run`
- `docker compose run --rm backend uv run pytest -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py`

## Phase 1 vertical slice verification
- `docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`

## Phase 2 core runtime verification
- `docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_session_store.py tests/services/test_trace_formatter.py -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py --help`
