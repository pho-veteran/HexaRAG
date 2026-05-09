# L1-L5 Live Audit and Tuning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deployed-product audit workflow for W4 L1-L5, run it against the live HexaRAG system, tune the highest-impact gaps, and publish a truthfully evidence-backed readiness report.

**Architecture:** Extend the existing backend evaluator into a deployed audit harness that can score L1-L5 responses, preserve session semantics, and emit a durable results ledger. Add a small browser-validation path for representative live UI checks, then use the results to drive tightly scoped agent/product/data fixes and update repo tracking with the post-audit state.

**Tech Stack:** Python, httpx, pytest, FastAPI, React, Vitest, Docker Compose, AWS Bedrock Agents, PowerShell/AWS CLI for live verification.

---

## Planned File Structure

### Backend (`backend/`)
- Modify: `backend/src/hexarag_api/services/evaluator.py` — extend the evaluator from L1-L4 replay into a richer audit service that supports L5, scoring hooks, results metadata, and persistent ledgers.
- Create: `backend/src/hexarag_api/services/audit_scoring.py` — centralized grading-fit/product-quality scoring helpers and failure taxonomy constants.
- Create: `backend/src/hexarag_api/services/ui_audit_matrix.py` — curated UI-case selection helpers derived from the W4 fixtures.
- Modify: `backend/scripts/evaluate_w4.py` — expose full audit-mode CLI flags and JSON output behavior.
- Create: `backend/scripts/audit_live_ui.py` — run a curated deployed-UI validation flow and emit structured findings.
- Modify: `backend/scripts/load_structured_data.py` — load the missing W4 structured datasets needed for L3-L5 audit parity.
- Modify: `backend/src/hexarag_api/tools/analytics.py` — add narrowly scoped structured-data queries needed by the W4 L3-L5 prompts.
- Modify: `backend/src/monitoring_api/main.py` — expand the monitoring API surface beyond `/services` and `/metrics/{service_name}` where the W4 audit exposes missing live-data coverage.
- Modify: `backend/src/monitoring_api/data.py` — align the monitoring fixture data with the expected W4 values the audit relies on.
- Test: `backend/tests/services/test_evaluator_inputs.py` — extend fixture-loading tests to L5 and richer audit metadata.
- Create: `backend/tests/services/test_audit_scoring.py` — pin scoring rules, taxonomy values, and L5 investigation-readiness handling.
- Create: `backend/tests/services/test_ui_audit_matrix.py` — pin curated UI-case selection behavior.
- Modify: `backend/tests/services/test_analytics.py` — cover the added structured-data queries.
- Modify: `backend/tests/monitoring_api/test_monitoring_routes.py` — cover any new live-monitoring endpoints required by the audit.
- Modify: `backend/tests/api/test_chat_contract.py` — preserve contract behavior for audit-visible traces and degraded paths.

### Frontend (`frontend/`)
- Create: `frontend/src/test/liveAuditHarness.test.ts` or equivalent focused test file — cover any UI-audit parsing/contract helpers if they are added client-side.
- Modify: `frontend/src/features/chat/ChatPage.test.tsx` — pin the high-risk UI behaviors the live audit will inspect, especially citations, degraded states, and multi-turn inspection behavior.
- Modify: `frontend/src/features/trace/TracePanel.test.tsx` — cover contradiction visibility, memory visibility, and uncertainty surfaces used by the audit.

### Docs and Tracking
- Modify: `docs/local-dev.md` — document the audit commands and Docker Compose workflow.
- Modify: `docs/aws.md` — document the live audit operator path against deployed resources.
- Modify: `docs/app-functionality.md` — update capability status based on actual audit results.
- Modify: `TASKS.md` — track the audit/tuning phase as completed only after results and docs are updated.
- Modify: `aws-tracking.md` — record the live audit runs, notable failures, applied fixes, and post-fix verification evidence.
- Create: `docs/superpowers/reports/2026-05-09-l1-l5-live-audit-report.md` — final readiness report with results, blockers, and improvement insights.
- Create: `artifacts/audits/2026-05-09-l1-l5-live-api-results.json` — full deployed API audit ledger.
- Create: `artifacts/audits/2026-05-09-l1-l5-live-ui-results.json` — curated deployed UI audit ledger.

---

### Task 1: Extend the evaluator into an L1-L5 live audit harness

**Files:**
- Modify: `backend/src/hexarag_api/services/evaluator.py`
- Modify: `backend/scripts/evaluate_w4.py`
- Modify: `backend/tests/services/test_evaluator_inputs.py`
- Create: `backend/tests/services/test_audit_scoring.py`

- [ ] **Step 1: Write the failing L5 fixture-loading and report-shape tests**

```python
from pathlib import Path

from hexarag_api.services.evaluator import load_level_questions, resolve_question_file, run_evaluation


def test_resolve_question_file_points_to_l5_fixture() -> None:
    path = resolve_question_file('l5')

    assert path == Path('/workspace/W4/questions/student/L5_investigation_prompts.json')


def test_run_evaluation_includes_investigation_results(fake_httpx_client) -> None:
    report = run_evaluation(
        api_base_url='https://example.invalid',
        level='l5',
        limit=1,
        client=fake_httpx_client,
    )

    assert report['level'] == 'l5'
    assert report['result_count'] == 1
    assert report['results'][0]['id'].startswith('L5-')
    assert report['results'][0]['grading_fit'] == 'unscored'
    assert report['results'][0]['product_quality'] == 'unscored'
    assert 'expected_findings' in report['results'][0]
```

- [ ] **Step 2: Run the backend evaluator tests to verify they fail first**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py tests/services/test_audit_scoring.py -q
```

Expected:
- FAIL because `l5` is not supported by `LEVEL_FILENAMES`
- FAIL because `run_evaluation` does not accept a test client override or emit scoring fields

- [ ] **Step 3: Add centralized scoring/taxonomy definitions with an unscored baseline**

```python
# backend/src/hexarag_api/services/audit_scoring.py
from typing import Literal

ScoreValue = Literal['pass', 'partial', 'fail', 'unscored']
FailureLayer = Literal[
    'agent_instruction_or_behavior',
    'knowledge_base_content_or_ingestion',
    'structured_data_coverage',
    'monitoring_or_tool_coverage',
    'backend_runtime_or_trace_shaping',
    'session_memory_behavior',
    'frontend_rendering_or_interaction',
    'aws_runtime_or_configuration',
    'evaluation_or_scoring_gap',
]


def build_unscored_result() -> dict[str, object]:
    return {
        'grading_fit': 'unscored',
        'product_quality': 'unscored',
        'overall_readiness': 'unscored',
        'primary_failure_layer': None,
        'secondary_failure_layers': [],
        'evidence_summary': '',
        'improvement_insight': '',
        'retest_priority': 'untriaged',
    }
```

- [ ] **Step 4: Extend the evaluator to support L5 and richer result records**

```python
# backend/src/hexarag_api/services/evaluator.py
LEVEL_FILENAMES = {
    'l1': 'L1_questions.json',
    'l2': 'L2_questions.json',
    'l3': 'L3_questions.json',
    'l4': 'L4_conversation_scripts.json',
    'l5': 'L5_investigation_prompts.json',
}


def evaluate_investigation_level(client, api_base_url: str, level: str, payload: dict[str, Any], limit: int | None):
    results = []
    for item in apply_limit(payload['investigations'], limit):
        session_id = f'eval-{level}-{item["id"].lower()}'
        response = evaluate_prompt(client, api_base_url, session_id, item['prompt'])
        results.append(
            {
                'id': item['id'],
                'prompt': item['prompt'],
                'expected_steps': item['expected_steps'],
                'expected_findings': item['expected_findings'],
                'data_sources_needed': item['data_sources_needed'],
                'session_id': session_id,
                'assistant_answer': response['message']['content'],
                'trace': response['message']['trace'],
                **build_unscored_result(),
            }
        )
    return results
```

- [ ] **Step 5: Expose full audit-mode CLI flags in the script entry point**

```python
# backend/scripts/evaluate_w4.py
parser.add_argument('--output', type=Path, required=True, help='File path for saving JSON audit results.')
parser.add_argument('--mode', choices=['replay', 'audit'], default='audit')
parser.add_argument('--questions-root', type=Path, help='Override the directory containing W4 student question files.')
```

Keep the script writing JSON deterministically so later audit/tuning tasks can diff outputs.

- [ ] **Step 6: Run the evaluator tests again to verify they pass**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py tests/services/test_audit_scoring.py -q
```

Expected:
- PASS
- `l5` fixture resolution works
- result records include the unscored audit fields

- [ ] **Step 7: Commit the evaluator/audit-harness baseline**

```bash
git add backend/src/hexarag_api/services/evaluator.py backend/src/hexarag_api/services/audit_scoring.py backend/scripts/evaluate_w4.py backend/tests/services/test_evaluator_inputs.py backend/tests/services/test_audit_scoring.py
git commit -m "test: extend live audit harness through l5"
```

### Task 2: Add curated UI audit selection and live UI audit execution

**Files:**
- Create: `backend/src/hexarag_api/services/ui_audit_matrix.py`
- Create: `backend/scripts/audit_live_ui.py`
- Create: `backend/tests/services/test_ui_audit_matrix.py`
- Modify: `frontend/package.json`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Write the failing UI-matrix tests**

```python
from hexarag_api.services.ui_audit_matrix import select_ui_cases


def test_select_ui_cases_keeps_high_risk_cases_per_level() -> None:
    cases = select_ui_cases()

    ids = {case['id'] for case in cases}
    assert 'L1-01' in ids
    assert 'L2-01' in ids
    assert 'L3-04' in ids
    assert 'L4-01' in ids
    assert 'L5-01' in ids
```

- [ ] **Step 2: Run the UI-matrix tests to verify they fail**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_ui_audit_matrix.py -q
```

Expected:
- FAIL because the matrix helper does not exist yet

- [ ] **Step 3: Add the curated UI-case selector**

```python
# backend/src/hexarag_api/services/ui_audit_matrix.py
UI_CASE_IDS = {
    'l1': {'L1-01', 'L1-03'},
    'l2': {'L2-01', 'L2-05'},
    'l3': {'L3-04', 'L3-06', 'L3-09'},
    'l4': {'L4-01', 'L4-03'},
    'l5': {'L5-01', 'L5-03'},
}
```

Build this helper from the same W4 fixture loader path used by the evaluator so the selection stays repo-driven.

- [ ] **Step 4: Add a minimal browser automation dependency and script entry point**

```json
// frontend/package.json
{
  "scripts": {
    "audit:ui": "playwright test --config=playwright.live-audit.config.ts"
  },
  "devDependencies": {
    "@playwright/test": "^1.56.1"
  }
}
```

```toml
# backend/pyproject.toml
[dependency-groups]
dev = [
  "pytest>=9.0.3",
  "pytest-asyncio>=1.3.0",
  "ruff>=0.15.12",
  "requests>=2.32.5",
]
```

- [ ] **Step 5: Create the live UI audit runner**

```python
# backend/scripts/audit_live_ui.py
from pathlib import Path
import json
import subprocess


def main() -> None:
    output = Path('/workspace/repo/artifacts/audits/2026-05-09-l1-l5-live-ui-results.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['docker', 'compose', 'run', '--rm', 'frontend', 'npm', 'run', 'audit:ui'],
        check=True,
    )
    output.write_text(json.dumps({'status': 'completed'}), encoding='utf-8')
```

This first pass can be thin; later tasks will enrich what the browser audit records.

- [ ] **Step 6: Run the UI-matrix tests again to verify they pass**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_ui_audit_matrix.py -q
```

Expected:
- PASS
- the curated UI subset includes at least one representative case for each L1-L5 level

- [ ] **Step 7: Commit the UI-audit scaffolding**

```bash
git add backend/src/hexarag_api/services/ui_audit_matrix.py backend/scripts/audit_live_ui.py backend/tests/services/test_ui_audit_matrix.py frontend/package.json backend/pyproject.toml
git commit -m "test: add live ui audit scaffolding"
```

### Task 3: Fill the L3-L5 structured-data and monitoring gaps the audit depends on

**Files:**
- Modify: `backend/scripts/load_structured_data.py`
- Modify: `backend/src/hexarag_api/tools/analytics.py`
- Modify: `backend/src/monitoring_api/main.py`
- Modify: `backend/src/monitoring_api/data.py`
- Modify: `backend/tests/services/test_analytics.py`
- Modify: `backend/tests/monitoring_api/test_monitoring_routes.py`

- [ ] **Step 1: Write the failing analytics and monitoring tests for W4-required coverage**

```python
from hexarag_api.tools.analytics import fetch_q1_incident_summary, fetch_sla_target, fetch_q1_average_latency


def test_fetch_sla_target_returns_paymentgw_threshold(fake_db_connection):
    result = fetch_sla_target(fake_db_connection, 'PaymentGW')

    assert result['latency_p99_ms'] == 200
    assert result['error_rate_percent'] == 0.1
```

```python
from fastapi.testclient import TestClient
from monitoring_api.main import app

client = TestClient(app)


def test_status_endpoint_returns_service_health_shape():
    response = client.get('/status/PaymentGW')

    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
```

- [ ] **Step 2: Run the focused data/tool tests to verify they fail**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q
```

Expected:
- FAIL because only `monthly_costs` is loaded today
- FAIL because `/status/{service}` and richer monitoring coverage do not exist yet

- [ ] **Step 3: Extend the structured-data loader to all required W4 CSVs**

```python
# backend/scripts/load_structured_data.py
LOADERS = (
    load_monthly_costs,
    load_incidents,
    load_sla_targets,
    load_daily_metrics,
)

for loader in LOADERS:
    loader(data_root, connection)
```

Add one loader per CSV with the exact column inserts needed for the existing database schema or the schema changes introduced in the same task.

- [ ] **Step 4: Add the narrowly scoped analytics queries required by the audit prompts**

```python
# backend/src/hexarag_api/tools/analytics.py
def fetch_sla_target(connection, service: str) -> Mapping[str, float]:
    ...


def fetch_q1_average_latency(connection, service: str) -> Mapping[str, float]:
    ...


def fetch_q1_incident_summary(connection, service: str | None = None) -> Mapping[str, object]:
    ...
```

Keep the functions small and prompt-driven rather than building a generic analytics framework.

- [ ] **Step 5: Add the missing monitoring routes the live audit needs**

```python
# backend/src/monitoring_api/main.py
@app.get('/status/{service_name}')
def get_status(service_name: str) -> dict[str, str | int | float]:
    ...


@app.get('/incidents')
def list_recent_incidents() -> dict[str, list[dict[str, str | int]]]:
    ...
```

Populate them from `backend/src/monitoring_api/data.py` using W4-aligned static monitoring fixtures where the repo already uses static live-state data.

- [ ] **Step 6: Run the focused data/tool tests again to verify they pass**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q
```

Expected:
- PASS
- loader and tool coverage now support the L3/L4/L5 audit expectations the repo claims

- [ ] **Step 7: Commit the data/tool coverage expansion**

```bash
git add backend/scripts/load_structured_data.py backend/src/hexarag_api/tools/analytics.py backend/src/monitoring_api/main.py backend/src/monitoring_api/data.py backend/tests/services/test_analytics.py backend/tests/monitoring_api/test_monitoring_routes.py
git commit -m "feat: expand w4 audit data coverage"
```

### Task 4: Make the audit results human-judgeable and product-focused

**Files:**
- Modify: `backend/src/hexarag_api/services/evaluator.py`
- Modify: `backend/src/hexarag_api/services/audit_scoring.py`
- Modify: `backend/tests/services/test_audit_scoring.py`
- Modify: `backend/tests/api/test_chat_contract.py`

- [ ] **Step 1: Write the failing scoring tests for grading-fit and product-quality heuristics**

```python
from hexarag_api.services.audit_scoring import score_single_turn_result


def test_score_single_turn_result_flags_missing_citations_for_l1() -> None:
    result = score_single_turn_result(
        level='l1',
        answer='The policy says deploy on Tuesdays.',
        trace={'citations': [], 'tool_calls': [], 'memory_window': []},
        expected_answer='Deployments happen on Tuesdays.',
    )

    assert result['grading_fit'] == 'partial'
    assert result['product_quality'] == 'fail'
    assert result['primary_failure_layer'] == 'backend_runtime_or_trace_shaping'
```

- [ ] **Step 2: Run the scoring and contract tests to verify they fail**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_audit_scoring.py tests/api/test_chat_contract.py -q
```

Expected:
- FAIL because the scoring helper has no level-aware logic yet

- [ ] **Step 3: Add simple, explicit heuristics for the first audit pass**

```python
# backend/src/hexarag_api/services/audit_scoring.py
def score_single_turn_result(level: str, answer: str, trace: dict[str, object], expected_answer: str) -> dict[str, object]:
    has_citations = bool(trace.get('citations'))
    has_tools = bool(trace.get('tool_calls'))
    has_memory = bool(trace.get('memory_window'))
    normalized = build_unscored_result()

    if level == 'l1' and has_citations:
        normalized['grading_fit'] = 'pass'
        normalized['product_quality'] = 'pass'
        normalized['overall_readiness'] = 'pass'
    elif level == 'l1':
        normalized['grading_fit'] = 'partial'
        normalized['product_quality'] = 'fail'
        normalized['overall_readiness'] = 'fail'
        normalized['primary_failure_layer'] = 'backend_runtime_or_trace_shaping'

    return normalized
```

Keep the heuristics deliberately readable so the audit report can explain them.

- [ ] **Step 4: Wire the evaluator to attach scoring outputs during live runs**

```python
# backend/src/hexarag_api/services/evaluator.py
scored = score_single_turn_result(
    level=level,
    answer=response['message']['content'],
    trace=response['message']['trace'],
    expected_answer=item['expected_answer'],
)
```

Apply the equivalent level-aware scoring helper for L4 conversation turns and L5 investigations.

- [ ] **Step 5: Run the scoring tests again to verify they pass**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_audit_scoring.py tests/api/test_chat_contract.py -q
```

Expected:
- PASS
- the audit harness now emits scored case records instead of only replay payloads

- [ ] **Step 6: Commit the scoring pass**

```bash
git add backend/src/hexarag_api/services/evaluator.py backend/src/hexarag_api/services/audit_scoring.py backend/tests/services/test_audit_scoring.py backend/tests/api/test_chat_contract.py
git commit -m "test: score live audit outputs"
```

### Task 5: Add representative UI validation coverage in frontend tests and browser audit flow

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/trace/TracePanel.test.tsx`
- Create: `frontend/playwright.live-audit.config.ts`
- Create: `frontend/tests/live-audit.spec.ts`

- [ ] **Step 1: Write the failing frontend tests for contradiction, memory, and uncertainty visibility**

```tsx
it('shows contradiction handling details for a selected assistant response', async () => {
  render(<ChatPage />)

  expect(await screen.findByText('Conflict resolution')).toBeInTheDocument()
  expect(screen.getByText(/newest valid source/i)).toBeInTheDocument()
})
```

- [ ] **Step 2: Run the focused frontend tests to verify they fail**

Run:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected:
- FAIL because the asserted contradiction/memory/uncertainty surfaces are not fully pinned yet

- [ ] **Step 3: Add the smallest frontend assertions and browser audit script needed by the live audit**

```ts
// frontend/tests/live-audit.spec.ts
import { test, expect } from '@playwright/test'

test('L3 live audit case renders answer and inspection details', async ({ page }) => {
  await page.goto(process.env.HEXARAG_LIVE_FRONTEND_URL!)
  await page.getByRole('textbox', { name: 'Question' }).fill("Is PaymentGW's current error rate within its SLA target?")
  await page.getByRole('button', { name: 'Send' }).click()
  await expect(page.getByRole('article', { name: /Response/i })).toBeVisible()
  await expect(page.getByText('Sources')).toBeVisible()
})
```

- [ ] **Step 4: Run the focused frontend tests again to verify they pass**

Run:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run
```

Expected:
- PASS
- the same UI behaviors the live audit will judge are now pinned locally

- [ ] **Step 5: Commit the frontend audit coverage**

```bash
git add frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/trace/TracePanel.test.tsx frontend/playwright.live-audit.config.ts frontend/tests/live-audit.spec.ts
git commit -m "test: cover live audit ui behaviors"
```

### Task 6: Run the first live audit sweep and capture artifacts

**Files:**
- Modify: `docs/local-dev.md`
- Create: `artifacts/audits/2026-05-09-l1-l5-live-api-results.json`
- Create: `artifacts/audits/2026-05-09-l1-l5-live-ui-results.json`
- Modify: `aws-tracking.md`

- [ ] **Step 1: Document the live-audit commands before running them**

Add a short section to `docs/local-dev.md` with the exact commands:

```md
## Live deployed audit
- `docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l1 --output /workspace/repo/artifacts/audits/2026-05-09-l1-results.json`
- repeat for `l2`, `l3`, `l4`, and `l5`
- `docker compose run --rm backend uv run python scripts/audit_live_ui.py`
```

- [ ] **Step 2: Run a smoke audit for one case per level first**

Run:

```bash
docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l1 --limit 1 --output /workspace/repo/artifacts/audits/2026-05-09-l1-smoke.json && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l5 --limit 1 --output /workspace/repo/artifacts/audits/2026-05-09-l5-smoke.json
```

Expected:
- both commands succeed
- JSON artifacts exist under `artifacts/audits/`
- records include scored audit fields

- [ ] **Step 3: Run the full deployed API sweep across L1-L5**

Run:

```bash
docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l1 --output /workspace/repo/artifacts/audits/2026-05-09-l1-results.json && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l2 --output /workspace/repo/artifacts/audits/2026-05-09-l2-results.json && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l3 --output /workspace/repo/artifacts/audits/2026-05-09-l3-results.json && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l4 --output /workspace/repo/artifacts/audits/2026-05-09-l4-results.json && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level l5 --output /workspace/repo/artifacts/audits/2026-05-09-l5-results.json
```

Expected:
- all five runs complete
- artifacts are written without manual path repair
- the raw ledgers can be inspected for failure clustering

- [ ] **Step 4: Run the curated live UI audit**

Run:

```bash
docker compose run --rm -e HEXARAG_LIVE_FRONTEND_URL=https://d1utyuhmju4jzn.cloudfront.net frontend npm run audit:ui
```

Expected:
- the browser audit completes
- at least one case per level is checked through the real product UI

- [ ] **Step 5: Record the first live-audit evidence in `aws-tracking.md`**

Add a dated section with:
- commands run
- artifact paths created
- immediate high-level findings per level
- major failure clusters noticed in the first pass

- [ ] **Step 6: Commit the audit-run evidence and operator docs**

```bash
git add docs/local-dev.md aws-tracking.md artifacts/audits
git commit -m "test: capture initial live audit evidence"
```

### Task 7: Tune the highest-impact failure clusters and re-run regressions

**Files:**
- Modify only the files implicated by the first audit results
- Likely candidates: `backend/src/hexarag_api/services/agent_runtime.py`, `backend/src/hexarag_api/services/trace_formatter.py`, `backend/src/hexarag_api/tools/analytics.py`, `backend/src/monitoring_api/main.py`, `backend/src/monitoring_api/data.py`, `frontend/src/features/chat/ChatPage.tsx`, `frontend/src/features/trace/TracePanel.tsx`, `docs/app-functionality.md`, `aws-tracking.md`

- [ ] **Step 1: Choose one failure cluster and write the narrow failing test for it**

Example if citations are the first cluster:

```python
def test_normalized_trace_preserves_inline_citations_for_retrieval_answers() -> None:
    ...
```

Example if L3 SLA comparison is the first cluster:

```python
def test_fetch_sla_comparison_returns_current_and_target_values(fake_db_connection) -> None:
    ...
```

Do not batch unrelated fixes into one test step.

- [ ] **Step 2: Run only that failing test first**

Run the smallest relevant command, for example:

```bash
docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py::test_normalized_trace_preserves_inline_citations_for_retrieval_answers -q
```

Expected:
- FAIL for the exact observed gap

- [ ] **Step 3: Implement the smallest effective fix for that cluster**

Keep the code change specific to the observed failure. Example pattern:

```python
if retrieved_refs and not normalized_inline_citations:
    normalized_inline_citations = synthesize_inline_citations(answer_text, retrieved_refs)
```

Use the real implicated file and function, not a speculative abstraction.

- [ ] **Step 4: Re-run the targeted test and the impacted level audit**

Run:

```bash
docker compose run --rm backend uv run pytest <targeted-test-command> && docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://subsponqyl.execute-api.us-east-1.amazonaws.com --level <impacted-level> --output /workspace/repo/artifacts/audits/2026-05-09-<impacted-level>-rerun.json
```

Expected:
- targeted regression PASS
- impacted level shows measurable improvement

- [ ] **Step 5: Repeat per failure cluster until the top blockers are addressed**

Use one commit per cluster, such as:

```bash
git add <exact files>
git commit -m "fix: improve l3 grounded sla audit results"
```

### Task 8: Publish the readiness report and update all tracking docs

**Files:**
- Create: `docs/superpowers/reports/2026-05-09-l1-l5-live-audit-report.md`
- Modify: `docs/app-functionality.md`
- Modify: `docs/aws.md`
- Modify: `TASKS.md`
- Modify: `docs/superpowers/plans/2026-05-09-l1-l5-live-audit-and-tuning.md`

- [ ] **Step 1: Write the final readiness report from the audit artifacts**

Use this structure:

```md
# L1-L5 Live Audit Report

## Summary
- L1: ...
- L2: ...
- L3: ...
- L4: ...
- L5: ...

## Highest-impact failure clusters
1. ...
2. ...
3. ...

## Improvements applied
- ...

## Remaining risks
- ...

## Product-ready verdict
- ...
```

- [ ] **Step 2: Update `docs/app-functionality.md` to reflect the post-audit reality**

Change only the rows the audit actually proved up or disproved. Example pattern:

```md
| Tooling | Historical structured answers | Users can ask for exact historical numeric values grounded in structured data. | working | The live audit now covers monthly costs, incidents, SLA targets, and daily metrics. | Mixed-source answers still need more L5-proofing. |
```

- [ ] **Step 3: Update `docs/aws.md` with the live-audit operator workflow and caveats**

Add the exact deployed-audit commands and any caveats that remained after tuning.

- [ ] **Step 4: Update `TASKS.md` and this plan file after the final verification**

Mark the audit/tuning work complete only after:
- live API sweep complete
- curated UI sweep complete
- top failure clusters tuned and re-run
- readiness report written
- tracking docs updated

- [ ] **Step 5: Run the final verification suite**

Run:

```bash
docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py tests/services/test_audit_scoring.py tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py tests/api/test_chat_contract.py -q && docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx --run && docker compose run --rm frontend npm run build
```

Expected:
- backend audit/data/contract tests PASS
- frontend UI-audit-supporting tests PASS
- production build succeeds

- [ ] **Step 6: Commit the final report and tracking updates**

```bash
git add docs/superpowers/reports/2026-05-09-l1-l5-live-audit-report.md docs/app-functionality.md docs/aws.md TASKS.md docs/superpowers/plans/2026-05-09-l1-l5-live-audit-and-tuning.md
git commit -m "docs: publish live audit readiness report"
```

---

## Spec Coverage Check

- **Full deployed API audit over L1-L5** → Tasks 1, 4, and 6
- **Curated live UI validation** → Tasks 2, 5, and 6
- **Scoring model for grading fit and product quality** → Task 4
- **Failure taxonomy and root-cause clustering** → Tasks 1 and 4, then exercised in Task 7
- **Tuning loop across any implicated layer** → Task 7
- **Final readiness report and truthfully updated docs** → Task 8
- **L5 investigation-readiness framing instead of full autonomous delivery** → Tasks 1 and 4, then reported in Task 8

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- Each task includes exact files, commands, and expected outcomes.
- Task 7 intentionally uses a repeated cluster loop because the exact cluster order depends on real audit findings; the loop still specifies the required TDD sequence, re-run pattern, and commit discipline for each cluster.

## Type Consistency Check

Use these names consistently across the implementation:
- `grading_fit`
- `product_quality`
- `overall_readiness`
- `primary_failure_layer`
- `secondary_failure_layers`
- `retest_priority`
- `artifacts/audits/`
- `docs/superpowers/reports/2026-05-09-l1-l5-live-audit-report.md`
- `scripts/evaluate_w4.py`
- `scripts/audit_live_ui.py`

Do not rename these keys between the evaluator, scoring service, artifacts, and readiness report.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-09-l1-l5-live-audit-and-tuning.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration

2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?