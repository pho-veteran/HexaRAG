# HexaRAG Testing and Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add W4 evaluation automation, degraded-mode regression coverage, and the final Docker Compose verification suite for HexaRAG.

**Architecture:** Keep evaluation separate from product logic by adding a dedicated backend evaluator script plus targeted regression tests in frontend and backend suites. The final phase validates that the app can be exercised through the same Docker Compose workflow that local development, testing, and evidence capture will use.

**Tech Stack:** Python, httpx, pytest, Vitest, React Testing Library, Docker Compose.

---

## Planned File Structure

### Backend (`backend/`)
- Create: `backend/scripts/evaluate_w4.py` — replay W4 L1-L4 prompts against the `/chat` API.
- Create: `backend/tests/services/test_evaluator_inputs.py` — evaluator input-loading test.
- Modify: `backend/tests/api/test_chat_contract.py` — keep graceful-failure path coverage green.

### Frontend (`frontend/`)
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — sending-state and degraded-success regression coverage.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — degraded trace rendering coverage.

### Docs
- Modify: `docs/local-dev.md` — evaluator and verification commands.
- Modify: `CLAUDE.md` — evaluator command reference.
- Modify: `TASKS.md` and `docs/superpowers/plans/2026-05-06-hexarag-v1.md` — Phase 4 progress tracking.

---

### Task 1: Add W4 evaluation automation and final verification

**Files:**
- Create: `backend/scripts/evaluate_w4.py`
- Create: `backend/tests/services/test_evaluator_inputs.py`
- Modify: `backend/tests/api/test_chat_contract.py`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`
- Modify: `docs/local-dev.md`
- Modify: `CLAUDE.md`

- [x] **Step 1: Add evaluator input coverage**

Added `backend/tests/services/test_evaluator_inputs.py` to lock down:
- level-to-file resolution for the W4 student fixtures
- L1 payload loading
- helper behavior for `--limit`

Run from `hexarag`:

```bash
docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py -q
```

- [x] **Step 2: Implement the evaluation harness**

Created `backend/scripts/evaluate_w4.py` with:
- `httpx`-based `/chat` requests
- `--api-base-url`
- `--level l1|l2|l3|l4`
- `--limit`
- `--output`
- `--questions-root`

The script resolves fixtures from the mounted W4 tree and supports both single-turn (`l1`-`l3`) and multi-turn (`l4`) evaluation flows.

- [x] **Step 3: Extend degraded-mode regression coverage**

Updated `backend/tests/api/test_chat_contract.py` to assert the degraded trace shape and session-memory behavior.

Updated `frontend/src/features/chat/ChatPage.test.tsx` to cover:
- the `Sending...` pending state
- degraded-success rendering without switching into hard-failure UI

Updated `frontend/src/features/trace/TracePanel.test.tsx` to pin degraded trace rendering.

- [x] **Step 4: Run the final verification suite**

Run from `hexarag`:

```bash
docker compose up -d --build backend postgres
docker compose run --rm backend uv run pytest tests/api/test_chat_contract.py tests/services/test_trace_formatter.py tests/services/test_evaluator_inputs.py -q
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
docker compose run --rm frontend npm run build
docker compose run --rm backend uv run pytest -q
docker compose exec backend uv run python scripts/evaluate_w4.py --api-base-url http://backend:8000 --level l1 --limit 3
docker compose down
```

Expected:
- targeted backend tests PASS
- targeted frontend tests PASS
- frontend build succeeds
- full backend tests PASS
- evaluator prints per-question results without crashing
- runtime services shut down cleanly after verification

- [ ] **Step 5: Update trackers after verification**

After the verification commands pass, mark Phase 4 complete in:
- `TASKS.md`
- `docs/superpowers/plans/2026-05-06-hexarag-v1.md`
- this plan file

Keep the Docker Compose-only workflow and the container-valid evaluator command aligned across docs.

- [ ] **Step 6: Commit the evaluation tooling**

```bash
git add backend/scripts/evaluate_w4.py backend/tests frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/trace/TracePanel.test.tsx docs/local-dev.md docs/superpowers/plans/2026-05-06-hexarag-testing.md docs/superpowers/plans/2026-05-06-hexarag-v1.md TASKS.md CLAUDE.md
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
