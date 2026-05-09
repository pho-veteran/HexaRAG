# HexaRAG AWS Deployment Guide

This guide describes the current AWS deployment path for HexaRAG as the repository exists today.

It assumes:
- AWS region `us-east-1`
- resource prefix `hexarag-`
- AWS-generated URLs
- Docker Compose for all local build, packaging, and test commands

## Current deployment shape

The checked-in deployment targets:
- S3 + CloudFront for the frontend
- API Gateway HTTP API + Lambda for the chat backend
- API Gateway HTTP API + Lambda for the monitoring API
- PostgreSQL for structured historical data
- DynamoDB for recent session memory
- S3-backed Bedrock Knowledge Base source content
- a scheduled Lambda for knowledge-base sync
- Bedrock Agents for orchestration via externally supplied `agent_id` and `agent_alias_id`

Terraform does not create the Bedrock Knowledge Base, Bedrock data source, Bedrock Agent, or Bedrock Agent alias in this repo. You must supply those identifiers.

## Required local tools

You need:
- AWS CLI
- Terraform
- Docker Desktop
- Git
- this repository cloned locally

Verify them:

```bash
aws --version
terraform version
docker --version
docker compose version
git --version
```

## Configure AWS

```bash
aws configure
aws sts get-caller-identity
aws configure get region
```

Use `us-east-1` and confirm the caller identity before continuing.

## Confirm the repo-local workflow

Do not switch to host-installed Python, Node, or PostgreSQL workflows.

```bash
docker compose run --rm frontend npm run build
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help
```

## Bedrock prerequisites

Before Terraform, create or locate:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_id`
- `agent_alias_id`

Current deployed workshop values recorded in `aws-tracking.md`:
- `knowledge_base_id = LGJRICMIJL`
- `knowledge_base_data_source_id = WYBIHCKLOV`
- `agent_id = SU1Q1YZRHP`
- `agent_alias_id = TSTALIASID`

## Prepare Terraform inputs

Create a real tfvars file from the example:

```powershell
Copy-Item infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Set:

```hcl
aws_region                    = "us-east-1"
project_name                  = "hexarag"
environment                   = "dev"
database_password             = "replace-with-a-real-password"
agent_id                      = "your-agent-id"
agent_alias_id                = "your-agent-alias-id"
knowledge_base_id             = "your-knowledge-base-id"
knowledge_base_data_source_id = "your-data-source-id"
```

## Package Lambda artifacts

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
```

Expected artifacts in `infra/terraform`:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

## Terraform workflow

From `infra/terraform`:

```bash
terraform init
terraform fmt -check
terraform validate
terraform apply
```

After apply, save:

```bash
terraform output backend_api_url
terraform output monitoring_api_url
terraform output frontend_bucket_name
terraform output knowledge_base_bucket_name
terraform output session_table_name
terraform output postgres_endpoint
terraform output cloudfront_domain_name
terraform output cloudfront_distribution_id
```

## Build the frontend for AWS

The frontend uses `VITE_API_BASE_URL` at build time. If you skip it, the bundle falls back to localhost.

For deployment builds, pass the real backend API URL directly into the `docker compose run` container:

```bash
docker compose run --rm -e VITE_API_BASE_URL=https://your-backend-api-url frontend sh -lc 'node node_modules/vite/bin/vite.js build'
```

Do not rely on only setting a host-shell environment variable before `docker compose run`. In this repo, that previously produced a bad published bundle that fell back to `http://localhost:8000`.

Do not rely on the Docker-local frontend service env for production builds either. That path previously baked `http://backend:8000` into the deployed bundle.

## Upload the frontend

```bash
aws s3 sync frontend/dist s3://<frontend-bucket-name> --delete
aws cloudfront create-invalidation --distribution-id <cloudfront-distribution-id> --paths '/*'
```

Then open the CloudFront domain and confirm the app loads.

## Upload and ingest the knowledge base

Upload the markdown documents:

```bash
docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket <knowledge-base-bucket>
```

Trigger ingestion only after upload completes:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py
```

Wait for the ingestion job to complete before trusting retrieval-backed answers.

## Load structured data if needed

The current repo loader imports the W4 structured datasets used by the live audit, including monthly costs, incidents, SLA targets, and daily metrics.

```bash
docker compose run --rm backend uv run python scripts/load_structured_data.py
```

## What the deployed app now exposes

### Runtime/model visibility
The backend now returns explicit runtime metadata in `ChatResponse.message.trace.runtime`, including:
- `mode`
- `provider`
- `region`
- `agent_id`
- `agent_alias_id`
- `model` when the Bedrock trace exposes it

The frontend maps those fields centrally in `frontend/src/lib/api.ts` and uses reasoning-oriented labels in the Thinking tab instead of leaking raw provider details everywhere.

### Backend-owned instruction contract
The backend now owns the instruction contract used for Bedrock Agent invocation. The runtime input explicitly instructs the model to:
- use recent conversation context only when relevant
- answer from grounded evidence
- prefer the newest valid source when sources disagree
- keep the answer concise
- surface uncertainty when evidence is incomplete

That contract lives in `backend/src/hexarag_api/services/agent_runtime.py`, not only in Bedrock-side configuration.

### Thinking tab behavior
The Thinking tab now explains synthesis instead of duplicating the Observability inventory. It can show:
- generated runtime label
- synthesized evidence summary
- selected answer-shaping sources
- applied tool results
- reused recent context
- resolved conflicting evidence
- included caveats

### Session memory behavior
Session memory is now temporary per page load.
- one browser tab keeps a stable generated `session_id` for follow-up turns
- a refresh or new tab gets a new `session_id`
- the frontend does not persist session IDs in localStorage, cookies, or the URL

## Focused verification commands

Backend contract slice:

```bash
docker compose run --rm backend uv run pytest tests/services/test_trace_formatter.py tests/services/test_chat_service.py tests/api/test_chat_contract.py -q
```

Evaluator contract slice:

```bash
docker compose run --rm backend uv run pytest tests/services/test_evaluator_inputs.py tests/services/test_audit_scoring.py -q
```

Live audit harness smoke checks:

```bash
docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://<backend-api-url> --level l1 --mode replay --output /workspace/repo/backend/evaluate_w4_l1_replay.json --limit 3

docker compose run --rm backend uv run python scripts/evaluate_w4.py --api-base-url https://<backend-api-url> --level l5 --mode audit --output /workspace/repo/backend/evaluate_w4_l5_audit.json --limit 1
```

Frontend trace and session slice:

```bash
docker compose run --rm frontend npm run test -- src/features/chat/ChatPage.test.tsx src/features/trace/TracePanel.test.tsx src/features/trace/buildTraceNarrative.test.ts --run
```

Data and monitoring audit slice:

```bash
docker compose run --rm backend uv run pytest tests/services/test_analytics.py tests/monitoring_api/test_monitoring_routes.py -q
```

## Current deployed verification state

Recorded in `aws-tracking.md`:
- monitoring `/services` and `/metrics/PaymentGW` respond successfully
- browser preflight from the CloudFront frontend succeeds
- live `POST /chat` succeeds from the browser
- the deployed UI renders assistant output and inspection-console sections
- retrieval is happening, but deployed citation normalization is still incomplete for some retrieval-backed answers

## Claude Haiku 4.5 readiness

Current repo readiness is partial.

- Amazon Bedrock documentation now includes a model card for `anthropic.claude-haiku-4-5-20251001-v1:0` for direct Bedrock Runtime use.
- This repo currently invokes Bedrock through Bedrock Agents, not direct `bedrock-runtime` calls.
- The deployed agent previously required switching from an on-demand Anthropic model ID to an inference-profile style model identifier for successful agent invocation.
- Because of that agent-specific requirement, Haiku 4.5 should be treated as a deployment verification task, not a doc-only toggle. Before switching, verify that Bedrock Agents in the target region accept the desired Haiku 4.5 identifier for the agent configuration and re-run `prepare-agent` plus browser `/chat` verification.

In short: Haiku 4.5 appears available in Bedrock, but HexaRAG should not claim Bedrock Agent readiness for it until the exact agent configuration path is verified in AWS.

## Known caveats

- Bedrock resource creation is still external to Terraform in this repo.
- The browser path depends on both Lambda-side allowed origins and API Gateway HTTP API CORS configuration.
- If you replace the CloudFront distribution or add a custom frontend domain, update both the backend allowlist and the API Gateway CORS config in Terraform.
- Retrieval-backed deployed responses can still miss normalized citations even when retrieval succeeds.

## Troubleshooting

### Frontend still calls localhost or `http://backend:8000`
Rebuild with an explicit HTTPS `VITE_API_BASE_URL` passed via `docker compose run -e ...`, re-upload `frontend/dist`, and invalidate CloudFront.

### Browser preflight fails
Check both:
- backend allowed origins passed into Lambda
- API Gateway HTTP API `cors_configuration`

### Lambda import errors
Rebuild artifacts with:

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
```

Then verify packaging still includes the required FastAPI runtime dependencies.

### Bedrock-backed chat falls back
Check:
- backend Lambda health first
- correct `AGENT_ID` and `AGENT_ALIAS_ID`
- agent model identifier or inference-profile requirement
- `prepare-agent` after agent changes

## Related files
- `infra/terraform/compute.tf`
- `infra/terraform/outputs.tf`
- `infra/terraform/scheduler.tf`
- `backend/src/hexarag_api/services/agent_runtime.py`
- `backend/src/hexarag_api/services/trace_formatter.py`
- `frontend/src/lib/api.ts`
- `frontend/src/features/chat/useChatSession.ts`
- `frontend/src/features/trace/buildTraceNarrative.ts`
- `aws-tracking.md`
