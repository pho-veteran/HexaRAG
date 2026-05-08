# AWS Deployment Tracking

## Purpose
This file records the AWS deployment trace for HexaRAG: Bedrock identifiers, Terraform inputs, deployed resource identifiers, environment wiring, outputs, and verification notes.

## Deployment Session
- Date: 2026-05-08
- Operator: Claude Code with user-authorized AWS CLI session
- Region target: `us-east-1`
- Plan: `docs/superpowers/plans/2026-05-08-aws-deploy-readiness-and-deployment.md`

## Step 1: AWS identity and Bedrock prerequisites
- Caller identity: `arn:aws:iam::274836647176:user/vinhIAM` (account `274836647176`)
- AWS configured region: `us-east-1`
- Knowledge base candidates:
  - `RTKQCDNQ98` — `geek-nhan`
  - `RLPMAUADOW` — `GeekBrain-KB-test`
  - `LGJRICMIJL` — `geekbrain-w4-kb-jb6`
  - `FQCQZXSBWV` — `knowledge-base-thong`
  - `CIQQEZ9QZN` — `knowledge-base-group6`
- Selected knowledge base ID: `LGJRICMIJL`
- Selected data source ID: `WYBIHCKLOV`
- Selected agent ID: `SU1Q1YZRHP`
- Selected agent alias ID: `TSTALIASID`
- Selected agent ARN: `arn:aws:bedrock:us-east-1:274836647176:agent/SU1Q1YZRHP`
- Selected agent role ARN: `arn:aws:iam::274836647176:role/service-role/hexarag-bedrock-agent-role-dev`
- Selected agent name: `hexarag-bedrock-agent-dev`
- Naming rule used during deployment: `hexarag-*`
- Root-cause conclusion from the original deployment blocker: AgentCore runtime resources were absent, so the repo was migrated to Bedrock Agents instead of waiting on a missing AgentCore path.

## Step 2: Terraform deployment inputs
- `aws_region`: `us-east-1`
- `project_name`: `hexarag`
- `environment`: `dev`
- `database_password`: generated locally and redacted from this file
- `knowledge_base_id`: `LGJRICMIJL`
- `knowledge_base_data_source_id`: `WYBIHCKLOV`
- `agent_id`: `SU1Q1YZRHP`
- `agent_alias_id`: `TSTALIASID`

## Migration verification
- Backend runtime adapter switched from AgentCore to `bedrock-agent-runtime` `InvokeAgent`.
- Backend settings and Lambda env contract switched from `agent_runtime_arn` to `agent_id` and `agent_alias_id`.
- Terraform IAM switched from `bedrock:InvokeAgentRuntime` to `bedrock:InvokeAgent`.
- Focused backend verification during migration: `docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py tests/services/test_chat_service.py tests/api/test_chat_contract.py -q` → passed.
- Terraform formatting verification: `terraform fmt -check` → passed.
- Terraform validation: `terraform validate` → passed.

## Step 3: Artifact packaging and Terraform outputs
- Lambda artifacts:
  - `infra/terraform/backend.zip`
  - `infra/terraform/monitoring.zip`
  - `infra/terraform/kb-sync.zip`
- First Terraform apply blockers and fixes:
  - RDS `engine_version = "16.3"` was no longer available in `us-east-1`; updated to `16.13`.
  - Explicit `AWS_REGION` Lambda env injection used a reserved key; removed from Terraform.
  - EventBridge Scheduler needed a dedicated invoke role instead of reusing the Lambda execution role.
- Post-apply blockers and fixes:
  - Monitoring API `GET /services` initially failed because packaged dependencies missed `annotated_doc`; fixed in Lambda packaging and redeployed.
  - Backend Lambda then failed on `annotated_doc` and later `dotenv`; both were added to packaging coverage and redeployed.
  - CloudFront initially returned `AccessDenied`; fixed with an OAC-scoped frontend bucket policy.
  - Bedrock-backed `/chat` initially degraded because the agent used an on-demand Anthropic model ID that Bedrock Agents rejected; fixed by switching the agent to an inference-profile style model identifier and re-running `prepare-agent`.
- Terraform outputs:
  - `backend_api_url`: `https://subsponqyl.execute-api.us-east-1.amazonaws.com/`
  - `monitoring_api_url`: `https://9nm3agbi64.execute-api.us-east-1.amazonaws.com/`
  - `frontend_bucket_name`: `hexarag-dev-frontend`
  - `knowledge_base_bucket_name`: `hexarag-dev-knowledge-base`
  - `cloudfront_domain_name`: `d1utyuhmju4jzn.cloudfront.net`
  - `cloudfront_distribution_id`: `E34QQXWL7Y7UG5`
  - `session_table_name`: `hexarag-dev-sessions`
  - `postgres_endpoint`: `hexarag-dev-postgres.chbgbzedm6sx.us-east-1.rds.amazonaws.com`
- Lambda ARNs:
  - backend: `arn:aws:lambda:us-east-1:274836647176:function:hexarag-dev-backend`
  - monitoring: `arn:aws:lambda:us-east-1:274836647176:function:hexarag-dev-monitoring`
  - kb-sync: `arn:aws:lambda:us-east-1:274836647176:function:hexarag-dev-kb-sync`
- Scheduler role ARN: `arn:aws:iam::274836647176:role/hexarag-dev-sync-scheduler`

## Step 4: Frontend publish
- The first deployed bundle baked `http://backend:8000` into the browser build and caused mixed-content failures from the HTTPS CloudFront frontend.
- Fix applied: scope the Docker-local `VITE_API_BASE_URL=http://backend:8000` to the dev server only and build production assets with an explicit HTTPS backend API URL.
- Verified fixed build command:
  - `docker compose run --rm -e VITE_API_BASE_URL=https://subsponqyl.execute-api.us-east-1.amazonaws.com frontend sh -lc 'node node_modules/vite/bin/vite.js build'`
- Fixed bundle verification before publish:
  - built asset contained `https://subsponqyl.execute-api.us-east-1.amazonaws.com`
  - built asset no longer contained `http://backend:8000`
  - built asset no longer contained `http://localhost:8000`
- Frontend publish completed with S3 sync and CloudFront invalidation.

## Step 5: Knowledge base upload and ingestion
- Knowledge-base markdown files uploaded to `s3://hexarag-dev-knowledge-base` before manual sync.
- Sync command triggered ingestion for `LGJRICMIJL` / `WYBIHCKLOV`.
- Ingestion job ID: `GVWIY5CMFO`
- Ingestion status: `COMPLETE`

## Step 6: Deployed behavior verification
- Backend `/chat` verification:
  - tool-backed question succeeded
  - follow-up memory question succeeded and reused `memory_window`
  - retrieval-backed question succeeded
  - open caveat: retrieval-backed deployed answers can still return empty normalized `citations` and `inline_citations` even when retrieval happened
- Monitoring verification:
  - `GET https://9nm3agbi64.execute-api.us-east-1.amazonaws.com/services` → HTTP 200
  - `GET https://9nm3agbi64.execute-api.us-east-1.amazonaws.com/metrics/PaymentGW` → HTTP 200
- Browser verification URL: `https://d1utyuhmju4jzn.cloudfront.net`
- Browser verification result:
  - browser preflight to the backend succeeded
  - browser `POST /chat` succeeded with HTTP 200
  - the UI rendered an assistant response and inspection-console sections

## Step 6B: Published CloudFront chat-hang investigation and fix
- User-reported symptom: the published CloudFront app loaded, Send enabled, and the browser issued `POST https://subsponqyl.execute-api.us-east-1.amazonaws.com/chat`, but the UI stayed on `Sending...`.
- Root-cause investigation findings:
  - direct deployed `/chat` requests returned HTTP 200
  - backend Lambda logs showed successful request completion rather than a stuck runtime
  - browser preflight and API CORS headers were valid for `https://d1utyuhmju4jzn.cloudfront.net`
  - the published site was serving older frontend/backend behavior than the local repo state
- Actual root cause: the current frontend could not be rebuilt for deployment because `frontend/src/features/chat/ChatPage.tsx` was corrupted by pasted transcript/tool-output text, so production remained on an older bundle.
- Frontend build blocker evidence:
  - Vite parse failure: `Expected a semicolon or an implicit semicolon after a statement, but found none`
  - file: `src/features/chat/ChatPage.tsx`
- Fix applied:
  - repaired `frontend/src/features/chat/ChatPage.tsx` to valid TSX
  - reran the frontend build successfully
  - repackaged and redeployed the backend Lambda so the latest runtime/trace slice was also published
- First republish after the TSX fix still failed in-browser:
  - the deployed bundle called `http://localhost:8000/chat`
  - browser fetch failed with `Failed to fetch`
- Root cause of that republish failure: setting `VITE_API_BASE_URL` in host PowerShell did not reliably propagate into `docker compose run`, so the production build fell back to localhost.
- Corrected production frontend build command:
  - `docker compose run --rm -e VITE_API_BASE_URL=https://subsponqyl.execute-api.us-east-1.amazonaws.com frontend sh -lc 'node node_modules/vite/bin/vite.js build'`
- Final publish evidence:
  - CloudFront invalidation after the bad republish: `I61G5IQ6215GGRP4N3UA72CLGH` at `2026-05-08T04:53:02Z`
  - CloudFront invalidation after the corrected republish: `I4KEMXYMM5YTCHNAV8B0VS6SG1` at `2026-05-08T04:54:56Z`
  - published bundle observed by browser automation: `index-HCsdPPUw.js`
- Final published browser verification after the corrected republish:
  - the page fetched `https://subsponqyl.execute-api.us-east-1.amazonaws.com/chat`
  - browser `POST /chat` completed with HTTP 200
  - assistant response rendered successfully
  - inspection console sections were visible: `Sources`, `Tool calls`, `Memory`, `Grounding`
  - no visible frontend error state remained

## Step 6C: Production 500 and frontend crash follow-up
- New user-reported production symptom after the earlier publish fix:
  - browser showed a failed resource with HTTP 500
  - published bundle threw `Cannot read properties of undefined (reading 'sessionId')`
- Root-cause investigation findings:
  - direct `POST https://subsponqyl.execute-api.us-east-1.amazonaws.com/chat` returned HTTP 500 with plain-text body `Internal Server Error`
  - backend Lambda logs showed the failure happened before Bedrock invocation in `SessionStore.load_recent_turns()`
  - exact exception: DynamoDB `ResourceNotFoundException` for `SESSION_TABLE_NAME=hexarag-dev-sessions`
  - Lambda configuration still pointed at `hexarag-dev-sessions`, but the table no longer existed in the account at the time of failure
- Infrastructure fix applied:
  - recreated DynamoDB table `hexarag-dev-sessions`
  - table ARN: `arn:aws:dynamodb:us-east-1:274836647176:table/hexarag-dev-sessions`
  - after table restoration, direct deployed `/chat` returned HTTP 200 again
- Secondary frontend bug confirmed:
  - `frontend/src/lib/api.ts` assumed every failed response was JSON containing `trace.request.session_id`
  - plain-text or malformed 500 responses could therefore crash the UI while rendering the error state
- Code hardening applied:
  - added a focused frontend regression test in `frontend/src/features/chat/ChatPage.test.tsx` for plain-text HTTP 500 handling
  - updated `frontend/src/lib/api.ts` to preserve the success contract, preserve structured JSON error rendering, and safely fall back to the original request values plus HTTP status text when the error response is non-JSON or missing `trace.request`
- Focused verification for this hotfix:
  - `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run` → exit code `0`
  - `docker compose run --rm -e VITE_API_BASE_URL=https://subsponqyl.execute-api.us-east-1.amazonaws.com frontend sh -lc 'npm run build'` → exit code `0`
  - direct deployed `/chat` verification after table restore → HTTP `200`
- Final republish for the frontend hardening:
  - uploaded rebuilt assets to `s3://hexarag-dev-frontend`
  - CloudFront invalidation ID: `ID4T227U5UIMC19X5KIFK5ONGW`
  - invalidation status: `Completed`
  - published CloudFront HTML still references `index-HCsdPPUw.js`, matching the local rebuilt `frontend/dist/index.html`

## Step 7: Runtime contract and product-trace follow-up
This repo slice added explicit runtime, reasoning, and session-lifetime behavior that now matters for deployment verification too.

### Backend contract changes now checked in
- The backend owns a reusable instruction contract in `backend/src/hexarag_api/services/agent_runtime.py`.
- The Bedrock input now explicitly instructs the model to:
  - use recent conversation context only when relevant
  - answer from grounded evidence
  - prefer the newest valid source when sources disagree
  - keep answers concise
  - surface uncertainty when evidence is incomplete
- The normalized trace now includes:
  - `runtime.mode`
  - `runtime.provider`
  - `runtime.region`
  - `runtime.agent_id`
  - `runtime.agent_alias_id`
  - `runtime.model` when exposed by Bedrock trace metadata
  - reasoning summaries for evidence types, source selection, tool basis, memory use, contradiction handling, and caveats

### Frontend contract changes now checked in
- The frontend maps the expanded trace contract centrally in `frontend/src/lib/api.ts`.
- The Thinking tab now renders synthesis-oriented steps instead of duplicating source inventory.
- The frontend session ID is now ephemeral per page load:
  - stable inside one page instance
  - regenerated on refresh or remount
  - not persisted in localStorage, cookies, or the URL

### Focused verification for this slice
- Backend focused verification:
  - `docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py tests/services/test_chat_service.py tests/api/test_chat_contract.py -q`
  - result: passed (`14 passed` in the latest local run)
- Frontend focused verification:
  - `docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run`
  - result: passed in Docker in the latest local verification

## Step 8: Claude Haiku 4.5 readiness note
- Current repo readiness: partial.
- Current deployment fact: the existing Bedrock Agent path already required an inference-profile style model identifier for successful Anthropic agent invocation.
- Current AWS documentation check: Amazon Bedrock now documents direct runtime access for `anthropic.claude-haiku-4-5-20251001-v1:0`.
- Remaining gap: this repo uses Bedrock Agents, not direct `bedrock-runtime` calls, so Haiku 4.5 cannot be claimed ready for HexaRAG until the exact Bedrock Agent configuration path is verified in `us-east-1` and the deployed browser `/chat` flow is re-tested after the switch.

## Current notable caveats
- Bedrock resource IDs remain external inputs rather than Terraform-managed resources in this repo.
- Browser success depends on both Lambda-side origin allowlisting and API Gateway HTTP API CORS configuration.
- Retrieval-backed deployed responses still have a citation-normalization gap for some answers.
- Structured-data coverage is still narrower than the full W4 package.
- Monitoring route coverage is still narrower than the full live-data surface expected by W4.
