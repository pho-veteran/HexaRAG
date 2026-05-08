# AWS Deployment Tracking

## Purpose
This file records the AWS deployment trace for HexaRAG: Bedrock identifiers, Terraform inputs, deployed resource identifiers, environment wiring, outputs, and verification notes.

## Deployment Session
- Date: 2026-05-08
- Operator: Claude Code with user-authorized AWS CLI session
- Region target: us-east-1
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
- Agent runtime candidates: none returned by `aws bedrock-agentcore-control list-agent-runtimes --region us-east-1`
- Selected knowledge base ID: `LGJRICMIJL`
- Selected data source ID: `WYBIHCKLOV`
- Selected agent ID: `SU1Q1YZRHP`
- Selected agent alias ID: `TSTALIASID`
- Selected agent ARN: `arn:aws:bedrock:us-east-1:274836647176:agent/SU1Q1YZRHP`
- Selected agent role ARN: `arn:aws:iam::274836647176:role/service-role/hexarag-bedrock-agent-role-dev`
- Selected agent name: `hexarag-bedrock-agent-dev`
- User decision: create or supply the missing Bedrock resources in this session.
- Naming rule: use the prefix `hexarag-` for workshop-account resource tracking.
- Initial blocker: no AgentCore runtime existed in `us-east-1`, so the original deployment path could not proceed.
- Repo evidence at blocker time:
  - `backend/src/hexarag_api/services/agent_runtime.py` only invoked an existing runtime via `boto3.client('bedrock-agentcore').invoke_agent_runtime(...)`.
  - `backend/Dockerfile` built the FastAPI backend container for local/dev packaging, not an AgentCore runtime artifact.
  - `infra/terraform/variables.tf` and `infra/terraform/compute.tf` consumed `agent_runtime_arn` as an external input and passed it into the backend Lambda environment.
  - `docs/aws.md` explicitly stated this repo did not create Bedrock resources directly.
- Root-cause conclusion at blocker time: this was a real missing Bedrock runtime resource, not just a missing local identifier.
- Follow-up resolution: the checked-in backend and Terraform wiring were migrated from AgentCore to Bedrock Agents, so deployment now depends on external `agent_id` and `agent_alias_id` instead of an AgentCore runtime ARN.

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
- Backend runtime adapter switched from `bedrock-agentcore` to `bedrock-agent-runtime` `InvokeAgent`.
- Backend settings and Lambda env contract switched from `agent_runtime_arn` to `agent_id` and `agent_alias_id`.
- Terraform IAM switched from `bedrock:InvokeAgentRuntime` to `bedrock:InvokeAgent`.
- Focused backend verification: `docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py tests/services/test_chat_service.py tests/api/test_chat_contract.py -q` → passed (`10 passed`).
- Terraform formatting verification: `terraform fmt -check` from `infra/terraform` → passed.
- Terraform validation: `terraform validate` from `infra/terraform` → passed.

## Step 3: Artifact packaging and Terraform outputs
- `backend.zip`: `infra/terraform/backend.zip`
- `monitoring.zip`: `infra/terraform/monitoring.zip`
- `kb-sync.zip`: `infra/terraform/kb-sync.zip`
- First Terraform apply blockers and fixes:
  - RDS `engine_version = "16.3"` failed in `us-east-1` because AWS no longer offers that exact Postgres version; updated to `16.13` after checking `aws rds describe-db-engine-versions`.
  - Lambda creation rejected explicit `AWS_REGION` environment variables for the sync function, and the backend Lambda would have hit the same reserved-key restriction; removed explicit `AWS_REGION` env injection from Terraform and relied on Lambda's built-in runtime environment.
  - EventBridge Scheduler creation failed because the schedule target reused the Lambda execution role, which is not assumable by `scheduler.amazonaws.com`; replaced it with a dedicated scheduler invoke role.
- Post-apply blockers and fixes:
  - Monitoring API `GET /services` initially returned HTTP 500 because the deployed `monitoring.zip` was missing the FastAPI transitive dependency `annotated_doc`; fixed with a failing packaging regression test, `COMMON_WEB_DEPENDENCIES += ('annotated_doc*',)`, artifact rebuild, and Lambda redeploy.
  - Backend Lambda then failed with the same `annotated_doc` import error and, after redeploy, a second `Runtime.ImportModuleError: No module named 'dotenv'`; fixed with a second failing packaging regression test, `COMMON_WEB_DEPENDENCIES += ('dotenv*',)`, artifact rebuild, and Lambda redeploy.
  - CloudFront initially returned `AccessDenied` because the frontend bucket lacked a policy granting the distribution's OAC access to `s3:GetObject`; fixed in `infra/terraform/storage.tf` by attaching a bucket policy scoped to the frontend distribution ARN and re-applying Terraform.
  - Bedrock tool-backed `/chat` responses initially degraded to the fallback contract because the agent was configured with the on-demand Anthropic model ID `anthropic.claude-3-5-haiku-20241022-v1:0`, which Bedrock rejected for agent invocation; fixed by switching the agent model to the inference profile `us.anthropic.claude-3-5-haiku-20241022-v1:0` and running `prepare-agent`.
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
  - scheduler role: `arn:aws:iam::274836647176:role/hexarag-dev-sync-scheduler`

## Step 4: Frontend publish
- Initial build API base URL: `https://subsponqyl.execute-api.us-east-1.amazonaws.com/`
- Initial S3 sync result: `aws s3 sync frontend/dist s3://hexarag-dev-frontend --delete` completed successfully.
- Initial CloudFront invalidation ID: `I7ANIE21D3Q1VI5ZE5HIHDHBK1` completed.
- Initial frontend delivery verification: `https://d1utyuhmju4jzn.cloudfront.net/` and `/index.html` returned HTTP 200 after the bucket-policy fix, and the deployed bundle asset `/assets/index-DQCUaPLZ.js` was retrievable.
- Follow-up browser root cause: the first deployed bundle still embedded `http://backend:8000`, which caused mixed-content failures from the HTTPS CloudFront page.
- Frontend config fix: `docker-compose.yml` now scopes `VITE_API_BASE_URL=http://backend:8000` to the frontend dev-server command instead of the service-level environment so production `docker compose run` builds do not inherit the Docker-only backend URL.
- Rebuild command that produced the fixed bundle: `docker compose run --rm -e VITE_API_BASE_URL=https://subsponqyl.execute-api.us-east-1.amazonaws.com frontend sh -lc 'node node_modules/vite/bin/vite.js build'`.
- Fixed bundle verification before publish: compiled asset `frontend/dist/assets/index-Dz3dBiUM.js` contained `https://subsponqyl.execute-api.us-east-1.amazonaws.com` and no longer contained `http://backend:8000` or `http://localhost:8000`.
- Fixed S3 sync result: `aws s3 sync frontend/dist s3://hexarag-dev-frontend --delete` uploaded `/assets/index-Dz3dBiUM.js`, `/assets/index-BrNcw9vS.css`, `index.html`, `favicon.svg`, and `icons.svg`, and deleted `/assets/index-DQCUaPLZ.js`.
- Fixed CloudFront invalidation ID: `I59C00NAO0ZQQF0ISHDFJNXAUZ` created.

## Step 5: Knowledge base upload and ingestion
- KB upload result: knowledge-base markdown files uploaded to `s3://hexarag-dev-knowledge-base` before manual sync.
- Sync script result: `docker compose run --rm backend uv run python scripts/sync_knowledge_base.py` triggered a Bedrock ingestion job against `LGJRICMIJL` / `WYBIHCKLOV`.
- Ingestion job ID: `GVWIY5CMFO`
- Ingestion verification: `COMPLETE`

## Step 6: End-to-end verification
- Backend `/chat` verification:
  - Tool-backed question succeeded: `What is the p99 latency for PaymentGW?` returned a live metric answer and a successful `/get-metrics` tool trace.
  - Follow-up memory check succeeded: `What about its error rate?` reused the prior turn through `memory_window`.
  - Retrieval-backed question succeeded: `What is HexaRAG?` returned a grounded answer with the note `Retrieved 4 references from LGJRICMIJL.`
  - Open caveat: the retrieval-backed response still surfaced empty `citations` and `inline_citations`, so deployed citation normalization remains incomplete even though retrieval is happening.
- Monitoring `/services` verification: `https://9nm3agbi64.execute-api.us-east-1.amazonaws.com/services` returned HTTP 200 with six services after the packaging fix.
- Monitoring `/metrics/PaymentGW` verification: `https://9nm3agbi64.execute-api.us-east-1.amazonaws.com/metrics/PaymentGW` returned HTTP 200 JSON.
- Browser verification URL: `https://d1utyuhmju4jzn.cloudfront.net`
- Browser verification notes: headless browser verification now confirms the deployed page submits to `https://subsponqyl.execute-api.us-east-1.amazonaws.com/chat`, the browser preflight succeeds with HTTP 204, the live `POST /chat` resolves with HTTP 200, and the UI renders an assistant response plus inspection-console sections for Sources, Tool calls, Memory, and Grounding. The earlier mixed-content failure was eliminated by rebuilding and republishing the frontend bundle with the correct HTTPS API base URL.

## Notes
- This file is intentionally deployment-focused and may contain sensitive identifiers. Database passwords are redacted here even if materialized in local untracked deployment inputs.
