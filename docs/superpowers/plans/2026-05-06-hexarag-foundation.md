# HexaRAG Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build the Docker Compose-first development workspace and the first end-to-end HexaRAG vertical slice from chat UI to stubbed API response.

**Architecture:** Start with a container-only local workflow so frontend, backend, seeding, and tests all run through Docker Compose. Build a Vite + React chat shell and a FastAPI backend contract first, then connect them with a simple request/response flow so later AgentCore, retrieval, and tool work can land on a stable product skeleton.

**Tech Stack:** Docker Compose, Vite, React, TypeScript, Vitest, React Testing Library, FastAPI, Pydantic, Mangum, uv, PostgreSQL.

---

## Planned File Structure

### Root
- Create: `.gitignore` — ignore Node, Python, Terraform, build, and local env artifacts.
- Create: `docker-compose.yml` — local development stack for frontend, backend, PostgreSQL, and tooling commands.
- Create: `scripts/docker/wait-for-postgres.sh` — helper entrypoint for DB-dependent container commands.
- Create: `docs/local-dev.md` — container-only local workflow guide.

### Frontend (`frontend/`)
- Create: `frontend/Dockerfile` — frontend development/test container image.
- Create: `frontend/package.json` — scripts and dependencies for Vite + React.
- Create: `frontend/vite.config.ts` — Vite and Vitest config.
- Create: `frontend/tsconfig.json` — TypeScript configuration.
- Create: `frontend/.env.example` — `VITE_API_BASE_URL` and frontend env docs.
- Modify: `frontend/tsconfig.app.json` — app build type configuration, including Vitest globals for test files under `src`.
- Modify: `frontend/src/App.tsx` — top-level app shell.
- Modify: `frontend/src/main.tsx` — React entrypoint setup.
- Create: `frontend/src/styles.css` — base layout and component styles.
- Create: `frontend/src/types/chat.ts` — request, response, and trace types.
- Create: `frontend/src/lib/api.ts` — HTTP client for the backend API.
- Create: `frontend/src/features/chat/useChatSession.ts` — chat session state and send-message flow.
- Create: `frontend/src/features/chat/ChatPage.tsx` — main two-pane screen.
- Create: `frontend/src/features/chat/ChatPage.test.tsx` — chat screen tests.
- Create: `frontend/src/features/trace/TracePanel.tsx` — right-side observability panel.
- Create: `frontend/src/features/trace/TracePanel.test.tsx` — trace panel tests.
- Create: `frontend/src/test/setup.ts` — Vitest test setup.

### Backend (`backend/`)
- Create: `backend/Dockerfile` — backend development/test container image.
- Create: `backend/pyproject.toml` — FastAPI app dependencies and test tooling.
- Create: `backend/.env.example` — backend configuration keys.
- Create: `backend/src/hexarag_api/config.py` — environment-driven settings.
- Create: `backend/src/hexarag_api/models/chat.py` — Pydantic request/response/trace models.
- Create: `backend/src/hexarag_api/api/health.py` — health route.
- Create: `backend/src/hexarag_api/api/chat.py` — chat endpoint.
- Create: `backend/src/hexarag_api/main.py` — FastAPI app factory and route registration.
- Create: `backend/src/hexarag_api/handler.py` — Lambda handler via Mangum.
- Create: `backend/tests/test_health.py` — health route tests.
- Create: `backend/tests/api/test_chat_contract.py` — chat API contract tests.

---

### Task 1: Scaffold the Docker Compose-first development workspace

**Files:**
- Create: `.gitignore`
- Create: `docker-compose.yml`
- Create: `frontend/Dockerfile`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `scripts/docker/wait-for-postgres.sh`

- [x] **Step 1: Create the Vite + React and FastAPI workspaces inside disposable containers**

Run from `C:\Users\thanh\Desktop\workspace\xbrain\hexarag`:

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace node:22-bookworm sh -lc "npm create vite@latest frontend -- --template react-ts && cd frontend && npm install && npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom"
docker run --rm -v "$PWD:/workspace" -w /workspace ghcr.io/astral-sh/uv:python3.12-bookworm sh -lc "uv init backend --package && cd backend && uv add fastapi mangum boto3 pydantic-settings psycopg[binary] httpx python-dotenv && uv add --dev pytest pytest-asyncio ruff"
```

Add this Vite/Vitest config to `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
})
```

- [x] **Step 2: Create Dockerfiles and Compose services for frontend, backend, and Postgres**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:22-bookworm
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

Create `backend/Dockerfile`:

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen || uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "hexarag_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
services:
  frontend:
    build: ./frontend
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    environment:
      VITE_API_BASE_URL: http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    working_dir: /app
    volumes:
      - ./backend:/app
      - ./W4:/workspace/W4:ro
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://hexarag:hexarag@postgres:5432/hexarag
      MONITORING_BASE_URL: http://backend:8001
      W4_DATA_ROOT: /workspace/W4/data_package
    depends_on:
      - postgres

  postgres:
    image: postgres:16-bookworm
    environment:
      POSTGRES_DB: hexarag
      POSTGRES_USER: hexarag
      POSTGRES_PASSWORD: hexarag
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

- [x] **Step 3: Add repo-wide ignore rules, env examples, and container helper script**

Create `.gitignore` with at least:

```gitignore
node_modules/
dist/
coverage/
.venv/
__pycache__/
.pytest_cache/
*.pyc
.env
.env.*
.terraform/
terraform.tfstate*
*.tfvars
.DS_Store
```

Create `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Create `backend/.env.example`:

```env
AWS_REGION=us-east-1
ALLOWED_ORIGIN=http://localhost:5173
DATABASE_URL=postgresql://hexarag:hexarag@postgres:5432/hexarag
SESSION_TABLE_NAME=hexarag-sessions
AGENTCORE_AGENT_RUNTIME_ARN=
KNOWLEDGE_BASE_ID=
KNOWLEDGE_BASE_DATA_SOURCE_ID=
MONITORING_BASE_URL=http://backend:8001
W4_DATA_ROOT=/workspace/xbrain-learners/W4/data_package
```

Create `scripts/docker/wait-for-postgres.sh`:

```bash
#!/bin/sh
set -eu
until pg_isready -h postgres -U hexarag -d hexarag; do
  sleep 1
done
exec "$@"
```

- [x] **Step 4: Verify the toolchains through Docker Compose before writing app code**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run build
docker compose run --rm backend uv run python -c "import fastapi, boto3, psycopg"
```

Expected: frontend build succeeds and backend import check exits with no output.

- [x] **Step 5: Commit the scaffolding**

```bash
git add .gitignore docker-compose.yml frontend backend scripts/docker
git commit -m "chore: scaffold hexarag docker compose workspace"
```

---

### Task 2: Document the container-only local workflow

**Files:**
- Modify: `docs/requirements.md`
- Create: `docs/local-dev.md`

- [x] **Step 1: Write the local workflow guide**

Create `docs/local-dev.md` with these sections:

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
```

- [x] **Step 2: Commit the workflow guide**

```bash
git add docs/local-dev.md docs/requirements.md
git commit -m "docs: add docker compose local workflow"
```

---

### Task 3: Build the frontend shell with a persistent observability panel

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/tsconfig.app.json`
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/features/chat/ChatPage.tsx`
- Create: `frontend/src/features/chat/ChatPage.test.tsx`
- Create: `frontend/src/features/trace/TracePanel.tsx`
- Create: `frontend/src/features/trace/TracePanel.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/test/setup.ts`

- [x] **Step 1: Write the failing frontend layout tests**

Create `frontend/src/features/chat/ChatPage.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { ChatPage } from './ChatPage'

it('renders the chat shell and observability panel', () => {
  render(<ChatPage />)

  expect(screen.getByRole('heading', { name: 'HexaRAG' })).toBeInTheDocument()
  expect(screen.getByPlaceholderText('Ask GeekBrain anything...')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Observability' })).toBeInTheDocument()
})
```

Create `frontend/src/features/trace/TracePanel.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { TracePanel } from './TracePanel'

it('shows empty-state guidance before the first answer', () => {
  render(<TracePanel trace={null} />)
  expect(screen.getByText('Send a question to inspect retrieval, tools, memory, and grounding.')).toBeInTheDocument()
})
```

- [x] **Step 2: Run the tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected: FAIL because `ChatPage` and `TracePanel` do not exist yet.

- [x] **Step 3: Implement the app shell and shared types**

Create `frontend/src/types/chat.ts`:

```ts
export type ChatRole = 'user' | 'assistant'

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
  conflictResolution?: {
    chosenSource: string
    rationale: string
    competingSources: string[]
  }
  toolCalls: ToolCallTrace[]
  memoryWindow: string[]
  groundingNotes: string[]
  uncertainty?: string
}
```

Create `frontend/src/features/trace/TracePanel.tsx`:

```tsx
import type { TracePayload } from '../../types/chat'

export function TracePanel({ trace }: { trace: TracePayload | null }) {
  if (!trace) {
    return <aside><h2>Observability</h2><p>Send a question to inspect retrieval, tools, memory, and grounding.</p></aside>
  }

  return (
    <aside>
      <h2>Observability</h2>
      <section>
        <h3>Sources</h3>
        <ul>{trace.citations.map((item) => <li key={item.sourceId}>{item.title}</li>)}</ul>
      </section>
      <section>
        <h3>Tool calls</h3>
        <ul>{trace.toolCalls.map((tool) => <li key={tool.name}>{tool.name}: {tool.summary}</li>)}</ul>
      </section>
      <section>
        <h3>Memory</h3>
        <ul>{trace.memoryWindow.map((entry) => <li key={entry}>{entry}</li>)}</ul>
      </section>
    </aside>
  )
}
```

Create `frontend/src/features/chat/ChatPage.tsx`:

```tsx
import { TracePanel } from '../trace/TracePanel'

export function ChatPage() {
  return (
    <main className="app-shell">
      <section className="chat-pane">
        <header>
          <h1>HexaRAG</h1>
          <p>Ask GeekBrain anything.</p>
        </header>
        <div className="message-thread" />
        <form className="composer">
          <textarea placeholder="Ask GeekBrain anything..." rows={3} />
          <button type="submit">Send</button>
        </form>
      </section>
      <section className="trace-pane">
        <TracePanel trace={null} />
      </section>
    </main>
  )
}
```

Update `frontend/src/App.tsx`:

```tsx
import { ChatPage } from './features/chat/ChatPage'

export default function App() {
  return <ChatPage />
}
```

- [x] **Step 4: Add basic styles and verify the layout tests pass**

Update `frontend/src/styles.css` with a real two-pane layout:

```css
:root {
  font-family: Inter, system-ui, sans-serif;
  color: #e5e7eb;
  background: #0f172a;
}

body {
  margin: 0;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
}

.chat-pane,
.trace-pane {
  padding: 24px;
}

.trace-pane {
  border-left: 1px solid #334155;
  background: #111827;
}
```

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
docker compose run --rm frontend npm run build
```

Expected: tests PASS and build succeeds.

- [x] **Step 5: Commit the frontend shell**

```bash
git add frontend
git commit -m "feat: add hexarag chat shell and observability panel"
```

---

### Task 4: Build the FastAPI skeleton and stubbed chat contract

**Files:**
- Create: `backend/src/hexarag_api/config.py`
- Create: `backend/src/hexarag_api/models/chat.py`
- Create: `backend/src/hexarag_api/api/health.py`
- Create: `backend/src/hexarag_api/api/chat.py`
- Create: `backend/src/hexarag_api/main.py`
- Create: `backend/src/hexarag_api/handler.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/api/test_chat_contract.py`

- [x] **Step 1: Write failing backend contract tests**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from hexarag_api.main import app

client = TestClient(app)


def test_healthcheck_returns_ok():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

Create `backend/tests/api/test_chat_contract.py`:

```python
from fastapi.testclient import TestClient
from hexarag_api.main import app

client = TestClient(app)


def test_chat_returns_message_and_trace_payload():
    response = client.post('/chat', json={'session_id': 's-1', 'message': 'What is PaymentGW latency?'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['session_id'] == 's-1'
    assert payload['message']['role'] == 'assistant'
    assert 'trace' in payload['message']
    assert 'citations' in payload['message']['trace']
```

- [x] **Step 2: Run the backend tests to verify they fail**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q
```

Expected: FAIL because the FastAPI app and routes do not exist.

- [x] **Step 3: Implement Pydantic models and stub routes**

Create `backend/src/hexarag_api/models/chat.py`:

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class TracePayload(BaseModel):
    citations: list[dict] = []
    tool_calls: list[dict] = []
    memory_window: list[str] = []
    grounding_notes: list[str] = []
    uncertainty: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str
    trace: TracePayload


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage
```

Create `backend/src/hexarag_api/api/chat.py`:

```python
from fastapi import APIRouter
from hexarag_api.models.chat import ChatRequest, ChatResponse, ChatMessage, TracePayload

router = APIRouter(tags=['chat'])


@router.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        session_id=request.session_id,
        message=ChatMessage(
            role='assistant',
            content='HexaRAG stub response.',
            trace=TracePayload(
                citations=[{'sourceId': 'stub', 'title': 'stub.md', 'excerpt': 'placeholder'}],
                grounding_notes=['Stub response until AgentCore is wired.'],
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

app = FastAPI(title='HexaRAG API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(health_router)
app.include_router(chat_router)
```

Create `backend/src/hexarag_api/handler.py`:

```python
from mangum import Mangum
from hexarag_api.main import app

handler = Mangum(app)
```

- [x] **Step 4: Run the tests again and verify the contract is stable**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/test_health.py tests/api/test_chat_contract.py -q
```

Expected: PASS.

Execution note: The approved backend chat endpoint for this vertical slice is `POST /chat`, not `/api/chat`.

- [x] **Step 5: Commit the backend skeleton**

```bash
git add backend
git commit -m "feat: add fastapi chat contract and lambda handler"
```

---

### Task 5: Connect the frontend to the backend chat contract

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/features/chat/useChatSession.ts`
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/trace/TracePanel.tsx`
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`

- [x] **Step 1: Write the failing frontend interaction test**

Update `frontend/src/features/chat/ChatPage.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { ChatPage } from './ChatPage'

beforeEach(() => {
  vi.spyOn(global, 'fetch').mockResolvedValue({
    ok: true,
    json: async () => ({
      session_id: 's-1',
      message: {
        role: 'assistant',
        content: 'PaymentGW is at ~185ms.',
        trace: {
          citations: [{ sourceId: '1', title: 'monitoring', excerpt: '185ms' }],
          toolCalls: [{ name: 'service_metrics', status: 'success', summary: 'Fetched current metrics', input: {}, output: { latency_p99_ms: 185 } }],
          memoryWindow: [],
          groundingNotes: ['Used live metrics'],
        },
      },
    }),
  } as Response)
})

it('submits a question and renders the answer plus trace output', async () => {
  render(<ChatPage />)

  fireEvent.change(screen.getByPlaceholderText('Ask GeekBrain anything...'), {
    target: { value: 'What is PaymentGW current latency?' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))

  await waitFor(() => {
    expect(screen.getByText('PaymentGW is at ~185ms.')).toBeInTheDocument()
  })
  expect(screen.getByText('service_metrics: Fetched current metrics')).toBeInTheDocument()
})
```

- [x] **Step 2: Run the test to verify it fails**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx --run
```

Expected: FAIL because there is no fetch-backed state management yet.

- [x] **Step 3: Implement the API client and session hook**

Create `frontend/src/lib/api.ts`:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function postChatMessage(sessionId: string, message: string) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })

  if (!response.ok) throw new Error('Chat request failed')
  return response.json()
}
```

Create `frontend/src/features/chat/useChatSession.ts`:

```ts
import { useMemo, useState } from 'react'
import { postChatMessage } from '../../lib/api'

export function useChatSession() {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [trace, setTrace] = useState(null)
  const [isSending, setIsSending] = useState(false)
  const sessionId = useMemo(() => crypto.randomUUID(), [])

  async function sendMessage(content: string) {
    setMessages((current) => [...current, { role: 'user', content }])
    setIsSending(true)
    const payload = await postChatMessage(sessionId, content)
    setMessages((current) => [...current, payload.message])
    setTrace(payload.message.trace)
    setIsSending(false)
  }

  return { messages, trace, isSending, sendMessage }
}
```

- [x] **Step 4: Wire the UI to the hook and verify the test passes**

Update `frontend/src/features/chat/ChatPage.tsx` so submit uses `useChatSession()` and renders `messages` plus `TracePanel trace={trace}`.

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
docker compose run --rm frontend npm run build
```

Expected: PASS.

Execution note: The approved Phase 1 UI is a single-turn form plus latest-result panel, not a transcript. Failed requests keep the form enabled, switch the latest-result area into an error state, and surface the request and error details in the observability panel.

- [x] **Step 5: Commit the first vertical slice**

```bash
git add frontend
git commit -m "feat: connect chat ui to backend contract"
```

---

## Spec Coverage Check

- **FR1 Chat interaction** → Tasks 3, 4, 5
- **FR7 Observability** → Tasks 3 and 5
- **NFR4 Performance / visible progress** → Task 5 establishes the request/response UI path for later streaming or loading-state work
- **NFR5 Simplicity** → Tasks 3 and 5 keep a single-screen chat experience
- **NFR7 Containerized developer workflow** → Tasks 1 and 2

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each task lists concrete files, commands, tests, and commit boundaries.

## Type Consistency Check

Use these names consistently across the foundation slice:
- `session_id` in JSON requests/responses
- `ChatResponse.message.trace`
- `TracePayload.citations`
- `TracePayload.toolCalls` in TypeScript and `tool_calls` in Python only if the serializer explicitly maps names
- `memoryWindow` in frontend and `memory_window` in backend only if aliasing is configured centrally

Do not mix casing patterns ad hoc.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`.
