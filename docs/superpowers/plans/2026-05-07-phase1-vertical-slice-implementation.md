# Phase 1 Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved Phase 1 vertical slice: a stubbed FastAPI `/chat` contract and a single-turn frontend form that renders the latest result plus the always-visible observability panel.

**Architecture:** Replace the backend scaffold's placeholder `backend` package with a real `hexarag_api` package, expose `GET /health` and `POST /chat`, and return deterministic stub data that exercises the UI contract. On the frontend, keep the two-pane shell, centralize snake_case-to-camelCase mapping in `frontend/src/lib/api.ts`, and drive the latest-result panel plus trace/error rendering through a focused `useChatSession` hook.

**Tech Stack:** Docker Compose, FastAPI, Pydantic, pydantic-settings, Mangum, React, TypeScript, Vitest, React Testing Library.

---

## Planned File Responsibilities

### Backend
- Modify: `backend/pyproject.toml` — remove the stale default CLI script and keep package metadata aligned with the new `hexarag_api` package.
- Delete: `backend/src/backend/__init__.py` — remove the `uv init` placeholder package once `hexarag_api` exists.
- Create: `backend/src/hexarag_api/config.py` — minimal app settings for API name and allowed origin.
- Create: `backend/src/hexarag_api/models/chat.py` — request, response, trace, and error models in backend snake_case.
- Create: `backend/src/hexarag_api/api/health.py` — `GET /health` readiness route.
- Create: `backend/src/hexarag_api/api/chat.py` — `POST /chat` stub success and stub failure contract.
- Create: `backend/src/hexarag_api/main.py` — FastAPI app factory and router wiring.
- Create: `backend/src/hexarag_api/handler.py` — Mangum Lambda entrypoint.
- Create: `backend/tests/test_health.py` — health endpoint contract test.
- Create: `backend/tests/api/test_chat_contract.py` — chat success and failure contract tests.

### Frontend
- Modify: `frontend/src/types/chat.ts` — internal camelCase app types for success trace and error state.
- Create: `frontend/src/lib/api.ts` — fetch client plus API-shape-to-app-shape mapping.
- Create: `frontend/src/features/chat/useChatSession.ts` — single-turn request state, latest-result state, and error state.
- Modify: `frontend/src/features/chat/ChatPage.tsx` — form, inline error, latest-result panel, and trace wiring.
- Modify: `frontend/src/features/trace/TracePanel.tsx` — success trace sections and failed-request details.
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — idle, success, and failure UI tests.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — empty, success, and error observability tests.
- Modify: `frontend/src/styles.css` — latest-result, error-state, and disabled-button styling.

### Tracking and Docs
- Modify: `TASKS.md` — mark the backend skeleton and frontend hookup tasks complete after implementation.
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` — note that the approved slice now uses `/chat` and a latest-result panel rather than transcript UI.
- Modify: `docs/local-dev.md` — add the targeted backend and frontend verification commands for this slice.

---

### Task 1: Replace the backend scaffold with the stubbed FastAPI contract

**Files:**
- Modify: `backend/pyproject.toml`
- Delete: `backend/src/backend/__init__.py`
- Create: `backend/src/hexarag_api/config.py`
- Create: `backend/src/hexarag_api/models/chat.py`
- Create: `backend/src/hexarag_api/api/health.py`
- Create: `backend/src/hexarag_api/api/chat.py`
- Create: `backend/src/hexarag_api/main.py`
- Create: `backend/src/hexarag_api/handler.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/api/test_chat_contract.py`

- [ ] **Step 1: Write the failing backend contract tests**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from hexarag_api.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

Create `backend/tests/api/test_chat_contract.py`:

```python
from fastapi.testclient import TestClient

from hexarag_api.main import app

client = TestClient(app)


def test_chat_returns_stubbed_message_and_trace() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 'phase1-session',
            'message': 'What is PaymentGW latency?',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'session_id': 'phase1-session',
        'message': {
            'role': 'assistant',
            'content': 'Stub answer for: What is PaymentGW latency?',
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-architecture',
                        'title': 'architecture.md',
                        'excerpt': 'Current p95 latency sits below the alert threshold.',
                        'version': None,
                        'recency_note': 'Stubbed knowledge base note.',
                    }
                ],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'success',
                        'summary': 'Prepared stub observability data',
                        'input': {'question': 'What is PaymentGW latency?'},
                        'output': {'mode': 'stub', 'latency_p95_ms': 185},
                    }
                ],
                'memory_window': ['No prior turns in Phase 1 single-turn mode.'],
                'grounding_notes': ['This is a deterministic stub response for the Phase 1 vertical slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        },
    }


def test_chat_returns_structured_error_details_for_failure_mode() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 'phase1-session',
            'message': 'trigger failure',
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        'error': 'Unable to generate stub response.',
        'trace': {
            'request': {
                'session_id': 'phase1-session',
                'message': 'trigger failure',
            },
            'details': ['Stub failure requested for UI error-state coverage.'],
        },
    }
```

- [ ] **Step 2: Run the backend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'hexarag_api'` because the placeholder backend package is still the default `backend/src/backend` scaffold.

- [ ] **Step 3: Replace the scaffold with the minimal FastAPI implementation**

Replace `backend/pyproject.toml` with:

```toml
[project]
name = "hexarag-api"
version = "0.1.0"
description = "HexaRAG FastAPI backend"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.43.4",
    "fastapi>=0.136.1",
    "httpx>=0.28.1",
    "mangum>=0.21.0",
    "psycopg[binary]>=3.3.4",
    "pydantic-settings>=2.14.0",
    "python-dotenv>=1.2.2",
]

[build-system]
requires = ["uv_build>=0.9.30,<0.10.0"]
build-backend = "uv_build"

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.15.12",
]
```

Delete `backend/src/backend/__init__.py`.

Create `backend/src/hexarag_api/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'HexaRAG API'
    allowed_origin: str = 'http://localhost:5173'


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `backend/src/hexarag_api/models/chat.py`:

```python
from typing import Any, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    version: str | None = None
    recency_note: str | None = None


class ToolCallTrace(BaseModel):
    name: str
    status: Literal['success', 'error']
    summary: str
    input: dict[str, Any]
    output: dict[str, Any] | None


class TracePayload(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    memory_window: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)
    uncertainty: str | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatMessage(BaseModel):
    role: Literal['assistant']
    content: str
    trace: TracePayload


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage


class ErrorTrace(BaseModel):
    request: dict[str, str]
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str
    trace: ErrorTrace
```

Create `backend/src/hexarag_api/api/health.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}
```

Create `backend/src/hexarag_api/api/chat.py`:

```python
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from hexarag_api.models.chat import (
    Citation,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ErrorTrace,
    ToolCallTrace,
    TracePayload,
)

router = APIRouter()


@router.post('/chat', response_model=ChatResponse, responses={502: {'model': ErrorResponse}})
async def post_chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    if request.message.casefold() == 'trigger failure':
        error_payload = ErrorResponse(
            error='Unable to generate stub response.',
            trace=ErrorTrace(
                request={
                    'session_id': request.session_id,
                    'message': request.message,
                },
                details=['Stub failure requested for UI error-state coverage.'],
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=error_payload.model_dump(),
        )

    return ChatResponse(
        session_id=request.session_id,
        message=ChatMessage(
            role='assistant',
            content=f'Stub answer for: {request.message}',
            trace=TracePayload(
                citations=[
                    Citation(
                        source_id='doc-architecture',
                        title='architecture.md',
                        excerpt='Current p95 latency sits below the alert threshold.',
                        recency_note='Stubbed knowledge base note.',
                    )
                ],
                tool_calls=[
                    ToolCallTrace(
                        name='monitoring_snapshot',
                        status='success',
                        summary='Prepared stub observability data',
                        input={'question': request.message},
                        output={'mode': 'stub', 'latency_p95_ms': 185},
                    )
                ],
                memory_window=['No prior turns in Phase 1 single-turn mode.'],
                grounding_notes=['This is a deterministic stub response for the Phase 1 vertical slice.'],
                uncertainty='Live systems are not wired in this slice.',
            ),
        ),
    )
```

Create `backend/src/hexarag_api/main.py`:

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
        allow_origins=[settings.allowed_origin],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
```

Create `backend/src/hexarag_api/handler.py`:

```python
from mangum import Mangum

from hexarag_api.main import app

handler = Mangum(app)
```

- [ ] **Step 4: Fix the import typo in the chat route before rerunning tests**

Update the import block in `backend/src/hexarag_api/api/chat.py` to use `Citation`, not `कैitation`:

```python
from hexarag_api.models.chat import (
    Citation,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ErrorTrace,
    ToolCallTrace,
    TracePayload,
)
```

- [ ] **Step 5: Run the backend tests to verify the contract passes**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q
```

Expected: `3 passed`.

- [ ] **Step 6: Commit the backend slice**

```bash
git add backend/pyproject.toml backend/src/hexarag_api backend/tests backend/src/backend/__init__.py
git commit -m "feat: add stubbed fastapi chat contract"
```

---

### Task 2: Wire the frontend form to the backend and render success plus failure states

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/features/chat/useChatSession.ts`
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/trace/TracePanel.tsx`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write the failing frontend tests for idle, success, and failure behavior**

Replace `frontend/src/features/chat/ChatPage.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ChatPage } from './ChatPage'

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('ChatPage', () => {
  it('renders the single-turn form with empty latest-result and observability states', () => {
    render(<ChatPage />)

    expect(screen.getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Latest result' })).toBeInTheDocument()
    expect(screen.getByText('Send one question to inspect the stubbed backend response.')).toBeInTheDocument()
    expect(screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.')).toBeInTheDocument()
  })

  it('submits a question and renders the assistant reply plus observability data', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'phase1-session',
        message: {
          role: 'assistant',
          content: 'Stub answer for: What is PaymentGW current latency?',
          trace: {
            citations: [
              {
                source_id: 'doc-architecture',
                title: 'architecture.md',
                excerpt: 'Current p95 latency sits below the alert threshold.',
                version: null,
                recency_note: 'Stubbed knowledge base note.',
              },
            ],
            tool_calls: [
              {
                name: 'monitoring_snapshot',
                status: 'success',
                summary: 'Prepared stub observability data',
                input: { question: 'What is PaymentGW current latency?' },
                output: { mode: 'stub', latency_p95_ms: 185 },
              },
            ],
            memory_window: ['No prior turns in Phase 1 single-turn mode.'],
            grounding_notes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
            uncertainty: 'Live systems are not wired in this slice.',
          },
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'What is PaymentGW current latency?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('Stub answer for: What is PaymentGW current latency?')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/chat',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('renders inline error, latest-result error state, and observability error details', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({
        error: 'Unable to generate stub response.',
        trace: {
          request: {
            session_id: 'phase1-session',
            message: 'trigger failure',
          },
          details: ['Stub failure requested for UI error-state coverage.'],
        },
      }),
    } as Response)

    const user = userEvent.setup()
    render(<ChatPage />)

    await user.type(screen.getByPlaceholderText('Ask GeekBrain anything...'), 'trigger failure')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate stub response.')
    expect(screen.getByText('Request failed')).toBeInTheDocument()
    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
```

Replace `frontend/src/features/trace/TracePanel.test.tsx` with:

```tsx
import { render, screen } from '@testing-library/react'

import { TracePanel } from './TracePanel'

describe('TracePanel', () => {
  it('shows empty-state guidance before the first answer', () => {
    render(<TracePanel trace={null} error={null} />)

    expect(
      screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.'),
    ).toBeInTheDocument()
  })

  it('renders successful trace sections', () => {
    render(
      <TracePanel
        trace={{
          citations: [
            {
              sourceId: 'doc-architecture',
              title: 'architecture.md',
              excerpt: 'Current p95 latency sits below the alert threshold.',
              version: undefined,
              recencyNote: 'Stubbed knowledge base note.',
            },
          ],
          toolCalls: [
            {
              name: 'monitoring_snapshot',
              status: 'success',
              summary: 'Prepared stub observability data',
              input: { question: 'What is PaymentGW latency?' },
              output: { mode: 'stub', latency_p95_ms: 185 },
            },
          ],
          memoryWindow: ['No prior turns in Phase 1 single-turn mode.'],
          groundingNotes: ['This is a deterministic stub response for the Phase 1 vertical slice.'],
          uncertainty: 'Live systems are not wired in this slice.',
        }}
        error={null}
      />,
    )

    expect(screen.getByText('architecture.md')).toBeInTheDocument()
    expect(screen.getByText('monitoring_snapshot: Prepared stub observability data')).toBeInTheDocument()
    expect(screen.getByText('No prior turns in Phase 1 single-turn mode.')).toBeInTheDocument()
    expect(screen.getByText('Live systems are not wired in this slice.')).toBeInTheDocument()
  })

  it('renders failed-request details when the API call fails', () => {
    render(
      <TracePanel
        trace={null}
        error={{
          message: 'Unable to generate stub response.',
          request: {
            sessionId: 'phase1-session',
            message: 'trigger failure',
          },
          details: ['Stub failure requested for UI error-state coverage.'],
        }}
      />,
    )

    expect(screen.getByText('Last request')).toBeInTheDocument()
    expect(screen.getByText('phase1-session')).toBeInTheDocument()
    expect(screen.getByText('trigger failure')).toBeInTheDocument()
    expect(screen.getByText('Stub failure requested for UI error-state coverage.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the frontend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: FAIL because `ChatPage` still renders the transcript placeholder, `TracePanel` does not accept an `error` prop, and there is no fetch-backed state or API mapping yet.

- [ ] **Step 3: Implement the shared chat types and centralized API mapper**

Replace `frontend/src/types/chat.ts` with:

```ts
export interface Citation {
  sourceId: string
  title: string
  excerpt: string
  version?: string
  recencyNote?: string
}

export interface ToolCallTrace {
  name: string
  status: 'success' | 'error'
  summary: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
}

export interface TracePayload {
  citations: Citation[]
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty: string | null
}

export interface ChatMessage {
  role: 'assistant'
  content: string
  trace: TracePayload
}

export interface ChatResponse {
  sessionId: string
  message: ChatMessage
}

export interface ChatErrorState {
  message: string
  request: {
    sessionId: string
    message: string
  }
  details: string[]
}
```

Create `frontend/src/lib/api.ts`:

```ts
import type { ChatErrorState, ChatResponse, TracePayload } from '../types/chat'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface ApiCitation {
  source_id: string
  title: string
  excerpt: string
  version: string | null
  recency_note: string | null
}

interface ApiToolCallTrace {
  name: string
  status: 'success' | 'error'
  summary: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
}

interface ApiTracePayload {
  citations: ApiCitation[]
  tool_calls: ApiToolCallTrace[]
  memory_window: string[]
  grounding_notes: string[]
  uncertainty: string | null
}

interface ApiChatResponse {
  session_id: string
  message: {
    role: 'assistant'
    content: string
    trace: ApiTracePayload
  }
}

interface ApiChatErrorResponse {
  error: string
  trace: {
    request: {
      session_id: string
      message: string
    }
    details: string[]
  }
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
    toolCalls: trace.tool_calls,
    memoryWindow: trace.memory_window,
    groundingNotes: trace.grounding_notes,
    uncertainty: trace.uncertainty,
  }
}

function mapError(payload: ApiChatErrorResponse): ChatErrorState {
  return {
    message: payload.error,
    request: {
      sessionId: payload.trace.request.session_id,
      message: payload.trace.request.message,
    },
    details: payload.trace.details,
  }
}

export async function postChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
  })

  const payload = (await response.json()) as ApiChatResponse | ApiChatErrorResponse

  if (!response.ok) {
    throw mapError(payload as ApiChatErrorResponse)
  }

  const successPayload = payload as ApiChatResponse

  return {
    sessionId: successPayload.session_id,
    message: {
      role: successPayload.message.role,
      content: successPayload.message.content,
      trace: mapTrace(successPayload.message.trace),
    },
  }
}
```

- [ ] **Step 4: Implement the single-turn hook and UI state transitions**

Create `frontend/src/features/chat/useChatSession.ts`:

```ts
import { useState } from 'react'

import { postChatMessage } from '../../lib/api'
import type { ChatErrorState, ChatMessage, TracePayload } from '../../types/chat'

const SESSION_ID = 'phase1-session'

interface ChatSessionState {
  prompt: string
  latestMessage: ChatMessage | null
  trace: TracePayload | null
  error: ChatErrorState | null
  inlineError: string | null
  isSubmitting: boolean
  canSubmit: boolean
  setPrompt: (value: string) => void
  submitPrompt: () => Promise<void>
}

export function useChatSession(): ChatSessionState {
  const [prompt, setPrompt] = useState('')
  const [latestMessage, setLatestMessage] = useState<ChatMessage | null>(null)
  const [trace, setTrace] = useState<TracePayload | null>(null)
  const [error, setError] = useState<ChatErrorState | null>(null)
  const [inlineError, setInlineError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const canSubmit = !isSubmitting && prompt.trim().length > 0

  const submitPrompt = async () => {
    if (!canSubmit) {
      return
    }

    setIsSubmitting(true)
    setInlineError(null)
    setError(null)

    try {
      const response = await postChatMessage(SESSION_ID, prompt.trim())
      setLatestMessage(response.message)
      setTrace(response.message.trace)
    } catch (requestError) {
      const mappedError = requestError as ChatErrorState
      setLatestMessage(null)
      setTrace(null)
      setError(mappedError)
      setInlineError(mappedError.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return {
    prompt,
    latestMessage,
    trace,
    error,
    inlineError,
    isSubmitting,
    canSubmit,
    setPrompt,
    submitPrompt,
  }
}
```

Replace `frontend/src/features/chat/ChatPage.tsx` with:

```tsx
import type { FormEvent } from 'react'

import { TracePanel } from '../trace/TracePanel'
import { useChatSession } from './useChatSession'

export function ChatPage() {
  const {
    prompt,
    latestMessage,
    trace,
    error,
    inlineError,
    isSubmitting,
    canSubmit,
    setPrompt,
    submitPrompt,
  } = useChatSession()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await submitPrompt()
  }

  return (
    <main className="app-shell">
      <section className="chat-pane">
        <header className="chat-header">
          <h1>HexaRAG</h1>
          <p>Ask GeekBrain anything.</p>
        </header>

        <form className="composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="chat-message">
            Question
          </label>
          <textarea
            id="chat-message"
            placeholder="Ask GeekBrain anything..."
            rows={3}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
          />
          {inlineError ? (
            <p className="form-error" role="alert">
              {inlineError}
            </p>
          ) : null}
          <button type="submit" disabled={!canSubmit}>
            {isSubmitting ? 'Sending...' : 'Send'}
          </button>
        </form>

        <section className="latest-result" aria-live="polite">
          <h2>Latest result</h2>
          {latestMessage ? (
            <article className="result-card">
              <h3>Assistant</h3>
              <p>{latestMessage.content}</p>
            </article>
          ) : error ? (
            <article className="result-card result-card--error">
              <h3>Request failed</h3>
              <p>{error.message}</p>
            </article>
          ) : (
            <p className="result-empty">Send one question to inspect the stubbed backend response.</p>
          )}
        </section>
      </section>

      <aside className="trace-pane">
        <TracePanel trace={trace} error={error} />
      </aside>
    </main>
  )
}
```

Replace `frontend/src/features/trace/TracePanel.tsx` with:

```tsx
import type { ChatErrorState, TracePayload } from '../../types/chat'

interface TracePanelProps {
  trace: TracePayload | null
  error: ChatErrorState | null
}

export function TracePanel({ trace, error }: TracePanelProps) {
  if (error) {
    return (
      <div className="trace-panel">
        <header className="trace-header">
          <h2>Observability</h2>
          <p>Always visible for every answer.</p>
        </header>

        <section className="trace-section">
          <h3>Last request</h3>
          <p>
            <strong>Session:</strong> {error.request.sessionId}
          </p>
          <p>
            <strong>Message:</strong> {error.request.message}
          </p>
        </section>

        <section className="trace-section">
          <h3>Error details</h3>
          <p>{error.message}</p>
          <ul className="trace-list">
            {error.details.map((detail) => (
              <li key={detail}>{detail}</li>
            ))}
          </ul>
        </section>
      </div>
    )
  }

  if (!trace) {
    return (
      <div className="trace-panel">
        <header className="trace-header">
          <h2>Observability</h2>
          <p>Always visible for every answer.</p>
        </header>

        <p className="trace-empty">Send a question to inspect retrieval, tools, memory, and grounding.</p>
      </div>
    )
  }

  return (
    <div className="trace-panel">
      <header className="trace-header">
        <h2>Observability</h2>
        <p>Always visible for every answer.</p>
      </header>

      <section className="trace-section">
        <h3>Sources</h3>
        <ul className="trace-list">
          {trace.citations.map((citation) => (
            <li key={citation.sourceId}>{citation.title}</li>
          ))}
        </ul>
      </section>

      <section className="trace-section">
        <h3>Tool calls</h3>
        <ul className="trace-list">
          {trace.toolCalls.map((tool) => (
            <li key={tool.name}>
              {tool.name}: {tool.summary}
            </li>
          ))}
        </ul>
      </section>

      <section className="trace-section">
        <h3>Memory</h3>
        <ul className="trace-list">
          {trace.memoryWindow.map((entry) => (
            <li key={entry}>{entry}</li>
          ))}
        </ul>
      </section>

      <section className="trace-section">
        <h3>Grounding</h3>
        <ul className="trace-list">
          {trace.groundingNotes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      {trace.uncertainty ? (
        <section className="trace-section">
          <h3>Uncertainty</h3>
          <p>{trace.uncertainty}</p>
        </section>
      ) : null}
    </div>
  )
}
```

Replace `frontend/src/styles.css` with:

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  color: #1a1a1a;
  background: #f5f5f5;
}

.app-shell {
  display: grid;
  grid-template-columns: 1fr 400px;
  height: 100vh;
  gap: 0;
}

.chat-pane {
  display: flex;
  flex-direction: column;
  background: white;
  border-right: 1px solid #e0e0e0;
}

.chat-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.chat-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.chat-header p {
  color: #666;
  font-size: 0.875rem;
}

.composer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.composer textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.9375rem;
  resize: vertical;
}

.composer textarea:focus {
  outline: none;
  border-color: #0066cc;
}

.composer button {
  align-self: flex-start;
  padding: 0.625rem 1.25rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
}

.composer button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.form-error {
  color: #b91c1c;
  font-size: 0.875rem;
}

.latest-result {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.5rem;
}

.latest-result h2 {
  font-size: 1.125rem;
  font-weight: 600;
}

.result-empty {
  color: #666;
  font-size: 0.9375rem;
}

.result-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
}

.result-card h3 {
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.result-card--error {
  border-color: #fecaca;
  background: #fef2f2;
  color: #991b1b;
}

.trace-pane {
  background: #fafafa;
  overflow-y: auto;
  padding: 1.5rem;
}

.trace-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.trace-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.trace-header p {
  color: #666;
  font-size: 0.8125rem;
}

.trace-empty {
  color: #999;
  font-size: 0.875rem;
  font-style: italic;
}

.trace-section {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.trace-section h3 {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  color: #666;
  margin-bottom: 0.75rem;
}

.trace-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.trace-list li {
  font-size: 0.875rem;
  color: #333;
  padding-left: 1rem;
  position: relative;
}

.trace-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #999;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

- [ ] **Step 5: Run the frontend tests to verify the UI contract passes**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: `6 passed`.

- [ ] **Step 6: Commit the frontend slice**

```bash
git add frontend/src/types/chat.ts frontend/src/lib/api.ts frontend/src/features/chat/useChatSession.ts frontend/src/features/chat/ChatPage.tsx frontend/src/features/trace/TracePanel.tsx frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/trace/TracePanel.test.tsx frontend/src/styles.css
git commit -m "feat: connect the phase 1 chat form to the stub api"
```

---

### Task 3: Update tracking/docs and run the Docker Compose verification commands

**Files:**
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- Modify: `docs/local-dev.md`

- [ ] **Step 1: Update the task tracker to reflect the completed Phase 1 slice**

Update the Phase 1 checklist in `TASKS.md` to:

```md
### Phase 1 — Foundation and First Vertical Slice
- [x] Read `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- [x] Complete Docker Compose workspace scaffolding
- [x] Document the container-only local workflow
- [x] Build the frontend shell with the persistent observability panel
- [x] Build the FastAPI skeleton and stubbed chat contract
- [x] Connect the frontend to the backend chat contract
```

- [ ] **Step 2: Update the foundation plan so it matches the approved slice contract**

Add this note immediately below `### Task 4: Build the FastAPI skeleton and stubbed chat contract` in `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`:

```md
> Execution note (2026-05-07): implement this task using `docs/superpowers/plans/2026-05-07-phase1-vertical-slice-implementation.md`. The approved endpoint path is `POST /chat`, not `/api/chat`.
```

Add this note immediately below `### Task 5: Connect the frontend to the backend chat contract`:

```md
> Execution note (2026-05-07): the approved UI is a single-turn form plus latest-result panel, not a transcript view. Failed requests keep the form enabled, switch the latest-result area into an error state, and show request/error details in the observability panel.
```

- [ ] **Step 3: Expand the local-dev guide with the exact slice verification commands**

Update `docs/local-dev.md` to:

```md
# HexaRAG Local Development

## Rules
- Do not run Node, Python, PostgreSQL, or test commands directly on the host.
- Use Docker Compose for app runtime, tests, and data seeding.

## Common commands
- `docker compose up --build frontend backend postgres`
- `docker compose run --rm frontend npm run test -- --run`
- `docker compose run --rm backend uv run pytest -q`
- `docker compose run --rm backend uv run python scripts/load_structured_data.py`

## Phase 1 vertical slice checks
- `docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q`
- `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run`
- `docker compose run --rm frontend npm run build`
```

- [ ] **Step 4: Run the targeted verification commands and then the frontend build**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
docker compose run --rm frontend npm run build
```

Expected:
- backend command reports `3 passed`
- frontend command reports `6 passed`
- build exits successfully

- [ ] **Step 5: Commit the tracking and documentation updates**

```bash
git add TASKS.md docs/superpowers/plans/2026-05-06-hexarag-foundation.md docs/local-dev.md
git commit -m "docs: record the phase 1 vertical slice workflow"
```

---

## Self-Review
- **Spec coverage:** The backend contract, frontend single-turn form, latest-result state, error observability state, tests, and doc updates all map to Tasks 1-3.
- **Placeholder scan:** No `TODO`, `TBD`, or implicit “write tests” placeholders remain.
- **Type consistency:** Backend API uses snake_case (`session_id`, `tool_calls`, `memory_window`, `grounding_notes`); frontend app state uses camelCase via the centralized mapper in `frontend/src/lib/api.ts`.

## Execution Handoff
Plan complete and saved to `docs/superpowers/plans/2026-05-07-phase1-vertical-slice-implementation.md`.

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**