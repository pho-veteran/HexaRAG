# HexaRAG AWS Deployment Runbook Design

## Goal
Create a beginner-friendly, end-to-end deployment runbook for HexaRAG that assumes no prior AWS deployment experience. The runbook should cover the full path from local prerequisite setup to a working AWS deployment in `us-east-1`, using the app name `hexarag`, AWS-generated URLs only, and the repo’s existing Terraform and Docker Compose workflow.

## Audience
- A beginner operator deploying the app into their own AWS account.
- Someone with admin access to AWS, but limited practical experience with Bedrock, Terraform, Lambda packaging, CloudFront, API Gateway, RDS, and DynamoDB.

## Non-goals
- Custom domains, Route 53, ACM certificate setup, or vanity URLs.
- Re-architecting the deployment to avoid manual Bedrock setup.
- Replacing the repo’s Docker Compose and Terraform workflow with a host-native alternative.

## Source of Truth
The runbook must stay aligned with these repo files:
- `docs/aws.md`
- `docs/local-dev.md`
- `infra/terraform/terraform.tfvars.example`
- `infra/terraform/compute.tf`
- `infra/terraform/storage.tf`
- `infra/terraform/scheduler.tf`
- `infra/terraform/outputs.tf`
- `backend/scripts/upload_knowledge_base.py`
- `backend/scripts/sync_knowledge_base.py`

## Deployment model the runbook describes
The runbook should describe the deployment exactly as the repo is currently shaped:
- Frontend: Vite static assets hosted in S3 and served through CloudFront.
- Backend API: FastAPI packaged as a Lambda behind API Gateway.
- Monitoring API: separate Lambda behind API Gateway for monitoring routes.
- Structured historical data: PostgreSQL.
- Session memory: DynamoDB.
- Knowledge base documents: S3 bucket + Bedrock Knowledge Base.
- Knowledge base ingestion: manual upload plus ingestion trigger, with a scheduled sync Lambda.

## Operator split labels
Every runbook step must be marked with one of these labels:
- **Manual in AWS Console** — the user clicks through AWS themselves.
- **Run locally yourself** — the user runs the exact command locally.
- **Claude can help/run** — Claude can guide or execute the command in-session.
- **Verify manually** — the user checks a URL, console page, log group, or UI behavior before continuing.

The document should use these labels consistently so a beginner always knows whether a step is manual, CLI-driven, or a verification checkpoint.

## Required structure of the runbook

### 1. Prerequisites on the local machine
The runbook should begin with exact prerequisite checks for:
- Docker Desktop with Docker Compose
- Terraform
- AWS CLI
- Git and a shell that can run the repo commands

It should explain that local development and verification in this repo are Docker Compose-first, matching `docs/local-dev.md`.

### 2. AWS credential setup
The runbook should include:
- `aws configure`
- a follow-up identity check using STS
- confirmation that the active region is `us-east-1`
- an explanation of what values the user is entering and why

This section should be labeled mostly **Run locally yourself** and **Verify manually**.

### 3. Manual Bedrock prerequisites
The runbook must explicitly call out that this repo expects the user to provide:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`

These values are consumed by Terraform via `infra/terraform/terraform.tfvars` and then passed into Lambda environment variables.

This section should walk the user through creating or locating:
- a Bedrock Knowledge Base
- a Knowledge Base data source
- an AgentCore runtime

This section should be labeled **Manual in AWS Console** and should tell the user to save all three identifiers before moving on.

### 4. Terraform input preparation
The runbook should explain how to copy `infra/terraform/terraform.tfvars.example` to a real `terraform.tfvars` file and fill in:
- `aws_region`
- `project_name`
- `environment`
- `database_password`
- `agent_runtime_arn`
- `knowledge_base_id`
- `knowledge_base_data_source_id`

Each variable should be explained in plain language. The document should use the approved defaults:
- `aws_region = "us-east-1"`
- `project_name = "hexarag"`

This section should be labeled **Claude can help/run** for file creation and validation, with **Run locally yourself** for any secrets the user prefers to enter personally.

### 5. Lambda packaging checkpoint
The runbook must include a clearly separated packaging stage before Terraform apply.

Reason: Terraform currently references these zip artifacts directly:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

The runbook should not pretend Terraform builds these for the user.

For beginner-friendliness on Windows, the packaging instructions should prefer:
- PowerShell `Compress-Archive`, or
- `7z` if that is simpler for the user

This section should explain:
- which source folders/scripts belong in each zip
- where the zip files must exist relative to `infra/terraform`
- that the user must verify the zip files exist before `terraform apply`

If the implementation later adds an automated packaging script, the runbook can prefer that, but the design must preserve a Windows-native manual fallback.

### 6. Terraform deploy sequence
The runbook should guide the user through the exact deployment flow from `infra/terraform`:
- `terraform init`
- `terraform fmt -check`
- `terraform validate`
- `terraform apply`

The document should explain what each command does in beginner terms and what success looks like.

After apply, the runbook should instruct the user to save these outputs:
- backend API URL
- monitoring API URL
- frontend bucket name
- knowledge base bucket name
- session table name
- PostgreSQL endpoint

Because the current Terraform outputs do not expose a CloudFront URL, the runbook should explicitly note that the frontend access URL may need to be retrieved manually unless Terraform outputs are extended.

### 7. Frontend publish stage
The runbook must treat frontend deployment as its own step after infrastructure creation.

It should cover:
- building the frontend with the repo’s Docker Compose workflow
- uploading the built assets to the Terraform-created frontend S3 bucket
- verifying CloudFront serves the site

This section must clearly explain that “Terraform created the hosting resources” is not the same as “the frontend is live.”

### 8. Post-deploy app setup
The runbook should include:
- uploading knowledge base markdown documents to the KB bucket using `backend/scripts/upload_knowledge_base.py`
- triggering a manual knowledge base ingestion job using `backend/scripts/sync_knowledge_base.py`
- any required structured-data preparation or validation needed by the deployed runtime

This section should use **Claude can help/run** for repo commands and **Verify manually** for checking the resulting AWS state.

### 9. End-to-end verification
The runbook should end with a concrete verification checklist:
- backend API responds
- monitoring API responds
- frontend loads through CloudFront
- chat works
- the observability panel appears and shows trace/citation context as expected
- CloudWatch logs are available for troubleshooting

The guide should separate “command verification” from “browser verification” so a beginner can tell whether the infrastructure is healthy versus whether the product behavior is correct.

### 10. Troubleshooting appendix
The runbook should include a troubleshooting section focused on likely real failures in this repo:
- Bedrock access not enabled or unavailable in the account/region
- missing or misplaced Lambda zip artifacts
- Terraform apply failures
- frontend assets never uploaded, resulting in a blank or stale site
- backend cannot reach PostgreSQL
- wrong `DATABASE_URL` or KB identifiers
- KB upload succeeded but ingestion was never triggered
- deployed URLs exist but the app behavior is still broken

## Tone and formatting requirements for the runbook
The final runbook should read like a checklist, not a theory document.

It should:
- use short sections with numbered steps
- include exact commands where possible
- include expected results after risky or confusing steps
- explicitly say when the user should stop and verify before continuing
- explain terms the first time they appear

## Design decisions approved in brainstorming
- Region: `us-east-1`
- App name: `hexarag`
- URL strategy: AWS-generated URLs only
- Scope: full deployment path through post-deploy verification
- Audience level: complete beginner
- Operational preference: explicitly separate manual tasks from tasks Claude can help drive through AWS CLI, Terraform, or repo commands
- Windows packaging preference: prefer a Windows zip command path such as PowerShell `Compress-Archive` or `7z`

## Open implementation notes to carry into planning
- Decide whether the deployment runbook should live by expanding `docs/aws.md`, or by adding a new beginner-focused deployment document and linking it from `docs/aws.md`.
- Confirm whether the codebase already has a reliable packaging flow for `backend.zip`, `monitoring.zip`, and `kb-sync.zip`; if not, the implementation must document the manual Windows packaging path explicitly.
- Consider adding a Terraform output for the CloudFront domain so the beginner runbook can avoid manual console lookup for the frontend URL.
