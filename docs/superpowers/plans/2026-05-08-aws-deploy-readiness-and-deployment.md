# AWS Deploy Readiness and Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make HexaRAG truthfully deployable to AWS, then deploy it so the live frontend and backend behavior matches the repo’s documented app-functionality contract as closely as the current codebase can support.

**Architecture:** Move `/chat` onto a real service boundary with explicit runtime selection and session-store selection so local stub behavior and deployed AWS behavior are intentional rather than accidental. Close the deploy blockers around CORS/origin handling, Lambda entrypoints, packaging, Terraform outputs, and trace visibility, then verify locally through Docker Compose before using the AWS CLI to deploy and validate the live stack.

**Tech Stack:** Docker Compose, FastAPI, Pydantic, boto3, Mangum, React, TypeScript, Vitest, pytest, Terraform, AWS CLI.

> **Update 2026-05-08:** The Bedrock runtime migration in this plan has been implemented. Wherever this document still names `AgentCore`, `agent_runtime_arn`, or `AGENT_RUNTIME_ARN`, treat those references as superseded by Bedrock Agents with `agent_id`, `agent_alias_id`, and the Bedrock agent runtime `InvokeAgent` path.

---

## Planned File Responsibilities

### Backend runtime and API
- Modify: `backend/src/hexarag_api/config.py` — add explicit runtime mode and multi-origin parsing for local plus deployed operation.
- Modify: `backend/src/hexarag_api/api/chat.py` — reduce the route to request parsing plus chat-service delegation.
- Modify: `backend/src/hexarag_api/main.py` — wire CORS from a parsed origin list instead of a single origin.
- Modify: `backend/src/hexarag_api/services/agent_runtime.py` — keep the real AgentCore client, move the stub runtime here, and normalize runtime output.
- Modify: `backend/src/hexarag_api/services/session_store.py` — add in-memory and DynamoDB table adapters plus a factory.
- Create: `backend/src/hexarag_api/services/chat_service.py` — own recent-turn loading, runtime invocation, fallback trace shaping, and turn persistence.
- Create: `backend/src/hexarag_api/services/service_factory.py` — cache the selected runtime and session-store dependencies behind `get_chat_service()`.
- Modify: `backend/scripts/sync_knowledge_base.py` — expose a real Lambda-safe handler instead of only a CLI `main()`.
- Modify: `backend/src/monitoring_api/main.py` — expose a Mangum `handler` so the Terraform Lambda target is valid.

### Frontend trace contract and deployment-visible behavior
- Modify: `frontend/src/types/chat.ts` — include `conflictResolution` in the internal app trace type.
- Modify: `frontend/src/lib/api.ts` — map backend `conflict_resolution` into frontend camelCase.
- Modify: `frontend/src/features/trace/TracePanel.tsx` — surface contradiction resolution details in the observability tab.
- Modify: `frontend/src/features/trace/buildTraceNarrative.ts` — add a contradiction-resolution narrative step.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — verify the contradiction-resolution UI section.
- Modify: `frontend/src/features/trace/buildTraceNarrative.test.ts` — verify the contradiction-resolution narrative step.

### Packaging and infrastructure wiring
- Modify: `docker-compose.yml` — mount the repo root into the backend container so packaging commands can emit artifacts into `infra/terraform` without a host-native workflow.
- Create: `backend/src/hexarag_api/services/lambda_packaging.py` — define artifact specs and package-copy helpers for the three Lambda zips.
- Create: `backend/scripts/package_lambda_artifacts.py` — canonical Docker Compose packaging command that emits `backend.zip`, `monitoring.zip`, and `kb-sync.zip`.
- Modify: `infra/terraform/compute.tf` — set runtime mode and allowed origins for the deployed backend Lambda, and add `source_code_hash` values.
- Modify: `infra/terraform/scheduler.tf` — point the sync Lambda at a real handler and add `source_code_hash`.
- Modify: `infra/terraform/outputs.tf` — expose CloudFront values in addition to the existing API, bucket, session-table, and database outputs.
- Modify: `.gitignore` — ignore generated Lambda zip artifacts.

### Tests
- Modify: `backend/tests/api/test_chat_contract.py` — verify the route delegates to the chat-service factory and preserves the response contract.
- Create: `backend/tests/services/test_chat_service.py` — cover runtime success, runtime fallback, and memory persistence.
- Modify: `backend/tests/services/test_session_store.py` — cover the DynamoDB-backed session-table factory.
- Create: `backend/tests/test_cors.py` — verify a CloudFront-style origin is accepted when configured.
- Create: `backend/tests/services/test_lambda_packaging.py` — verify the artifact specs target the correct zip files and handlers.
- Create: `backend/tests/scripts/test_sync_knowledge_base.py` — verify the scheduled Lambda handler starts an ingestion job.
- Modify: `backend/tests/monitoring_api/test_monitoring_routes.py` — verify the monitoring module exposes a Lambda handler in addition to the HTTP routes.

### Docs and tracking
- Modify: `docs/aws.md` — replace vague manual packaging with the canonical packaging command, include new outputs, and keep the Bedrock prerequisite sequence honest.
- Modify: `docs/app-functionality.md` — update the rows affected by the runtime-selection, conflict-resolution, CORS, and output-discoverability changes.
- Modify: `docs/local-dev.md` — add the packaging command and readiness verification commands.
- Modify: `TASKS.md` — index this plan and note the deploy-readiness follow-up.

---

### Task 1: Refactor `/chat` onto a real runtime and session-store service

**Files:**
- Modify: `backend/src/hexarag_api/config.py`
- Modify: `backend/src/hexarag_api/services/agent_runtime.py`
- Modify: `backend/src/hexarag_api/services/session_store.py`
- Create: `backend/src/hexarag_api/services/chat_service.py`
- Create: `backend/src/hexarag_api/services/service_factory.py`
- Modify: `backend/src/hexarag_api/api/chat.py`
- Modify: `backend/tests/api/test_chat_contract.py`
- Modify: `backend/tests/services/test_session_store.py`
- Create: `backend/tests/services/test_chat_service.py`

- [ ] **Step 1: Write the failing backend service and route tests**

Create `backend/tests/services/test_chat_service.py`:

```python
from hexarag_api.services.chat_service import ChatService
from hexarag_api.services.session_store import InMemorySessionTable, SessionStore, build_session_table
from hexarag_api.config import Settings


class FakeRuntime:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, str, list[str]]] = []

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        self.calls.append((session_id, message, memory_window))
        if self.should_fail:
            raise RuntimeError('live tool unavailable')

        return {
            'answer': f'AWS-mode answer for: {message}',
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-ops',
                        'title': 'ops.md',
                        'excerpt': 'Operational ownership details.',
                    }
                ],
                'tool_calls': [],
                'grounding_notes': ['Returned from the fake runtime.'],
                'uncertainty': None,
            },
        }


class FakeDynamoResource:
    def __init__(self) -> None:
        self.requested_tables: list[str] = []

    def Table(self, table_name: str):
        self.requested_tables.append(table_name)
        return object()


def test_chat_service_persists_turns_and_passes_memory_window() -> None:
    table = InMemorySessionTable()
    session_store = SessionStore(table)
    session_store.append_turns('memory-session', 'Who owns Notifications?', 'Team Mercury owns Notifications.')
    runtime = FakeRuntime()
    service = ChatService(
        session_store=session_store,
        runtime=runtime,
        recent_turn_limit=6,
        failure_message='fallback',
    )

    response = service.answer('memory-session', 'What is PaymentGW latency?')

    assert response.message.content == 'AWS-mode answer for: What is PaymentGW latency?'
    assert runtime.calls == [
        (
            'memory-session',
            'What is PaymentGW latency?',
            ['Who owns Notifications?', 'Team Mercury owns Notifications.'],
        )
    ]
    assert session_store.load_recent_turns('memory-session', limit=4) == [
        'Team Mercury owns Notifications.',
        'What is PaymentGW latency?',
        'AWS-mode answer for: What is PaymentGW latency?',
    ]


def test_chat_service_returns_grounded_fallback_when_runtime_raises() -> None:
    service = ChatService(
        session_store=SessionStore(InMemorySessionTable()),
        runtime=FakeRuntime(should_fail=True),
        recent_turn_limit=6,
        failure_message='Could not complete the live tool step. Here is the best grounded fallback available right now.',
    )

    response = service.answer('fallback-session', 'What is NotificationSvc status?')

    assert 'could not complete the live tool step' in response.message.content.lower()
    assert response.message.trace.citations == []
    assert response.message.trace.tool_calls[0].status == 'error'
    assert response.message.trace.uncertainty == 'Live monitoring data is temporarily unavailable.'


def test_build_session_table_uses_dynamodb_in_aws_mode(monkeypatch) -> None:
    fake_resource = FakeDynamoResource()

    class FakeBoto3:
        @staticmethod
        def resource(service_name: str, region_name: str):
            assert service_name == 'dynamodb'
            assert region_name == 'us-east-1'
            return fake_resource

    monkeypatch.setattr('hexarag_api.services.session_store.boto3', FakeBoto3)

    table = build_session_table(
        Settings(runtime_mode='aws', aws_region='us-east-1', session_table_name='hexarag-sessions')
    )

    assert table.__class__.__name__ == 'DynamoSessionTable'
    assert fake_resource.requested_tables == ['hexarag-sessions']
```

Replace `backend/tests/api/test_chat_contract.py` with:

```python
from fastapi.testclient import TestClient

from hexarag_api.main import create_app
from hexarag_api.models.chat import ChatMessage, ChatResponse, TracePayload


class FakeChatService:
    def answer(self, session_id: str, message: str) -> ChatResponse:
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(
                role='assistant',
                content=f'Factory answer for: {message}',
                trace=TracePayload(
                    citations=[],
                    inline_citations=[],
                    tool_calls=[],
                    memory_window=['prior turn'],
                    grounding_notes=['Returned by the fake chat service.'],
                    uncertainty=None,
                ),
            ),
        )


def test_chat_route_delegates_to_factory_service(monkeypatch) -> None:
    from hexarag_api.api import chat as chat_api

    monkeypatch.setattr(chat_api, 'get_chat_service', lambda: FakeChatService())
    client = TestClient(create_app())

    response = client.post(
        '/chat',
        json={
            'session_id': 'route-session',
            'message': 'Who owns Notifications?',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'session_id': 'route-session',
        'message': {
            'role': 'assistant',
            'content': 'Factory answer for: Who owns Notifications?',
            'trace': {
                'citations': [],
                'inline_citations': [],
                'tool_calls': [],
                'memory_window': ['prior turn'],
                'grounding_notes': ['Returned by the fake chat service.'],
                'uncertainty': None,
                'conflict_resolution': None,
            },
        },
    }
```

- [ ] **Step 2: Run the backend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_chat_service.py tests/services/test_session_store.py -q
```

Expected: FAIL because `ChatService`, `get_chat_service()`, and the DynamoDB-aware session-table factory do not exist yet.

- [ ] **Step 3: Implement the runtime, chat-service, and session-store boundaries**

Update `backend/src/hexarag_api/config.py` to make runtime selection explicit:

```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'HexaRAG API'
    allowed_origins: str = 'http://localhost:5173'
    runtime_mode: Literal['stub', 'aws'] = 'stub'
    aws_region: str = 'us-east-1'
    database_url: str = 'postgresql://hexarag:hexarag@postgres:5432/hexarag'
    session_table_name: str = 'hexarag-sessions'
    monitoring_base_url: str = 'http://backend:8001'
    w4_data_root: str = '/workspace/W4/data_package'
    knowledge_base_id: str = ''
    knowledge_base_data_source_id: str = ''
    agent_runtime_arn: str = ''
    failure_message: str = 'Could not complete the live tool step. Here is the best grounded fallback available right now.'
    recent_turn_limit: int = 6

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Replace `backend/src/hexarag_api/services/agent_runtime.py` with:

```python
import json
from typing import Any, Protocol

import boto3

FAILURE_TRIGGER_MESSAGE = 'trigger failure'


class ChatRuntime(Protocol):
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
        ...


class StubAgentRuntime:
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
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
                'grounding_notes': ['This is a deterministic stub response for the deploy-readiness slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        }


class AgentRuntimeService:
    def __init__(self, runtime_arn: str, region: str) -> None:
        self.runtime_arn = runtime_arn
        self.client = boto3.client('bedrock-agentcore', region_name=region)

    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict[str, Any]:
        payload = json.dumps({'prompt': message, 'memory_window': memory_window})
        response = self.client.invoke_agent_runtime(
            agentRuntimeArn=self.runtime_arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier='DEFAULT',
        )
        raw = json.loads(response['response'].read())
        if 'answer' in raw:
            return raw
        if 'message' in raw:
            return {'answer': raw['message'], 'trace': raw.get('trace', {})}
        raise RuntimeError('Agent runtime returned an unsupported payload shape.')
```

Replace `backend/src/hexarag_api/services/session_store.py` with:

```python
from collections.abc import Sequence

import boto3

from hexarag_api.config import Settings


class InMemorySessionTable:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, list[str]]] = {}

    def get_item(self, Key: dict[str, str]) -> dict[str, dict[str, list[str]]]:
        item = self.items.get(Key['session_id'])
        return {'Item': item} if item else {}

    def put_item(self, Item: dict[str, list[str] | str]) -> None:
        session_id = Item['session_id']
        turns = Item['turns']
        self.items[session_id] = {'session_id': session_id, 'turns': turns}


class DynamoSessionTable:
    def __init__(self, table) -> None:
        self.table = table

    def get_item(self, Key: dict[str, str]) -> dict:
        return self.table.get_item(Key=Key)

    def put_item(self, Item: dict[str, list[str] | str]) -> None:
        self.table.put_item(Item=Item)


IN_MEMORY_SESSION_TABLE = InMemorySessionTable()


def trim_recent_turns(turns: Sequence[str], limit: int = 6) -> list[str]:
    return list(turns[-limit:])


class SessionStore:
    def __init__(self, table) -> None:
        self.table = table

    def load_recent_turns(self, session_id: str, limit: int = 6) -> list[str]:
        response = self.table.get_item(Key={'session_id': session_id})
        turns = response.get('Item', {}).get('turns', [])
        return trim_recent_turns(turns, limit=limit)

    def append_turns(self, session_id: str, user_message: str, assistant_message: str) -> None:
        existing = self.load_recent_turns(session_id, limit=100)
        self.table.put_item(Item={'session_id': session_id, 'turns': [*existing, user_message, assistant_message]})


def build_session_table(settings: Settings):
    if settings.runtime_mode == 'aws':
        table = boto3.resource('dynamodb', region_name=settings.aws_region).Table(settings.session_table_name)
        return DynamoSessionTable(table)
    return IN_MEMORY_SESSION_TABLE
```

Create `backend/src/hexarag_api/services/chat_service.py`:

```python
from hexarag_api.models.chat import ChatMessage, ChatResponse
from hexarag_api.services.trace_formatter import build_trace_payload


class ChatService:
    def __init__(self, session_store, runtime, recent_turn_limit: int, failure_message: str) -> None:
        self.session_store = session_store
        self.runtime = runtime
        self.recent_turn_limit = recent_turn_limit
        self.failure_message = failure_message

    def answer(self, session_id: str, message: str) -> ChatResponse:
        memory_window = self.session_store.load_recent_turns(session_id, limit=self.recent_turn_limit)

        try:
            runtime_output = self.runtime.answer(session_id, message, memory_window)
            content = runtime_output['answer']
            trace = build_trace_payload(runtime_output.get('trace', {}), memory_window)
        except RuntimeError:
            content = self.failure_message
            trace = build_trace_payload(
                {
                    'citations': [],
                    'inline_citations': [],
                    'tool_calls': [
                        {
                            'name': 'monitoring_snapshot',
                            'status': 'error',
                            'summary': 'Live monitoring call failed.',
                            'input': {'question': message},
                            'output': None,
                        }
                    ],
                    'grounding_notes': ['Returned fallback answer because the live tool step failed.'],
                    'uncertainty': 'Live monitoring data is temporarily unavailable.',
                },
                memory_window,
            )

        self.session_store.append_turns(session_id, message, content)
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(role='assistant', content=content, trace=trace),
        )
```

Create `backend/src/hexarag_api/services/service_factory.py`:

```python
from functools import lru_cache

from hexarag_api.config import get_settings
from hexarag_api.services.agent_runtime import AgentRuntimeService, StubAgentRuntime
from hexarag_api.services.chat_service import ChatService
from hexarag_api.services.session_store import SessionStore, build_session_table


@lru_cache
def get_chat_service() -> ChatService:
    settings = get_settings()
    runtime = (
        AgentRuntimeService(settings.agent_runtime_arn, settings.aws_region)
        if settings.runtime_mode == 'aws'
        else StubAgentRuntime()
    )
    session_store = SessionStore(build_session_table(settings))
    return ChatService(
        session_store=session_store,
        runtime=runtime,
        recent_turn_limit=settings.recent_turn_limit,
        failure_message=settings.failure_message,
    )
```

Replace `backend/src/hexarag_api/api/chat.py` with:

```python
from fastapi import APIRouter

from hexarag_api.models.chat import ChatRequest, ChatResponse
from hexarag_api.services.service_factory import get_chat_service

router = APIRouter()


@router.post('/chat', response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    return get_chat_service().answer(request.session_id, request.message)
```

- [ ] **Step 4: Run the backend tests to verify the new service boundary passes**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_chat_service.py tests/services/test_session_store.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 5: Commit the backend runtime refactor**

```bash
git add backend/src/hexarag_api/config.py backend/src/hexarag_api/api/chat.py backend/src/hexarag_api/services/agent_runtime.py backend/src/hexarag_api/services/session_store.py backend/src/hexarag_api/services/chat_service.py backend/src/hexarag_api/services/service_factory.py backend/tests/api/test_chat_contract.py backend/tests/services/test_session_store.py backend/tests/services/test_chat_service.py
git commit -m "feat: refactor chat runtime selection for aws deploys"
```

---

### Task 2: Expose contradiction resolution in the frontend and make CORS deployment-safe

**Files:**
- Modify: `backend/src/hexarag_api/main.py`
- Create: `backend/tests/test_cors.py`
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/features/trace/TracePanel.tsx`
- Modify: `frontend/src/features/trace/buildTraceNarrative.ts`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`
- Modify: `frontend/src/features/trace/buildTraceNarrative.test.ts`

- [ ] **Step 1: Write the failing CORS and contradiction-visibility tests**

Create `backend/tests/test_cors.py`:

```python
from fastapi.testclient import TestClient

from hexarag_api.config import Settings
from hexarag_api.main import create_app


def test_preflight_accepts_cloudfront_origin(monkeypatch) -> None:
    from hexarag_api import main as main_module

    monkeypatch.setattr(
        main_module,
        'get_settings',
        lambda: Settings(allowed_origins='http://localhost:5173,https://d111111abcdef8.cloudfront.net'),
    )
    client = TestClient(create_app())

    response = client.options(
        '/chat',
        headers={
            'Origin': 'https://d111111abcdef8.cloudfront.net',
            'Access-Control-Request-Method': 'POST',
        },
    )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'https://d111111abcdef8.cloudfront.net'
```

Add this test to `frontend/src/features/trace/TracePanel.test.tsx`:

```tsx
  it('renders contradiction-resolution details when the trace provides them', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-v2',
              title: 'api_reference_v2.md',
              excerpt: '1000 rpm',
              version: 'v2',
              recencyNote: undefined,
            },
          ],
          inlineCitations: [],
          toolCalls: [],
          memoryWindow: [],
          groundingNotes: ['Used the newest API document.'],
          uncertainty: null,
          conflictResolution: {
            chosenSource: 'api_reference_v2.md',
            rationale: 'v2 supersedes archived v1.',
            competingSources: ['api_reference_v1_archived.md'],
          },
        }}
        error={null}
        traceLabel="Response 2"
        activeTab="observability"
        onTabChange={() => undefined}
        onOpenMockup={() => undefined}
      />,
    )

    expect(screen.getByText('Conflict resolution')).toBeInTheDocument()
    expect(screen.getByText('api_reference_v2.md')).toBeInTheDocument()
    expect(screen.getByText('v2 supersedes archived v1.')).toBeInTheDocument()
  })
```

Replace `frontend/src/features/trace/buildTraceNarrative.test.ts` with:

```ts
import { buildTraceNarrative } from './buildTraceNarrative'

describe('buildTraceNarrative', () => {
  it('builds an ordered narrative from sources, tools, memory, contradiction handling, grounding, and uncertainty', () => {
    expect(
      buildTraceNarrative({
        citations: [
          {
            sourceId: 'doc-ownership',
            title: 'ownership.md',
            excerpt: 'Notifications is owned by Team Mercury.',
            version: undefined,
            recencyNote: undefined,
          },
        ],
        inlineCitations: [],
        toolCalls: [
          {
            name: 'knowledge_base_lookup',
            status: 'success',
            summary: 'Retrieved ownership document',
            input: { question: 'Who owns the Notifications service?' },
            output: { source: 'ownership.md' },
          },
        ],
        memoryWindow: ['Prior question about latency'],
        groundingNotes: ['Used the ownership document.'],
        uncertainty: 'Live monitoring was not needed for this answer.',
        conflictResolution: {
          chosenSource: 'api_reference_v2.md',
          rationale: 'v2 supersedes archived v1.',
          competingSources: ['api_reference_v1_archived.md'],
        },
      }),
    ).toEqual([
      {
        id: 'sources',
        title: 'Checked sources',
        detail: 'Reviewed 1 retrieved source: ownership.md.',
      },
      {
        id: 'tools',
        title: 'Ran tools',
        detail: 'Used 1 tool call to validate the answer: knowledge_base_lookup.',
      },
      {
        id: 'memory',
        title: 'Used session context',
        detail: 'Considered 1 recent context item from the conversation.',
      },
      {
        id: 'contradiction',
        title: 'Resolved contradiction',
        detail: 'Preferred api_reference_v2.md because v2 supersedes archived v1..',
      },
      {
        id: 'grounding',
        title: 'Grounded answer',
        detail: 'Used the ownership document.',
      },
      {
        id: 'uncertainty',
        title: 'Called out uncertainty',
        detail: 'Live monitoring was not needed for this answer.',
      },
    ])
  })

  it('still produces a grounded-answer step when the trace is sparse', () => {
    expect(
      buildTraceNarrative({
        citations: [],
        inlineCitations: [],
        toolCalls: [],
        memoryWindow: [],
        groundingNotes: [],
        uncertainty: null,
        conflictResolution: undefined,
      }),
    ).toEqual([
      {
        id: 'grounding',
        title: 'Grounded answer',
        detail: 'Built the final answer from the available evidence in this turn.',
      },
    ])
  })
})
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_cors.py -q
docker compose run --rm frontend npm run test -- src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Expected: FAIL because the backend still passes a single origin into CORSMiddleware and the frontend trace types do not yet include contradiction-resolution data.

- [ ] **Step 3: Implement the CORS and contradiction-resolution changes**

Replace the CORS middleware block in `backend/src/hexarag_api/main.py` with:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hexarag_api.api.chat import router as chat_router
from hexarag_api.api.health import router as health_router
from hexarag_api.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origin_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
```

Update `frontend/src/types/chat.ts` to include contradiction resolution:

```ts
export interface ConflictResolution {
  chosenSource: string
  rationale: string
  competingSources: string[]
}

export interface TracePayload {
  citations: Citation[]
  inlineCitations: InlineCitationAnchor[]
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
  conflictResolution?: ConflictResolution
}

export interface TraceNarrativeStep {
  id: 'sources' | 'tools' | 'memory' | 'contradiction' | 'grounding' | 'uncertainty'
  title: string
  detail: string
}
```

Add this interface and mapping to `frontend/src/lib/api.ts`:

```ts
interface ApiConflictResolution {
  chosen_source: string
  rationale: string
  competing_sources: string[]
}

interface ApiTracePayload {
  citations: ApiCitation[]
  inline_citations?: ApiInlineCitationAnchor[]
  tool_calls: ApiToolCallTrace[]
  memory_window: string[]
  grounding_notes: string[]
  uncertainty: string | null
  conflict_resolution?: ApiConflictResolution | null
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
    conflictResolution: trace.conflict_resolution
      ? {
          chosenSource: trace.conflict_resolution.chosen_source,
          rationale: trace.conflict_resolution.rationale,
          competingSources: trace.conflict_resolution.competing_sources,
        }
      : undefined,
  }
}
```

Add the contradiction section to `frontend/src/features/trace/TracePanel.tsx` inside the observability branch, immediately after the `Grounding` section:

```tsx
            {trace.conflictResolution ? (
              <section className="trace-section">
                <h3>Conflict resolution</h3>
                <p>
                  <strong>Chosen source:</strong> {trace.conflictResolution.chosenSource}
                </p>
                <p>{trace.conflictResolution.rationale}</p>
                {trace.conflictResolution.competingSources.length > 0 ? (
                  <ul className="trace-list">
                    {trace.conflictResolution.competingSources.map((source, index) => (
                      <li key={`${source}-${index}`}>{source}</li>
                    ))}
                  </ul>
                ) : null}
              </section>
            ) : null}
```

Update `frontend/src/features/trace/buildTraceNarrative.ts` to add the contradiction step before grounding:

```ts
  if (trace.conflictResolution) {
    steps.push({
      id: 'contradiction',
      title: 'Resolved contradiction',
      detail: `Preferred ${trace.conflictResolution.chosenSource} because ${trace.conflictResolution.rationale}.`,
    })
  }
```

- [ ] **Step 4: Run the targeted tests to verify the new behavior passes**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_cors.py -q
docker compose run --rm frontend npm run test -- src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Expected: the new backend CORS test passes and the frontend contradiction-resolution tests pass.

- [ ] **Step 5: Commit the deploy-visible trace and CORS fixes**

```bash
git add backend/src/hexarag_api/main.py backend/tests/test_cors.py frontend/src/types/chat.ts frontend/src/lib/api.ts frontend/src/features/trace/TracePanel.tsx frontend/src/features/trace/buildTraceNarrative.ts frontend/src/features/trace/TracePanel.test.tsx frontend/src/features/trace/buildTraceNarrative.test.ts
git commit -m "feat: surface contradiction handling for deployed traces"
```

---

### Task 3: Add Lambda-safe entrypoints, canonical packaging, and Terraform deployment wiring

**Files:**
- Modify: `docker-compose.yml`
- Modify: `backend/scripts/sync_knowledge_base.py`
- Modify: `backend/src/monitoring_api/main.py`
- Create: `backend/src/hexarag_api/services/lambda_packaging.py`
- Create: `backend/scripts/package_lambda_artifacts.py`
- Modify: `infra/terraform/compute.tf`
- Modify: `infra/terraform/scheduler.tf`
- Modify: `infra/terraform/outputs.tf`
- Modify: `.gitignore`
- Modify: `backend/tests/monitoring_api/test_monitoring_routes.py`
- Create: `backend/tests/services/test_lambda_packaging.py`
- Create: `backend/tests/scripts/test_sync_knowledge_base.py`

- [ ] **Step 1: Write the failing Lambda wiring and packaging tests**

Create `backend/tests/services/test_lambda_packaging.py`:

```python
from pathlib import Path

from hexarag_api.services.lambda_packaging import build_artifact_specs


def test_build_artifact_specs_cover_all_three_lambda_zips() -> None:
    specs = build_artifact_specs(Path('/workspace/repo'))

    assert sorted(specs.keys()) == ['backend', 'kb_sync', 'monitoring']
    assert specs['backend'].output_path == Path('/workspace/repo/infra/terraform/backend.zip')
    assert specs['monitoring'].handler == 'monitoring_api.main.handler'
    assert specs['kb_sync'].handler == 'sync_knowledge_base.handler'
```

Create `backend/tests/scripts/test_sync_knowledge_base.py`:

```python
from scripts import sync_knowledge_base


def test_handler_starts_an_ingestion_job(monkeypatch) -> None:
    calls: dict[str, str] = {}

    class FakeClient:
        def start_ingestion_job(self, knowledgeBaseId: str, dataSourceId: str) -> None:
            calls['knowledge_base_id'] = knowledgeBaseId
            calls['data_source_id'] = dataSourceId

    class FakeBoto3:
        @staticmethod
        def client(service_name: str, region_name: str):
            assert service_name == 'bedrock-agent'
            assert region_name == 'us-east-1'
            return FakeClient()

    class FakeSettings:
        aws_region = 'us-east-1'
        knowledge_base_id = 'KB12345678'
        knowledge_base_data_source_id = 'DS12345678'

    monkeypatch.setattr(sync_knowledge_base, 'boto3', FakeBoto3)
    monkeypatch.setattr(sync_knowledge_base, 'Settings', FakeSettings)

    result = sync_knowledge_base.handler({}, None)

    assert result == {
        'status': 'started',
        'knowledge_base_id': 'KB12345678',
        'data_source_id': 'DS12345678',
    }
    assert calls == {
        'knowledge_base_id': 'KB12345678',
        'data_source_id': 'DS12345678',
    }
```

Add this test to `backend/tests/monitoring_api/test_monitoring_routes.py`:

```python
def test_monitoring_module_exposes_lambda_handler():
    from monitoring_api.main import handler

    assert handler is not None
```

- [ ] **Step 2: Run the Lambda and packaging tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/monitoring_api/test_monitoring_routes.py tests/services/test_lambda_packaging.py tests/scripts/test_sync_knowledge_base.py -q
```

Expected: FAIL because the monitoring module does not expose `handler`, the sync script handler does not exist, and the packaging helper is still missing.

- [ ] **Step 3: Implement the Lambda handlers, packaging helper, and packaging command**

Add the repo-root mount and packaging env to `docker-compose.yml`:

```yaml
  backend:
    build: ./backend
    working_dir: /app
    volumes:
      - ./backend:/app
      - ./W4:/workspace/W4:ro
      - ./:/workspace/repo
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://hexarag:hexarag@postgres:5432/hexarag
      MONITORING_BASE_URL: http://backend:8001
      W4_DATA_ROOT: /workspace/W4/data_package
      RUNTIME_MODE: stub
      HEXARAG_REPO_ROOT: /workspace/repo
```

Replace `backend/scripts/sync_knowledge_base.py` with:

```python
import argparse

import boto3

from hexarag_api.config import Settings


def run_sync() -> dict[str, str]:
    settings = Settings()
    client = boto3.client('bedrock-agent', region_name=settings.aws_region)
    client.start_ingestion_job(
        knowledgeBaseId=settings.knowledge_base_id,
        dataSourceId=settings.knowledge_base_data_source_id,
    )
    return {
        'status': 'started',
        'knowledge_base_id': settings.knowledge_base_id,
        'data_source_id': settings.knowledge_base_data_source_id,
    }


def handler(event, context):
    return run_sync()


def main() -> None:
    parser = argparse.ArgumentParser(description='Trigger a Bedrock knowledge base ingestion job.')
    parser.parse_args()
    run_sync()


if __name__ == '__main__':
    main()
```

Replace `backend/src/monitoring_api/main.py` with:

```python
from fastapi import FastAPI, HTTPException
from mangum import Mangum

from monitoring_api.data import BASE_METRICS

app = FastAPI(title='HexaRAG Monitoring API')


@app.get('/services')
def list_services() -> dict[str, list[str]]:
    return {'services': sorted(BASE_METRICS.keys())}


@app.get('/metrics/{service_name}')
def get_metrics(service_name: str) -> dict[str, int | float]:
    if service_name not in BASE_METRICS:
        raise HTTPException(status_code=404, detail='Unknown service')

    return BASE_METRICS[service_name]


handler = Mangum(app)
```

Create `backend/src/hexarag_api/services/lambda_packaging.py`:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LambdaArtifactSpec:
    name: str
    handler: str
    output_path: Path
    package_dirs: tuple[Path, ...]
    root_files: tuple[Path, ...]
    dependency_globs: tuple[str, ...]


COMMON_WEB_DEPENDENCIES = (
    'annotated_types*',
    'anyio*',
    'boto3*',
    'botocore*',
    'certifi*',
    'dateutil*',
    'fastapi*',
    'h11*',
    'httpcore*',
    'httpx*',
    'idna*',
    'jmespath*',
    'mangum*',
    'psycopg*',
    'pydantic*',
    'pydantic_core*',
    'pydantic_settings*',
    'python_dotenv*',
    's3transfer*',
    'sniffio*',
    'starlette*',
    'typing_extensions*',
    'typing_inspection*',
    'urllib3*',
    'six*',
)

SYNC_ONLY_DEPENDENCIES = (
    'boto3*',
    'botocore*',
    'dateutil*',
    'jmespath*',
    'pydantic*',
    'pydantic_core*',
    'pydantic_settings*',
    'python_dotenv*',
    's3transfer*',
    'typing_extensions*',
    'typing_inspection*',
    'urllib3*',
    'six*',
)


def build_artifact_specs(repo_root: Path) -> dict[str, LambdaArtifactSpec]:
    backend_root = repo_root / 'backend'
    terraform_root = repo_root / 'infra' / 'terraform'

    return {
        'backend': LambdaArtifactSpec(
            name='backend',
            handler='hexarag_api.handler.handler',
            output_path=terraform_root / 'backend.zip',
            package_dirs=(backend_root / 'src' / 'hexarag_api',),
            root_files=(),
            dependency_globs=COMMON_WEB_DEPENDENCIES,
        ),
        'monitoring': LambdaArtifactSpec(
            name='monitoring',
            handler='monitoring_api.main.handler',
            output_path=terraform_root / 'monitoring.zip',
            package_dirs=(backend_root / 'src' / 'monitoring_api',),
            root_files=(),
            dependency_globs=COMMON_WEB_DEPENDENCIES,
        ),
        'kb_sync': LambdaArtifactSpec(
            name='kb_sync',
            handler='sync_knowledge_base.handler',
            output_path=terraform_root / 'kb-sync.zip',
            package_dirs=(backend_root / 'src' / 'hexarag_api',),
            root_files=(backend_root / 'scripts' / 'sync_knowledge_base.py',),
            dependency_globs=SYNC_ONLY_DEPENDENCIES,
        ),
    }
```

Create `backend/scripts/package_lambda_artifacts.py`:

```python
import os
import shutil
import sysconfig
import zipfile
from pathlib import Path

from hexarag_api.services.lambda_packaging import build_artifact_specs


def _copy_dependency_matches(site_packages: Path, staging_root: Path, patterns: tuple[str, ...]) -> None:
    copied: set[Path] = set()
    for pattern in patterns:
        for match in site_packages.glob(pattern):
            if match in copied or not match.exists():
                continue
            destination = staging_root / match.name
            if match.is_dir():
                shutil.copytree(match, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(match, destination)
            copied.add(match)


def _write_zip(staging_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(staging_root.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(staging_root))


def package_artifacts() -> list[Path]:
    repo_root = Path(os.environ.get('HEXARAG_REPO_ROOT', '/workspace/repo')).resolve()
    site_packages = Path(sysconfig.get_paths()['purelib'])
    build_root = repo_root / '.lambda-build'
    specs = build_artifact_specs(repo_root)
    outputs: list[Path] = []

    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True, exist_ok=True)

    for spec in specs.values():
        staging_root = build_root / spec.name
        staging_root.mkdir(parents=True, exist_ok=True)

        for package_dir in spec.package_dirs:
            shutil.copytree(package_dir, staging_root / package_dir.name, dirs_exist_ok=True)
        for root_file in spec.root_files:
            shutil.copy2(root_file, staging_root / root_file.name)
        _copy_dependency_matches(site_packages, staging_root, spec.dependency_globs)
        _write_zip(staging_root, spec.output_path)
        outputs.append(spec.output_path)

    return outputs


if __name__ == '__main__':
    for output in package_artifacts():
        print(output)
```

- [ ] **Step 4: Wire Terraform and git ignore to the new packaging/output model**

Update the backend Lambda block in `infra/terraform/compute.tf` to:

```hcl
resource "aws_lambda_function" "backend" {
  function_name    = "${local.name_prefix}-backend"
  role             = aws_iam_role.backend_lambda.arn
  runtime          = "python3.12"
  handler          = "hexarag_api.handler.handler"
  filename         = "backend.zip"
  source_code_hash = filebase64sha256("backend.zip")
  timeout          = 30

  environment {
    variables = {
      RUNTIME_MODE                  = "aws"
      ALLOWED_ORIGINS               = join(",", ["http://localhost:5173", "https://${aws_cloudfront_distribution.frontend.domain_name}"])
      AWS_REGION                    = var.aws_region
      DATABASE_URL                  = "postgresql://hexarag:${var.database_password}@${aws_db_instance.postgres.address}:5432/hexarag"
      SESSION_TABLE_NAME            = aws_dynamodb_table.sessions.name
      MONITORING_BASE_URL           = aws_apigatewayv2_stage.monitoring.invoke_url
      KNOWLEDGE_BASE_ID             = var.knowledge_base_id
      KNOWLEDGE_BASE_DATA_SOURCE_ID = var.knowledge_base_data_source_id
      AGENT_RUNTIME_ARN             = var.agent_runtime_arn
    }
  }
}
```

Update the monitoring Lambda block in the same file to:

```hcl
resource "aws_lambda_function" "monitoring" {
  function_name    = "${local.name_prefix}-monitoring"
  role             = aws_iam_role.monitoring_lambda.arn
  runtime          = "python3.12"
  handler          = "monitoring_api.main.handler"
  filename         = "monitoring.zip"
  source_code_hash = filebase64sha256("monitoring.zip")
  timeout          = 15
}
```

Update `infra/terraform/scheduler.tf` to:

```hcl
resource "aws_lambda_function" "kb_sync" {
  function_name    = "${local.name_prefix}-kb-sync"
  role             = aws_iam_role.sync_lambda.arn
  runtime          = "python3.12"
  handler          = "sync_knowledge_base.handler"
  filename         = "kb-sync.zip"
  source_code_hash = filebase64sha256("kb-sync.zip")
  timeout          = 60

  environment {
    variables = {
      AWS_REGION                    = var.aws_region
      KNOWLEDGE_BASE_ID             = var.knowledge_base_id
      KNOWLEDGE_BASE_DATA_SOURCE_ID = var.knowledge_base_data_source_id
    }
  }
}
```

Append these outputs to `infra/terraform/outputs.tf`:

```hcl
output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}
```

Append this line to `.gitignore`:

```gitignore
infra/terraform/*.zip
```

- [ ] **Step 5: Run the Lambda/packaging tests, build the zips, and validate Terraform**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/monitoring_api/test_monitoring_routes.py tests/services/test_lambda_packaging.py tests/scripts/test_sync_knowledge_base.py -q
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

Expected:
- the selected backend tests pass
- the packaging script prints three zip paths under `infra/terraform`
- Terraform formatting and validation succeed

- [ ] **Step 6: Commit the packaging and Terraform wiring changes**

```bash
git add docker-compose.yml backend/scripts/sync_knowledge_base.py backend/src/monitoring_api/main.py backend/src/hexarag_api/services/lambda_packaging.py backend/scripts/package_lambda_artifacts.py infra/terraform/compute.tf infra/terraform/scheduler.tf infra/terraform/outputs.tf .gitignore backend/tests/monitoring_api/test_monitoring_routes.py backend/tests/services/test_lambda_packaging.py backend/tests/scripts/test_sync_knowledge_base.py
git commit -m "build: add lambda packaging flow for aws deploy"
```

---

### Task 4: Update the deployment docs, functionality tracker, and local-dev guide

**Files:**
- Modify: `docs/aws.md`
- Modify: `docs/app-functionality.md`
- Modify: `docs/local-dev.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Rewrite the packaging section in `docs/aws.md` around the canonical command**

Replace the current Step 7 / Step 8 packaging guidance with:

```md
## Step 7: Package the Lambda artifacts
**Run locally yourself**
**Verify manually**

Use the repo-owned packaging command from the repo root:

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
```

Expected result: the command prints three artifact paths and creates these files in `infra/terraform`:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

Verify the files exist before continuing:

```powershell
Get-ChildItem .\infra\terraform\*.zip
```
```

Replace the CloudFront output caveat with:

```md
### Frontend and CloudFront outputs
Terraform now exposes both:
- `cloudfront_domain_name`
- `cloudfront_distribution_id`

Use those outputs for browser verification and cache invalidation after uploading frontend assets.
```

- [ ] **Step 2: Update the app-functionality tracker rows that changed**

Replace the contradiction-handling row in `docs/app-functionality.md` with:

```md
| Grounding | Contradiction handling visibility | Multi-source conflicts should be surfaced and explained, including why one source was trusted. | Answer text and inspection console | Retrieval logic and trace shaping | partial | The trace contract and inspection console can now surface explicit conflict-resolution details when the backend provides `conflict_resolution`. | Live correctness still depends on the deployed runtime consistently populating contradiction metadata. | contradiction resolution policy | L2 requirement |
```

Replace the deployed CORS row with:

```md
| Deployment | Deployed frontend/browser CORS compatibility | Browser requests from the deployed frontend should be accepted by the backend API. | Browser chat requests | Backend allowed origin configuration | working | Backend settings now parse multiple allowed origins and Terraform supplies the CloudFront domain to the deployed Lambda. | Additional custom domains would still need to be added to the configured origin list. | n/a | Deployment-critical |
```

Replace the output-discoverability row with:

```md
| Deployment | AWS output discoverability for operators | Operators should be able to find the deployed endpoints and buckets without guesswork. | Deployment docs and Terraform outputs | `infra/terraform/outputs.tf` | working | Terraform outputs expose backend API URL, monitoring API URL, frontend bucket name, knowledge-base bucket name, CloudFront domain, CloudFront distribution ID, session table name, and PostgreSQL endpoint. | Bedrock resource IDs remain external inputs rather than Terraform-managed outputs in this repo. | n/a | Ops usability |
```

- [ ] **Step 3: Add the packaging and readiness commands to `docs/local-dev.md` and index the new plan in `TASKS.md`**

Append this subsection to `docs/local-dev.md` after the Phase 3 verification commands:

```md
## Deploy-readiness verification
- `docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_chat_service.py tests/services/test_session_store.py tests/test_cors.py tests/services/test_lambda_packaging.py tests/scripts/test_sync_knowledge_base.py tests/monitoring_api/test_monitoring_routes.py -q`
- `docker compose run --rm frontend npm run test -- src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run`
- `docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py`
- from `infra/terraform`: `terraform fmt -check`
- from `infra/terraform`: `terraform validate`
```

Add this line to the Plan Index in `TASKS.md`:

```md
- `docs/superpowers/plans/2026-05-08-aws-deploy-readiness-and-deployment.md` — runtime truthfulness, packaging automation, deployment wiring, and live AWS rollout
```

- [ ] **Step 4: Verify the docs against the code paths you just changed**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
docker compose run --rm frontend npm run build
```

Expected: the packaging command succeeds, Terraform still validates, and the frontend build still succeeds with the updated docs describing the correct workflow.

- [ ] **Step 5: Commit the doc and tracker updates**

```bash
git add docs/aws.md docs/app-functionality.md docs/local-dev.md TASKS.md
git commit -m "docs: align aws deployment guidance with live wiring"
```

---

### Task 5: Run the full local deploy-readiness verification suite

**Files:**
- Modify: none

- [ ] **Step 1: Run the backend verification commands**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_chat_service.py tests/services/test_session_store.py tests/services/test_trace_formatter.py tests/test_cors.py tests/services/test_lambda_packaging.py tests/scripts/test_sync_knowledge_base.py tests/monitoring_api/test_monitoring_routes.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run the frontend verification commands**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
docker compose run --rm frontend npm run build
```

Expected: the targeted frontend tests pass and the production build succeeds.

- [ ] **Step 3: Rebuild the Lambda zips and validate Terraform one more time**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

Expected: the three zips are recreated successfully and Terraform reports no formatting or validation errors.

- [ ] **Step 4: Do not create a commit in this task**

This task is verification-only. Leave the git history unchanged unless you discover a real defect that requires another code or doc fix.

---

### Task 6: Deploy the prepared repo to AWS and verify the live stack

**Files:**
- Modify: `infra/terraform/terraform.tfvars` (local untracked deployment input)

- [ ] **Step 1: Verify AWS identity, region, and the three Bedrock prerequisites**

Run from `hexarag`:

```powershell
aws sts get-caller-identity
aws configure get region
aws bedrock-agent list-knowledge-bases --region us-east-1
aws bedrock-agentcore-control list-agent-runtimes --region us-east-1
```

Expected:
- the caller identity matches the intended AWS account
- the region is `us-east-1`
- you can see the knowledge base and AgentCore runtime you intend to use

After selecting the knowledge base ID from the list output, run:

```powershell
$KnowledgeBaseId = '<selected-knowledge-base-id>'
aws bedrock-agent list-data-sources --knowledge-base-id $KnowledgeBaseId --region us-east-1
```

Expected: the intended data source appears in the list output. If any of the three Bedrock prerequisites do not exist yet, complete the creation flow in the updated `docs/aws.md` before continuing.

- [ ] **Step 2: Materialize `terraform.tfvars` from the selected deployment inputs**

Run from `hexarag`:

```powershell
Copy-Item infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars -Force
@"
aws_region                    = "us-east-1"
project_name                  = "hexarag"
environment                   = "dev"
database_password             = "replace-with-a-real-password"
agent_runtime_arn             = "<selected-agent-runtime-arn>"
knowledge_base_id             = "$KnowledgeBaseId"
knowledge_base_data_source_id = "<selected-data-source-id>"
"@ | Set-Content infra/terraform/terraform.tfvars
```

Expected: `infra/terraform/terraform.tfvars` exists with the intended region, project name, environment, password, runtime ARN, knowledge base ID, and data source ID.

- [ ] **Step 3: Package artifacts, apply Terraform, and capture the outputs**

Run from `hexarag`:

```powershell
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform apply
$BackendApiUrl = terraform -chdir=infra/terraform output -raw backend_api_url
$MonitoringApiUrl = terraform -chdir=infra/terraform output -raw monitoring_api_url
$FrontendBucket = terraform -chdir=infra/terraform output -raw frontend_bucket_name
$KnowledgeBaseBucket = terraform -chdir=infra/terraform output -raw knowledge_base_bucket_name
$CloudFrontDomain = terraform -chdir=infra/terraform output -raw cloudfront_domain_name
$CloudFrontDistributionId = terraform -chdir=infra/terraform output -raw cloudfront_distribution_id
```

Expected: Terraform applies successfully and all six output variables are populated.

- [ ] **Step 4: Build and publish the frontend with the deployed backend URL**

Run from `hexarag`:

```powershell
$env:VITE_API_BASE_URL = $BackendApiUrl
docker compose run --rm frontend npm run build
Remove-Item Env:VITE_API_BASE_URL
aws s3 sync frontend/dist "s3://$FrontendBucket" --delete
aws cloudfront create-invalidation --distribution-id $CloudFrontDistributionId --paths '/*'
```

Expected: the frontend build succeeds, the S3 sync uploads the static assets, and CloudFront starts an invalidation.

- [ ] **Step 5: Upload the knowledge-base markdown files and trigger ingestion**

Run from `hexarag`:

```powershell
docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket $KnowledgeBaseBucket
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py
aws bedrock-agent start-ingestion-job --knowledge-base-id $KnowledgeBaseId --data-source-id '<selected-data-source-id>' --region us-east-1
```

Expected: the knowledge-base files upload to S3 and the ingestion job starts. Use the AWS Console or the CLI to confirm the ingestion job completes successfully before trusting retrieval behavior.

- [ ] **Step 6: Verify backend, monitoring, and browser behavior end to end**

Run from `hexarag`:

```powershell
Invoke-RestMethod -Method Post -Uri "$BackendApiUrl/chat" -ContentType 'application/json' -Body '{"session_id":"deploy-check","message":"What changed in EC2 cost last month?"}'
Invoke-RestMethod -Method Get -Uri "$MonitoringApiUrl/services"
Start-Process "https://$CloudFrontDomain"
```

Expected:
- the backend `/chat` route returns a real trace-shaped response instead of the permanently stubbed path
- the monitoring API returns the service list
- the CloudFront frontend loads in the browser and uses the deployed backend instead of `localhost`

---

## Self-Review
- **Spec coverage:** Task 1 covers runtime truthfulness and session-store selection. Task 2 covers trace-contract alignment and deployed-origin handling. Task 3 covers Lambda entrypoints, packaging automation, Terraform outputs, and deploy wiring. Task 4 covers doc/tracker truthfulness. Task 5 covers local verification. Task 6 covers the actual AWS deployment and live verification.
- **Placeholder scan:** No `TODO`, `TBD`, or “figure this out later” steps remain. The only angle-bracket substitutions are account-specific AWS values gathered in Task 6 immediately before use.
- **Type consistency:** Backend keeps snake_case in the API contract; frontend continues to centralize snake_case-to-camelCase mapping in `frontend/src/lib/api.ts`. The new contradiction field is `conflict_resolution` on the backend and `conflictResolution` on the frontend.

## Execution Handoff
Plan complete and saved to `docs/superpowers/plans/2026-05-08-aws-deploy-readiness-and-deployment.md`.

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
