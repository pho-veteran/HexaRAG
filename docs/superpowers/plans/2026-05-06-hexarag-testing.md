# HexaRAG Testing and Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add W4 evaluation automation, degraded-mode regression coverage, and the final Docker Compose verification suite for HexaRAG.

**Architecture:** Keep evaluation separate from product logic by adding a dedicated root-level evaluator script plus targeted regression tests in frontend and backend suites. The final phase validates that the app can be exercised through the same Docker Compose workflow that local development, testing, and evidence capture will use.

**Tech Stack:** Python, requests, pytest, Vitest, React Testing Library, Docker Compose.

---

## Planned File Structure

### Root
- Create: `scripts/evaluate_w4.py` — replay W4 L1-L4 questions against the deployed API.

### Backend (`backend/`)
- Create: `backend/tests/services/test_evaluator_inputs.py` — evaluator input-loading test.
- Modify: `backend/tests/api/test_chat_contract.py` — keep graceful-failure path coverage green.

### Frontend (`frontend/`)
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — sending-state regression coverage.

### Docs
- Modify: `docs/local-dev.md` — evaluator and verification commands.

---

### Task 1: Add W4 evaluation automation and final verification

**Files:**
- Create: `scripts/evaluate_w4.py`
- Create: `backend/tests/services/test_evaluator_inputs.py`
- Modify: `backend/tests/api/test_chat_contract.py`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `docs/local-dev.md`

- [ ] **Step 1: Write a failing evaluator unit test**

Create `backend/tests/services/test_evaluator_inputs.py`:

```python
from pathlib import Path
from evaluate_w4 import load_level_questions


def test_load_level_questions_reads_l1_fixture():
    fixture = Path('../xbrain-learners/W4/questions/student/L1_questions.json')
    payload = load_level_questions(fixture)
    assert payload['level'] == 1
    assert len(payload['questions']) >= 1
```

- [ ] **Step 2: Run the evaluator test to verify it fails**

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest backend/tests/services/test_evaluator_inputs.py -q
```

Expected: FAIL because `scripts/evaluate_w4.py` does not exist.

- [ ] **Step 3: Implement the evaluation harness**

Create `scripts/evaluate_w4.py`:

```python
import json
from pathlib import Path
import requests


def load_level_questions(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def evaluate_question(api_base_url: str, session_id: str, prompt: str) -> dict:
    response = requests.post(
        f'{api_base_url}/chat',
        json={'session_id': session_id, 'message': prompt},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

Add CLI flags:
- `--api-base-url`
- `--level l1|l2|l3|l4`
- `--limit`
- `--output`

- [ ] **Step 4: Add final UI and API regression tests for degraded behavior**

Extend `frontend/src/features/chat/ChatPage.test.tsx` with:

```tsx
it('shows a sending state while waiting for the backend', async () => {
  let resolveFetch: (value: Response) => void
  vi.spyOn(global, 'fetch').mockReturnValue(new Promise((resolve) => {
    resolveFetch = resolve
  }) as Promise<Response>)

  render(<ChatPage />)
  fireEvent.change(screen.getByPlaceholderText('Ask GeekBrain anything...'), { target: { value: 'Check PaymentGW SLA' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))

  expect(screen.getByText('Thinking...')).toBeInTheDocument()

  resolveFetch!({
    ok: true,
    json: async () => ({ session_id: 's-1', message: { role: 'assistant', content: 'done', trace: { citations: [], toolCalls: [], memoryWindow: [], groundingNotes: [] } } }),
  } as Response)
})
```

Also keep the backend failure-path test from the runtime plan green.

Update `docs/local-dev.md` to include:

```md
- `docker compose run --rm frontend npm run test -- --run`
- `docker compose run --rm backend uv run pytest -q`
- `docker compose run --rm backend uv run python /workspace/scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l1 --limit 3`
```

- [ ] **Step 5: Run the full verification suite**

Run from `hexarag`:

```bash
docker compose run --rm frontend npm run test -- --run
docker compose run --rm frontend npm run build
docker compose run --rm backend uv run pytest -q
docker compose run --rm backend uv run python /workspace/scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l1 --limit 3
```

Expected:
- frontend tests PASS
- frontend build succeeds
- backend tests PASS
- evaluator prints per-question results without crashing

- [ ] **Step 6: Commit the evaluation tooling**

```bash
git add scripts backend/tests frontend/src/features/chat/ChatPage.test.tsx docs/local-dev.md
git commit -m "test: add w4 evaluation harness and docker verification"
```

---

## Spec Coverage Check

- **FR11 Testing support** → Task 1
- **12.1 Question-set alignment** → Task 1 evaluator loads W4 question files
- **12.3 Test execution model** → Task 1 verification commands use Docker Compose
- **FR9 Graceful failure behavior** → Task 1 preserves degraded-mode regression coverage
- **NFR7 Containerized developer workflow** → Task 1 verification commands use Docker Compose only

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- The plan includes exact tests, commands, and expected results.

## Type Consistency Check

Use these names consistently across evaluator and tests:
- `session_id`
- `/chat`
- `--api-base-url`
- `--level`
- `--limit`
- `--output`

Do not change CLI flag names between the script, docs, and verification commands.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-06-hexarag-testing.md`.
