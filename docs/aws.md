# HexaRAG AWS Deployment Guide

## Services provisioned
- S3 + CloudFront for the Vite frontend
- API Gateway + Lambda for the FastAPI chat API
- API Gateway + Lambda for the internal monitoring API
- PostgreSQL for structured historical data
- DynamoDB for recent-turn session windows
- S3 + Bedrock Knowledge Base for W4 markdown docs
- Bedrock AgentCore runtime for orchestration
- EventBridge Scheduler + Lambda for KB sync
- IAM roles, security groups, and CloudWatch logs

## Terraform layout
- `infra/terraform/providers.tf` configures Terraform and the AWS provider.
- `infra/terraform/networking.tf` creates the VPC, subnets, route table, and security groups.
- `infra/terraform/storage.tf` provisions the frontend bucket, CloudFront distribution, and knowledge base bucket.
- `infra/terraform/database.tf` provisions PostgreSQL and the `${var.project_name}-${var.environment}-sessions` DynamoDB table.
- `infra/terraform/compute.tf` provisions the backend Lambda, monitoring Lambda, and HTTP APIs.
- `infra/terraform/bedrock.tf` stores `knowledge_base_id`, `knowledge_base_data_source_id`, and `agent_runtime_arn` for deployment wiring.
- `infra/terraform/iam.tf` defines Lambda IAM roles and policies.
- `infra/terraform/scheduler.tf` provisions the KB sync Lambda and EventBridge Scheduler trigger.
- `infra/terraform/outputs.tf` exposes API URLs, bucket names, the session table, and the PostgreSQL endpoint.

## Environment variables by service
### Backend Lambda
- `AWS_REGION`
- `DATABASE_URL`
- `SESSION_TABLE_NAME`
- `MONITORING_BASE_URL`
- `KNOWLEDGE_BASE_ID`
- `KNOWLEDGE_BASE_DATA_SOURCE_ID`
- `AGENT_RUNTIME_ARN`

### Monitoring Lambda
- no custom variables are required for the static monitoring fixture service in this phase

### KB sync Lambda
- `AWS_REGION`
- `KNOWLEDGE_BASE_ID`
- `KNOWLEDGE_BASE_DATA_SOURCE_ID`

## Terraform apply flow
1. Copy `infra/terraform/terraform.tfvars.example` to `terraform.tfvars` and fill in real values.
2. Run `terraform init` from `infra/terraform`.
3. Run `terraform fmt -check`.
4. Run `terraform validate`.
5. Run `terraform apply`.
6. Capture the output values for the backend API URL, monitoring API URL, frontend bucket, knowledge base bucket, session table, and PostgreSQL endpoint.

## Knowledge base upload and sync
Upload the W4 markdown documents:

```bash
docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket <knowledge-base-bucket>
```

Trigger a sync manually:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help
```

The Terraform scheduler provisions a `rate(6 hours)` EventBridge schedule that invokes the KB sync Lambda.

## Where to find deployed values
- `terraform output backend_api_url` → chat API base URL
- `terraform output monitoring_api_url` → monitoring API base URL
- `terraform output frontend_bucket_name` → static asset bucket
- `terraform output knowledge_base_bucket_name` → S3 bucket for knowledge base markdown files
- `terraform output session_table_name` → DynamoDB session window table
- `terraform output postgres_endpoint` → PostgreSQL host for `DATABASE_URL`

## Networking and IAM notes
- The Lambda security group is the only source allowed to reach PostgreSQL on port 5432.
- The backend Lambda role is limited to DynamoDB session writes, knowledge base bucket reads, Bedrock runtime and ingestion calls, and CloudWatch logs.
- The sync Lambda role is limited to KB sync and CloudWatch logging.
