# HexaRAG Task Tracker

This file tracks high-level execution across the split implementation plans. Run the plans in order. Each plan contains the full task-by-task implementation detail, test commands, and commit checkpoints.

## Execution Order

### Phase 1 — Foundation and First Vertical Slice
- [ ] Read `docs/superpowers/plans/2026-05-06-hexarag-foundation.md`
- [ ] Complete Docker Compose workspace scaffolding
- [ ] Document the container-only local workflow
- [ ] Build the frontend shell with the persistent observability panel
- [ ] Build the FastAPI skeleton and stubbed chat contract
- [ ] Connect the frontend to the backend chat contract

### Phase 2 — Core Runtime and W4 Data Integration
- [ ] Read `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md`
- [ ] Implement the structured-data and monitoring services that mirror the W4 package
- [ ] Implement AgentCore orchestration, recent-turn memory, and trace formatting

### Phase 3 — AWS Infrastructure and KB Sync
- [ ] Read `docs/superpowers/plans/2026-05-06-hexarag-infra.md`
- [ ] Provision Terraform-managed AWS resources
- [ ] Add knowledge base upload and scheduled sync flow
- [ ] Write `docs/aws.md`

### Phase 4 — Evaluation and Final Verification
- [ ] Read `docs/superpowers/plans/2026-05-06-hexarag-testing.md`
- [ ] Add W4 evaluation automation
- [ ] Extend degraded-mode regression coverage
- [ ] Run the full Docker Compose verification suite

## Plan Index
- `docs/superpowers/plans/2026-05-06-hexarag-foundation.md` — local workspace, frontend shell, backend skeleton, first UI/API slice
- `docs/superpowers/plans/2026-05-06-hexarag-core-runtime.md` — W4 data services, AgentCore runtime, session memory, trace shaping
- `docs/superpowers/plans/2026-05-06-hexarag-infra.md` — Terraform, AWS deployment, knowledge base upload/sync, deployment docs
- `docs/superpowers/plans/2026-05-06-hexarag-testing.md` — evaluator, regression coverage, final verification commands
- `docs/superpowers/plans/2026-05-06-hexarag-v1.md` — umbrella index and handoff document for the split plans

## Notes
- Docker Compose is the default path for local runtime, test execution, data seeding, and evaluation.
- The split plans replace the monolithic execution flow. Treat the plan files above as the implementation source of truth.
- Keep the execution order unless a later plan is explicitly made independent by the codebase state.
- After finishing any task, update the relevant docs and tracking files before marking it complete. At minimum review `TASKS.md`, and update `docs/local-dev.md`, `docs/aws.md`, `docs/requirements.md`, or the active phase plan when the task changes those areas.
