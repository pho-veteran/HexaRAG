# HexaRAG Task Tracker

This file tracks high-level execution across the split implementation plans. Run the plans in order. Each plan contains the full task-by-task implementation detail, test commands, and commit checkpoints.

## Execution Order

### Phase 1 — Foundation and First Vertical Slice
- [x] Read `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- [x] Complete Docker Compose workspace scaffolding
- [x] Document the container-only local workflow
- [x] Build the frontend shell with the persistent observability panel
- [x] Build the FastAPI skeleton and stubbed chat contract
- [x] Connect the frontend to the backend chat contract

### Phase 2 — Core Runtime and W4 Data Integration
- [x] Read `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md`
- [x] Implement the structured-data and monitoring services that mirror the W4 package
- [x] Implement AgentCore orchestration, recent-turn memory, and trace formatting

### Phase 3 — AWS Infrastructure and KB Sync
- [x] Read `docs/superpowers/plans/2026-05-06-hexarag-infra.md`
- [x] Provision Terraform-managed AWS resources
- [x] Add knowledge base upload and scheduled sync flow
- [x] Write `docs/aws.md`

### Phase 4 — Evaluation and Final Verification
- [x] Read `docs/superpowers/plans/2026-05-06-hexarag-testing.md`
- [x] Add W4 evaluation automation
- [x] Extend degraded-mode regression coverage
- [x] Run the full Docker Compose verification suite

## Plan Index
- `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` — local workspace, frontend shell, backend skeleton, first UI/API slice
- `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md` — W4 data services, AgentCore runtime, session memory, trace shaping
- `docs/superpowers/plans/2026-05-06-hexarag-infra.md` — Terraform, AWS deployment, knowledge base upload/sync, deployment docs
- `docs/superpowers/plans/2026-05-06-hexarag-testing.md` — evaluator, regression coverage, final verification commands
- `docs/superpowers/plans/2026-05-06-hexarag-v1.md` — umbrella index and handoff document for the split plans
- `docs/superpowers/plans/2026-05-07-frontend-observability-transcript.md` — transcript chat UI, sample demo prompts, referenced documents, per-reply trace selection
- `docs/superpowers/plans/2026-05-07-frontend-ui-remake.md` — Executive Console frontend redesign with tabbed inspection console, refined to the light gradient review variant
- `docs/superpowers/plans/2026-05-07-citation-list-modal.md` — row-by-row citation list, citation detail modal, and interactive mockup citation review
- `docs/superpowers/plans/2026-05-07-inline-numbered-citations.md` — backend inline citation anchors plus frontend numbered inline citation rendering

## Notes
- Docker Compose is the default path for local runtime, test execution, data seeding, and evaluation.
- The split plans replace the monolithic execution flow. Treat the plan files above as the implementation source of truth.
- Keep the execution order unless a later plan is explicitly made independent by the codebase state.
- After finishing any task, update the relevant docs and tracking files before marking it complete. At minimum review `TASKS.md`, and update `docs/local-dev.md`, `docs/aws.md`, `docs/requirements.md`, or the active phase plan when the task changes those areas.
