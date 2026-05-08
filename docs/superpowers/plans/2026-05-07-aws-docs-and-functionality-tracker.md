# AWS Docs and Functionality Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `docs/aws.md` so it reflects the real AWS/Bedrock deployment flow in this repo, and add `docs/app-functionality.md` as the single tracker for all expected product capabilities and their Bedrock mapping.

**Architecture:** Keep deployment guidance and capability tracking in separate documents with clear boundaries. Ground every statement in the current repo state by checking the Terraform files, backend scripts, frontend UI surface, and W4 data package before editing the docs.

**Tech Stack:** Markdown documentation, Terraform references, AWS CLI references, FastAPI/Python scripts, React/TypeScript frontend files

---

## File Structure

- **Modify:** `docs/aws.md` — canonical AWS deployment runbook for the repo as it exists today.
- **Create:** `docs/app-functionality.md` — narrative overview plus status matrix for all expected app capabilities.
- **Modify:** `TASKS.md` — keep repo tracking aligned with the new documentation work and add this plan to the plan index.
- **Reference:** `docs/local-dev.md` — Docker Compose-first local workflow language.
- **Reference:** `docs/requirements.md` — expected product capabilities and W4 source-of-truth boundaries.
- **Reference:** `docs/superpowers/specs/2026-05-07-aws-docs-and-app-functionality-design.md` — approved design for this task.
- **Reference:** `infra/terraform/terraform.tfvars.example` — required Bedrock and deployment inputs.
- **Reference:** `infra/terraform/storage.tf` — frontend and knowledge-base buckets plus CloudFront/OAC wiring.
- **Reference:** `infra/terraform/compute.tf` — Lambda handlers, env vars, API routes, and Bedrock identifier injection.
- **Reference:** `infra/terraform/outputs.tf` — currently exposed deployment outputs.
- **Reference:** `backend/scripts/upload_knowledge_base.py` — KB S3 upload flow.
- **Reference:** `backend/scripts/sync_knowledge_base.py` — Bedrock ingestion trigger flow.
- **Reference:** `backend/scripts/load_structured_data.py` — actual structured-data load scope.
- **Reference:** `backend/src/hexarag_api/config.py` — deployed origin and runtime defaults.
- **Reference:** `backend/src/monitoring_api/main.py` — monitoring surface currently exposed by the repo.
- **Reference:** `frontend/src/lib/api.ts` — frontend build-time API base URL behavior.
- **Reference:** `frontend/src/types/chat.ts` — UI-facing trace contract.
- **Reference:** `frontend/src/features/chat/ChatPage.tsx` — visible chat, citations, and mockup surface.
- **Reference:** `frontend/src/features/trace/TracePanel.tsx` — right-side inspection console behaviors.
- **Reference:** `frontend/src/features/chat/useChatSession.ts` — chat-session UX behavior and trace selection.
- **Reference:** `W4/data_package/README.md` — expected knowledge-base, structured-data, and monitoring capabilities.

### Task 1: Refresh the factual source map before editing docs

**Files:**
- Modify: `docs/aws.md`
- Create: `docs/app-functionality.md`
- Reference: `docs/requirements.md`
- Reference: `docs/local-dev.md`
- Reference: `W4/data_package/README.md`
- Reference: `infra/terraform/terraform.tfvars.example`
- Reference: `infra/terraform/storage.tf`
- Reference: `infra/terraform/compute.tf`
- Reference: `infra/terraform/outputs.tf`
- Reference: `backend/scripts/upload_knowledge_base.py`
- Reference: `backend/scripts/sync_knowledge_base.py`
- Reference: `backend/scripts/load_structured_data.py`
- Reference: `backend/src/hexarag_api/config.py`
- Reference: `backend/src/monitoring_api/main.py`
- Reference: `frontend/src/lib/api.ts`
- Reference: `frontend/src/types/chat.ts`
- Reference: `frontend/src/features/chat/ChatPage.tsx`
- Reference: `frontend/src/features/trace/TracePanel.tsx`
- Reference: `frontend/src/features/chat/useChatSession.ts`

- [ ] **Step 1: Re-read the approved design and source-of-truth docs**

Read these files before drafting any copy:

```text
- docs/superpowers/specs/2026-05-07-aws-docs-and-app-functionality-design.md
- docs/requirements.md
- docs/local-dev.md
- W4/data_package/README.md
```

Expected: a written checklist in your notes covering deployment facts, expected W4 capabilities, and the required outputs for `docs/aws.md` and `docs/app-functionality.md`.

- [ ] **Step 2: Capture the real deployment facts from Terraform and helper scripts**

Extract these facts from the repo and keep them in working notes:

```text
- Terraform requires knowledge_base_id, knowledge_base_data_source_id, and agent_runtime_arn from terraform.tfvars.example.
- storage.tf creates frontend and knowledge-base buckets plus CloudFront/OAC, but does not show an S3 bucket policy.
- compute.tf injects Bedrock IDs into the backend Lambda, exposes POST /chat, GET /services, and GET /metrics/{service_name}, and points monitoring at handler monitoring_api.main.handler.
- outputs.tf exposes backend_api_url, monitoring_api_url, frontend_bucket_name, knowledge_base_bucket_name, session_table_name, and postgres_endpoint only.
- upload_knowledge_base.py uploads markdown files from W4/data_package/knowledge_base.
- sync_knowledge_base.py starts a Bedrock ingestion job using Settings.knowledge_base_id and Settings.knowledge_base_data_source_id.
- load_structured_data.py currently loads only monthly_costs.csv into monthly_costs.
- config.py defaults allowed_origin to http://localhost:5173.
- frontend/src/lib/api.ts uses VITE_API_BASE_URL at build time and falls back to localhost outside tests.
```

Expected: a fact list you can map directly into the revised runbook caveats and verification steps.

- [ ] **Step 3: Capture the visible product surface for the functionality tracker**

Review the frontend and trace contract files and record the visible behaviors they expose:

```text
- ChatPage.tsx renders sample questions, the conversation thread, inline citation links, document rows, an inspect-response action, a citation modal, and a mockup dialog.
- TracePanel.tsx renders Observability and Thinking process tabs, source/tool/memory/grounding/uncertainty sections, error details, and an Open frontend mockup button.
- useChatSession.ts uses a fixed session id, appends user and assistant messages, auto-selects the latest assistant trace, and clears errors when appropriate.
- frontend/src/types/chat.ts defines the UI trace shape: citations, inlineCitations, toolCalls, memoryWindow, groundingNotes, and uncertainty.
```

Expected: a capability list you can convert into matrix rows instead of a raw component inventory.

- [ ] **Step 4: Verify current AWS CLI capability references before documenting CLI setup**

Use Context7 for `/aws/aws-cli` and verify that the runbook can name CLI-based Bedrock setup paths for these operations:

```text
- bedrock-agent create-knowledge-base
- bedrock-agent create-data-source
- bedrock-agentcore-control create-agent-runtime
```

Expected: confirmation that `docs/aws.md` can honestly describe Bedrock setup as “CLI or Console” rather than “Console only.”

### Task 2: Rewrite the front half of `docs/aws.md`

**Files:**
- Modify: `docs/aws.md`
- Reference: `docs/local-dev.md`
- Reference: `infra/terraform/terraform.tfvars.example`
- Reference: `infra/terraform/storage.tf`
- Reference: `backend/scripts/upload_knowledge_base.py`
- Reference: `backend/scripts/sync_knowledge_base.py`

- [ ] **Step 1: Replace the intro so the runbook describes the repo as it exists today**

Update the opening sections of `docs/aws.md` so they say the repo is not one-click, Terraform does not create the Bedrock-side identifiers, and deployment guidance is grounded in the current repo shape.

Write intro copy in this structure:

```md
# HexaRAG AWS Deployment Guide

This guide is a beginner-friendly runbook for deploying HexaRAG to AWS as the repository exists today.

It is written for:
- AWS region `us-east-1`
- app name `hexarag`
- AWS-generated URLs only
- a beginner operator with admin access to their AWS account

This repo is not a one-click deployment yet. Some steps are CLI-driven, some can be done in the AWS Console, and some depend on current repo limitations that are called out explicitly below.
```

Expected: the old “manual console work” framing is removed from the intro and replaced with neutral operator language.

- [ ] **Step 2: Keep the label legend, but update it to support CLI-or-console Bedrock work**

Ensure the label section still contains these operator modes and that later steps use them consistently:

```md
- **AWS CLI or SDK** — use terminal commands or scripts against AWS services.
- **Manual in AWS Console** — use the AWS web console instead of CLI.
- **Run locally yourself** — run the command on your machine.
- **Claude can help/run** — Claude can help prepare files, explain values, or run repo commands with you.
- **Verify manually** — stop and confirm the result before continuing.
```

Expected: the runbook vocabulary now supports both CLI and Console paths.

- [ ] **Step 3: Add a “Current deployment model” section before the numbered steps**

Insert a short factual section with these bullets:

```md
## Current deployment model
- S3 + CloudFront host the frontend assets.
- API Gateway + Lambda expose the FastAPI chat API.
- API Gateway + Lambda expose the monitoring API.
- PostgreSQL stores structured historical data.
- DynamoDB stores recent session memory.
- An S3 bucket stores knowledge base markdown documents.
- A scheduled sync Lambda exists for knowledge base ingestion support.
- Terraform consumes `knowledge_base_id`, `knowledge_base_data_source_id`, and `agent_runtime_arn`, but this repo does not create those Bedrock resources directly.
```

Expected: a reader can tell what Terraform creates and what it expects as external inputs before reading the steps.

- [ ] **Step 4: Replace the current Bedrock prerequisite section with CLI-or-console setup paths**

Rewrite the current Step 5 area so it has one subsection for CLI users and one for Console users, while preserving the same required outputs.

Use this heading structure:

```md
## Step 5: Create or locate the Bedrock prerequisites

Terraform does not create these Bedrock resources for you in this repo. You must create or locate them before you can finish the deployment inputs:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`

### Option A: AWS CLI or SDK path
### Option B: AWS Console path
```

Expected: the revised section no longer claims these steps are console-only.

- [ ] **Step 5: Fix the S3/KB ordering problem in the deployment sequence**

Rewrite the sequencing text so the document explicitly explains that the data source must point to a real S3 location and that KB document upload must happen before ingestion.

Add copy with this meaning:

```md
Before you create the Bedrock data source, decide which S3 bucket path it will target.
If you want the data source to point at the Terraform-managed knowledge-base bucket, document that this requires a deployment sequence where the bucket exists before the data source is finalized.
The knowledge-base upload step must finish before you trigger ingestion.
```

Expected: the logical conflict between “create data source” and “Terraform creates the bucket later” is explicitly called out instead of hidden.

### Task 3: Finish the back half of `docs/aws.md`

**Files:**
- Modify: `docs/aws.md`
- Reference: `infra/terraform/compute.tf`
- Reference: `infra/terraform/outputs.tf`
- Reference: `backend/scripts/load_structured_data.py`
- Reference: `backend/src/hexarag_api/config.py`
- Reference: `backend/src/monitoring_api/main.py`
- Reference: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add a dedicated “Current repo limitations and caveats” section**

Create a standalone section before troubleshooting with bullets derived from the current repo state.

Use content in this pattern:

```md
## Current repo limitations and caveats
- CloudFront and the frontend bucket are provisioned, but the repo does not currently show the S3 bucket policy wiring normally required for private OAC-backed access.
- The frontend build must use `VITE_API_BASE_URL`; otherwise it falls back to `http://localhost:8000`.
- The backend default allowed origin is `http://localhost:5173`, so deployed browser access may require additional origin configuration.
- The current structured-data loader only loads `monthly_costs.csv`; it does not populate every structured dataset described in `W4/data_package/README.md`.
- The monitoring API routes in Terraform currently expose `/services` and `/metrics/{service_name}` only.
```

Expected: the runbook clearly separates “known repo limits” from “unexpected failure.”

- [ ] **Step 2: Rewrite the structured-data step so it matches the actual loader scope**

Replace any wording that implies the loader imports all structured datasets.

Write the step so it says:

```md
## Step 19: Load structured historical data if needed

The current repo loader imports `monthly_costs.csv` into `monthly_costs`.
It does not fully populate every structured dataset described in the W4 package.
Confirm the target database schema and connection settings before running the loader against AWS-hosted PostgreSQL.
```

Expected: Step 19 becomes precise and no longer overclaims capability.

- [ ] **Step 3: Rewrite the verification steps to separate infrastructure, Bedrock/data, and product checks**

Refactor the final verification area into three blocks with headings like these:

```md
## Infrastructure verification
## Bedrock and data verification
## Browser and product verification
```

Make sure the checks explicitly cover:

```text
- backend_api_url responds on POST /chat
- monitoring_api_url responds on GET /services
- KB files are uploaded before sync and the ingestion job completes
- frontend assets are built with the deployed API URL and uploaded to the frontend bucket
- the browser renders the chat UI, citations, and right-side inspection console
```

Expected: the runbook stops mixing resource checks with end-user behavior checks.

- [ ] **Step 4: Tighten the output and frontend URL caveat language**

Revise the Terraform outputs section so it accurately states that `outputs.tf` does not expose the CloudFront domain.

Use copy in this pattern:

```md
The current Terraform outputs expose the backend API URL, monitoring API URL, frontend bucket name, knowledge-base bucket name, session table name, and PostgreSQL endpoint.
They do not expose the CloudFront distribution domain, so you must retrieve that separately until Terraform outputs are extended.
```

Expected: the output section matches `infra/terraform/outputs.tf` exactly.

- [ ] **Step 5: Add a short cross-link to the functionality tracker**

Near the end of `docs/aws.md`, add a sentence pointing readers to `docs/app-functionality.md` for capability-level tracking.

Use this exact sentence:

```md
For the current product-capability inventory, partial wiring notes, and Bedrock mapping checklist, see `docs/app-functionality.md`.
```

Expected: deployment readers can discover the separate capability tracker without turning `docs/aws.md` into a product-status document.

### Task 4: Create `docs/app-functionality.md`

**Files:**
- Create: `docs/app-functionality.md`
- Reference: `docs/requirements.md`
- Reference: `frontend/src/types/chat.ts`
- Reference: `frontend/src/features/chat/ChatPage.tsx`
- Reference: `frontend/src/features/trace/TracePanel.tsx`
- Reference: `frontend/src/features/chat/useChatSession.ts`
- Reference: `backend/src/monitoring_api/main.py`
- Reference: `backend/scripts/load_structured_data.py`
- Reference: `backend/scripts/upload_knowledge_base.py`
- Reference: `backend/scripts/sync_knowledge_base.py`
- Reference: `W4/data_package/README.md`

- [ ] **Step 1: Write the document header, purpose, and status vocabulary**

Start the new file with this structure:

```md
# HexaRAG App Functionality Tracker

This document tracks all expected app capabilities across frontend behavior, backend responses, tool/data integrations, observability, memory, and deployment-dependent runtime behavior.

It is the source of truth for:
- what the product is expected to do
- what is currently working, partial, mocked, unwired, or missing
- which Bedrock-side behaviors each capability will eventually require

## Status vocabulary
- `working` — the expected capability is present and wired through the current app flow.
- `partial` — some of the capability works, but key behavior or coverage is incomplete.
- `mocked` — the UI or docs show the capability using non-production data or a static preview path.
- `unwired` — pieces exist, but the full end-to-end product behavior is not connected.
- `missing` — the capability is expected but not currently implemented.
```

Expected: the tracker opens with a stable vocabulary that later rows can reuse consistently.

- [ ] **Step 2: Add narrative overview sections by product area**

Create short overview sections for these areas:

```md
## Chat experience
## Citations and grounding
## Inspection console
## Tool-backed historical and live answers
## Session memory and follow-up continuity
## Degraded-mode and uncertainty behavior
## Deployment and runtime dependencies
```

Each section should contain 2-5 sentences describing the expected behavior, the current repo state, and the most important implementation gap if one exists.

Expected: a reader can understand the product surface without reading the matrix first.

- [ ] **Step 3: Add the functionality status matrix with fixed columns**

Create a markdown table with these columns in this order:

```md
| Area | Functionality | Expected behavior | User surface | Backend or tool dependency | Current state | Current implementation notes | Known gap or blocker | Bedrock agent mapping | Phase or priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Expected: the document has a stable matrix shape before you start filling rows.

- [ ] **Step 4: Populate the matrix with the first capability group: chat, session, and trace basics**

Add rows for at least these capabilities and assign a status grounded in the current repo:

```text
- Freeform chat submit
- Conversation history rendering
- Sample question insertion
- Per-response trace selection
- Session continuity via a stable session id
- Error-state rendering in the inspection console
- Observability tab rendering
- Thinking process tab rendering
```

Use Bedrock mapping notes such as:

```text
- prompt orchestration
- session memory window
- UI-facing trace shaping
- graceful error propagation
```

Expected: the matrix starts with the core user loop before moving into citations and tools.

- [ ] **Step 5: Populate the matrix with citations, grounding, and explanation capabilities**

Add rows for at least these capabilities:

```text
- Inline numbered citations in answer text
- Referenced document list per assistant response
- Citation detail modal
- Source metadata display expectations
- Grounding notes in the inspection console
- Contradiction handling visibility
- Uncertainty or degraded-mode messaging
```

Use Bedrock mapping notes such as:

```text
- KB retrieval
- source metadata capture
- contradiction resolution policy
- grounding summary generation
- uncertainty signaling
```

Expected: the matrix shows the full answer-explainability surface expected by the requirements.

### Task 5: Finish `docs/app-functionality.md` and update repo tracking

**Files:**
- Create: `docs/app-functionality.md`
- Modify: `TASKS.md`
- Reference: `docs/aws.md`
- Reference: `backend/src/monitoring_api/main.py`
- Reference: `backend/scripts/load_structured_data.py`
- Reference: `W4/data_package/README.md`

- [ ] **Step 1: Populate the matrix with tool/data and monitoring capabilities**

Add rows for at least these capabilities:

```text
- List services answers
- Live metrics answers
- Historical monthly cost answers
- Incident history answers
- SLA target answers
- Daily-metric historical answers
- Multi-source answers that mix retrieval, structured data, and live data
- Monitoring API surface exposed by the deployed repo
```

Use current-state labels that match the repo instead of the requirements alone. For example, mark rows as `partial`, `unwired`, or `missing` when the repo does not yet expose the full W4 capability.

Use Bedrock mapping notes such as:

```text
- live monitoring tool use
- structured historical data tool use
- multi-tool orchestration
- current-vs-historical answer framing
```

Expected: the tracker makes the gap between W4 expectations and current implementation explicit.

- [ ] **Step 2: Add deployment- and runtime-dependent capability rows**

Add rows covering:

```text
- Frontend build-time API base URL configuration
- Deployed frontend/browser CORS compatibility
- KB document upload dependency
- KB ingestion trigger dependency
- Scheduled KB sync readiness
- AWS output discoverability for operators
```

Use Bedrock mapping notes only where a capability actually depends on Bedrock. For deployment-only rows, say `n/a`.

Expected: the tracker captures non-UI conditions that still affect whether product capabilities are usable.

- [ ] **Step 3: Add the two explicit summary sections for partial wiring**

After the matrix, add these sections:

```md
## Frontend features present but not fully wired
## Backend or tooling capabilities present but not fully surfaced
```

Under each heading, write short bullet summaries derived from the matrix, for example:

```md
- The UI supports inline citations, citation details, and inspection tabs, but the completeness of those views still depends on the backend trace payload.
- The monitoring deployment exposes only `/services` and `/metrics/{service_name}` today, while the W4 package describes a broader live-monitoring surface.
- The structured-data loader currently imports monthly costs only, so exact numeric support is narrower than the full W4 structured dataset.
```

Expected: a reader can scan the biggest integration gaps without reading every matrix row.

- [ ] **Step 4: Cross-link the tracker back to the deployment guide**

Add this sentence near the top or bottom of `docs/app-functionality.md`:

```md
For the AWS deployment runbook and current infrastructure caveats, see `docs/aws.md`.
```

Expected: the two docs point to each other without merging responsibilities.

- [ ] **Step 5: Update `TASKS.md` so tracking matches the new documentation work**

Make these edits:

```md
- Add `docs/superpowers/plans/2026-05-07-aws-docs-and-functionality-tracker.md` to the Plan Index with a short description.
- Add `docs/app-functionality.md` to the docs/tracking note where appropriate if the repo now treats it as a required review target for capability tracking.
```

Expected: the repo’s task tracker acknowledges the new plan and the new capability-tracking doc.

### Task 6: Verify the documentation changes before claiming completion

**Files:**
- Modify: `docs/aws.md`
- Create: `docs/app-functionality.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Review the final diff for the three documentation files only**

Run:

```bash
git diff -- docs/aws.md docs/app-functionality.md TASKS.md
```

Expected: the diff shows only the intended documentation changes and no unrelated file edits.

- [ ] **Step 2: Verify the new docs contain the required phrases and sections**

Check for these exact headings or phrases in the final docs:

```text
- docs/aws.md contains “Current deployment model”.
- docs/aws.md contains “Current repo limitations and caveats”.
- docs/aws.md states that KB upload must happen before ingestion.
- docs/aws.md describes Bedrock setup as CLI or Console, not Console only.
- docs/app-functionality.md contains “## Status vocabulary”.
- docs/app-functionality.md contains the matrix header with “Bedrock agent mapping”.
- docs/app-functionality.md contains “## Frontend features present but not fully wired”.
- docs/app-functionality.md contains “## Backend or tooling capabilities present but not fully surfaced”.
```

Expected: every required structure from the approved design is present in the saved docs.

- [ ] **Step 3: Re-check factual alignment against the source files**

Re-read these references after editing:

```text
- infra/terraform/outputs.tf
- infra/terraform/storage.tf
- infra/terraform/compute.tf
- backend/scripts/load_structured_data.py
- backend/src/monitoring_api/main.py
- frontend/src/lib/api.ts
```

Expected: no sentence in the docs contradicts the current repo state for outputs, CloudFront/S3 wiring, monitoring routes, structured-data loading, or frontend API configuration.

- [ ] **Step 4: Stop after documentation verification and do not claim infra fixes**

Before reporting completion, make sure the summary says only that documentation and tracking were updated.

Use this completion language:

```text
Updated docs/aws.md, added docs/app-functionality.md, and refreshed TASKS.md so the deployment runbook and capability tracking now match the current repo state. No Terraform, backend, or frontend behavior was changed in this task.
```

Expected: the implementation report stays honest about the scope.
