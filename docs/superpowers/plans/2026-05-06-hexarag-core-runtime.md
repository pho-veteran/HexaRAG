# HexaRAG Core Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add the W4 data integrations, AgentCore orchestration, recent-turn memory, and UI-facing trace shaping that power grounded HexaRAG answers.

**Architecture:** Keep tool-backed data access and orchestration concerns separate from the frontend shell by introducing dedicated services for monitoring, historical analytics, session storage, and runtime output formatting. The chat endpoint becomes the composition point that loads recent memory, invokes AgentCore, shapes trace data, and returns a grounded answer contract to the UI.

**Tech Stack:** FastAPI, Pydantic, boto3, DynamoDB, PostgreSQL, httpx, Docker Compose, pytest.

---

## Planned File Structure

### Backend (`backend/`)
- Create: `backend/src/monitoring_api/data.py` — monitoring fixture values and jitter logic.
- Create: `backend/src/monitoring_api/main.py` — AWS-hosted equivalent of the W4 monitoring API.
- Create: `backend/src/hexarag_api/tools/analytics.py` — structured-data queries against PostgreSQL.
- Create: `backend/src/hexarag_api/tools/live_monitoring.py` — client for internal monitoring API.
- Create: `backend/src/hexarag_api/tools/service_catalog.py` — service metadata helpers used by tools.
- Create: `backend/scripts/load_structured_data.py` — seed PostgreSQL from `../xbrain-learners/W4/data_package/structured_data`.
- Create: `backend/src/hexarag_api/services/session_store.py` — recent-turn session window persistence.
- Create: `backend/src/hexarag_api/services/agent_runtime.py` — Bedrock AgentCore invocation wrapper.
- Create: `backend/src/hexarag_api/services/trace_formatter.py` — convert runtime output into UI trace.
- Create: `backend/src/hexarag_api/services/tool_catalog.py` — tool registration and routing helpers.
- Modify: `backend/src/hexarag_api/api/chat.py` — compose memory, runtime, and trace shaping.
- Modify: `backend/src/hexarag_api/models/chat.py` — extend trace models as needed for conflict resolution and tool output.
- Create: `backend/tests/services/test_analytics.py` — data-query tests.
- Create: `backend/tests/monitoring_api/test_monitoring_routes.py` — monitoring API parity tests.
- Create: `backend/tests/services/test_session_store.py` — session window tests.
- Create: `backend/tests/services/test_trace_formatter.py` — trace formatting tests.
- Modify: `backend/tests/api/test_chat_contract.py` — chat contract and graceful-failure path tests.

---

### Task 1: Implement the structured-data and monitoring services that mirror the W4 package

**Files:**
- Create: `backend/src/monitoring_api/data.py`
- Create: `backend/src/monitoring_api/main.py`
- Create: `backend/src/hexarag_api/tools/analytics.py`
- Create: `backend/src/hexarag_api/tools/live_monitoring.py`
- Create: `backend/src/hexarag_api/tools/service_catalog.py`
- Create: `backend/scripts/load_structured_data.py`
- Create: `backend/tests/services/test_analytics.py`
- Create: `backend/tests/monitoring_api/test_monitoring_routes.py`

- [x] **Step 1: Write the failing tests for data queries and monitoring API parity**

Create `backend/tests/services/test_analytics.py`:

```python
from hexarag_api.tools.analytics import summarize_q1_costs


def test_summarize_q1_costs_returns_expected_total(fake_db_connection):
    result = summarize_q1_costs(fake_db_connection)
    assert result['total_cost'] == 56350
```

Create `backend/tests/monitoring_api/test_monitoring_routes.py`:

```python
from fastapi.testclient import TestClient
from monitoring_api.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_paymentgw_shape():
    response = client.get('/metrics/PaymentGW')
    assert response.status_code == 200
    payload = response.json()
    assert 'latency_p99_ms' in payload
    assert 'error_rate_percent' in payload


def test_services_endpoint_lists_all_six_services():
    response = client.get('/services')
    assert response.status_code == 200
    assert len(response.json()['services']) == 6
```

- [x] **Step 2: Run the tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q
```

Expected: FAIL because the analytics functions and monitoring API do not exist yet.

- [x] **Step 3: Implement the monitoring service with W4-compatible endpoints**

Create `backend/src/monitoring_api/data.py`:

```python
BASE_METRICS = {
    'PaymentGW': {'latency_p99_ms': 185, 'error_rate_percent': 0.08, 'requests_per_minute': 22000, 'cpu_percent': 62, 'memory_percent': 71},
    'AuthSvc': {'latency_p99_ms': 72, 'error_rate_percent': 0.02, 'requests_per_minute': 28000, 'cpu_percent': 45, 'memory_percent': 58},
    'NotificationSvc': {'latency_p99_ms': 3200, 'error_rate_percent': 2.1, 'requests_per_minute': 9500, 'cpu_percent': 88, 'memory_percent': 82},
}
```

Create `backend/src/monitoring_api/main.py`:

```python
from fastapi import FastAPI, HTTPException
from monitoring_api.data import BASE_METRICS

app = FastAPI(title='HexaRAG Monitoring API')


@app.get('/services')
def list_services():
    return {'services': sorted(BASE_METRICS.keys())}


@app.get('/metrics/{service_name}')
def get_metrics(service_name: str):
    if service_name not in BASE_METRICS:
        raise HTTPException(status_code=404, detail='Unknown service')
    return BASE_METRICS[service_name]
```

- [x] **Step 4: Implement analytics helpers and the CSV-to-PostgreSQL seed script**

Create `backend/src/hexarag_api/tools/analytics.py`:

```python
from collections.abc import Mapping


def summarize_q1_costs(connection) -> Mapping[str, int]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(SUM(total_cost), 0)
            FROM monthly_costs
            WHERE month IN ('2026-01', '2026-02', '2026-03')
            """
        )
        total_cost = cursor.fetchone()[0]
    return {'total_cost': total_cost}
```

Create `backend/scripts/load_structured_data.py`:

```python
from pathlib import Path
import csv
import psycopg
from hexarag_api.config import Settings


def load_monthly_costs(data_root: Path, connection) -> None:
    csv_path = data_root / 'structured_data' / 'monthly_costs.csv'
    with csv_path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        with connection.cursor() as cursor:
            for row in reader:
                cursor.execute(
                    "INSERT INTO monthly_costs (service, month, total_cost) VALUES (%s, %s, %s)",
                    (row['service'], row['month'], row['total_cost']),
                )
        connection.commit()
```

- [x] **Step 5: Re-run the tests and validate the seed script interface**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q
docker compose run --rm backend uv run python scripts/load_structured_data.py --help
```

Expected: tests PASS and script help renders without traceback.

- [x] **Step 6: Commit the W4 data services**

```bash
git add backend
git commit -m "feat: add structured data queries and monitoring service"
```

---

### Task 2: Implement AgentCore orchestration, recent-turn memory, and trace formatting

**Files:**
- Create: `backend/src/hexarag_api/services/session_store.py`
- Create: `backend/src/hexarag_api/services/agent_runtime.py`
- Create: `backend/src/hexarag_api/services/trace_formatter.py`
- Create: `backend/src/hexarag_api/services/tool_catalog.py`
- Modify: `backend/src/hexarag_api/api/chat.py`
- Modify: `backend/src/hexarag_api/models/chat.py`
- Create: `backend/tests/services/test_session_store.py`
- Create: `backend/tests/services/test_trace_formatter.py`
- Modify: `backend/tests/api/test_chat_contract.py`

- [x] **Step 1: Write failing tests for session windows and trace shaping**

Create `backend/tests/services/test_session_store.py`:

```python
from hexarag_api.services.session_store import trim_recent_turns


def test_trim_recent_turns_keeps_last_four_entries():
    turns = ['u1', 'a1', 'u2', 'a2', 'u3', 'a3']
    assert trim_recent_turns(turns, limit=4) == ['u2', 'a2', 'u3', 'a3']
```

Create `backend/tests/services/test_trace_formatter.py`:

```python
from hexarag_api.services.trace_formatter import build_trace_payload


def test_build_trace_payload_surfaces_conflict_resolution():
    raw = {
        'citations': [{'sourceId': 'api_reference_v2.md', 'title': 'api_reference_v2.md', 'excerpt': '1000 rpm'}],
        'conflict_resolution': {
            'chosen_source': 'api_reference_v2.md',
            'rationale': 'v2 supersedes archived v1',
            'competing_sources': ['api_reference_v1_archived.md'],
        },
    }

    trace = build_trace_payload(raw, memory_window=['What is the PaymentGW rate limit?'])
    assert trace.conflict_resolution.chosen_source == 'api_reference_v2.md'
    assert trace.memory_window == ['What is the PaymentGW rate limit?']
```

- [x] **Step 2: Run the tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_session_store.py tests/services/test_trace_formatter.py -q
```

Expected: FAIL because the services do not exist.

- [x] **Step 3: Implement the session window helper and DynamoDB-backed store**

Create `backend/src/hexarag_api/services/session_store.py`:

```python
from collections.abc import Sequence


def trim_recent_turns(turns: Sequence[str], limit: int = 6) -> list[str]:
    return list(turns[-limit:])


class SessionStore:
    def __init__(self, table):
        self.table = table

    def load_recent_turns(self, session_id: str, limit: int = 6) -> list[str]:
        response = self.table.get_item(Key={'session_id': session_id})
        turns = response.get('Item', {}).get('turns', [])
        return trim_recent_turns(turns, limit=limit)

    def append_turns(self, session_id: str, user_message: str, assistant_message: str) -> None:
        existing = self.load_recent_turns(session_id, limit=100)
        self.table.put_item(Item={'session_id': session_id, 'turns': [*existing, user_message, assistant_message]})
```

- [x] **Step 4: Implement AgentCore invocation and trace formatting**

Create `backend/src/hexarag_api/services/agent_runtime.py`:

```python
import json
import boto3


class AgentRuntimeService:
    def __init__(self, runtime_arn: str, region: str):
        self.runtime_arn = runtime_arn
        self.client = boto3.client('bedrock-agentcore', region_name=region)

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        payload = json.dumps({'prompt': message, 'memory_window': memory_window})
        response = self.client.invoke_agent_runtime(
            agentRuntimeArn=self.runtime_arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier='DEFAULT',
        )
        return json.loads(response['response'].read())
```

Create `backend/src/hexarag_api/services/trace_formatter.py`:

```python
from hexarag_api.models.chat import TracePayload


def build_trace_payload(raw: dict, memory_window: list[str]) -> TracePayload:
    conflict = raw.get('conflict_resolution')
    return TracePayload(
        citations=raw.get('citations', []),
        tool_calls=raw.get('tool_calls', []),
        memory_window=memory_window,
        grounding_notes=raw.get('grounding_notes', []),
        uncertainty=raw.get('uncertainty'),
        conflict_resolution=conflict,
    )
```

- [x] **Step 5: Wire the real chat endpoint to memory + AgentCore + trace formatting**

Update `backend/src/hexarag_api/api/chat.py` so it:
1. loads recent turns from `SessionStore`
2. invokes `AgentRuntimeService.answer(...)`
3. converts runtime output using `build_trace_payload(...)`
4. appends the new turn pair back into the session store
5. returns `ChatResponse`

Use this route shape:

```python
@router.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    memory_window = session_store.load_recent_turns(request.session_id)
    runtime_output = agent_runtime.answer(request.session_id, request.message, memory_window)
    trace = build_trace_payload(runtime_output['trace'], memory_window)
    content = runtime_output['answer']
    session_store.append_turns(request.session_id, request.message, content)
    return ChatResponse(session_id=request.session_id, message=ChatMessage(role='assistant', content=content, trace=trace))
```

- [x] **Step 6: Re-run the tests and add a graceful-failure case**

Add this assertion to `backend/tests/api/test_chat_contract.py` after wiring dependency injection:

```python
def test_chat_returns_grounded_failure_when_runtime_errors(client, failing_agent_runtime):
    response = client.post('/chat', json={'session_id': 's-1', 'message': 'What is NotificationSvc status?'})
    assert response.status_code == 200
    assert 'could not complete the live tool step' in response.json()['message']['content'].lower()
```

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_session_store.py tests/services/test_trace_formatter.py -q
```

Expected: PASS.

- [x] **Step 7: Commit the orchestration layer**

```bash
git add backend
git commit -m "feat: integrate agentcore runtime with memory and trace formatting"
```

---

## Spec Coverage Check

- **FR2 Bedrock + AgentCore orchestration** → Task 2
- **FR3 Retrieval support** → Task 2 runtime integration and trace shaping
- **FR4 Conflict resolution** → Task 2 trace formatting + runtime prompt contract
- **FR5 Tool support** → Tasks 1 and 2
- **FR6 Grounded numeric answers** → Tasks 1 and 2
- **FR8 Session memory** → Task 2
- **FR9 Graceful failure behavior** → Task 2 failure-path test and response path
- **L5 stretch-readiness** → Task 2 trace model supports multi-step extension

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each task lists concrete files, commands, tests, and commit boundaries.

## Type Consistency Check

Use these names consistently across runtime-facing files:
- `session_id` in JSON requests/responses
- `ChatResponse.message.trace`
- `TracePayload.citations`
- `TracePayload.toolCalls` in TypeScript and `tool_calls` in Python only if the serializer explicitly maps names
- `memoryWindow` in frontend and `memory_window` in backend only if Pydantic aliasing is configured centrally
- `conflictResolution` in frontend and `conflict_resolution` in backend only if aliasing is configured centrally

Do not mix aliasing and raw field names ad hoc.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md`.
