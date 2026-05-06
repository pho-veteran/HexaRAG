# HexaRAG Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision the AWS deployment stack for HexaRAG, including knowledge base storage, scheduled sync, and deployment documentation.

**Architecture:** Keep infrastructure separate from product logic by defining Terraform resources for network, storage, database, compute, IAM, and scheduling in focused files under `infra/terraform`. Pair the infrastructure with explicit deployment scripts and `docs/aws.md` so the provisioned Bedrock, API, storage, and sync paths are understandable and repeatable.

**Tech Stack:** Terraform, AWS, Lambda, API Gateway, S3, CloudFront, DynamoDB, RDS PostgreSQL, EventBridge Scheduler, boto3.

---

## Planned File Structure

### Infrastructure (`infra/terraform/`)
- Create: `infra/terraform/providers.tf` — AWS provider and Terraform version constraints.
- Create: `infra/terraform/variables.tf` — environment-specific inputs.
- Create: `infra/terraform/networking.tf` — VPC, subnets, route tables, security groups.
- Create: `infra/terraform/storage.tf` — S3 buckets for frontend and KB docs.
- Create: `infra/terraform/database.tf` — PostgreSQL and DynamoDB resources.
- Create: `infra/terraform/compute.tf` — Lambda functions and API Gateway.
- Create: `infra/terraform/bedrock.tf` — Bedrock/KB identifiers and wiring inputs.
- Create: `infra/terraform/iam.tf` — IAM roles and policies.
- Create: `infra/terraform/scheduler.tf` — EventBridge schedule for KB sync.
- Create: `infra/terraform/outputs.tf` — output API URL, bucket names, table names.
- Create: `infra/terraform/terraform.tfvars.example` — sample values.

### Backend scripts
- Create: `backend/scripts/upload_knowledge_base.py` — upload W4 KB markdown to the KB S3 bucket.
- Create: `backend/scripts/sync_knowledge_base.py` — trigger Bedrock KB sync manually or from the scheduler.

### Docs
- Create: `docs/aws.md` — explain AWS resources, deployment steps, networking, IAM, and sync flow.

---

### Task 1: Provision AWS resources, KB sync, and deployment documentation

**Files:**
- Create: `infra/terraform/providers.tf`
- Create: `infra/terraform/variables.tf`
- Create: `infra/terraform/networking.tf`
- Create: `infra/terraform/storage.tf`
- Create: `infra/terraform/database.tf`
- Create: `infra/terraform/compute.tf`
- Create: `infra/terraform/bedrock.tf`
- Create: `infra/terraform/iam.tf`
- Create: `infra/terraform/scheduler.tf`
- Create: `infra/terraform/outputs.tf`
- Create: `infra/terraform/terraform.tfvars.example`
- Create: `backend/scripts/upload_knowledge_base.py`
- Create: `backend/scripts/sync_knowledge_base.py`
- Create: `docs/aws.md`

- [ ] **Step 1: Write the Terraform skeleton and resource inputs**

Create `infra/terraform/providers.tf`:

```hcl
terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
```

Create `infra/terraform/variables.tf`:

```hcl
variable "aws_region" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }
variable "database_password" { type = string, sensitive = true }
variable "agent_runtime_arn" { type = string }
variable "knowledge_base_id" { type = string }
variable "knowledge_base_data_source_id" { type = string }
```

- [ ] **Step 2: Add AWS infrastructure resources**

Create these Terraform resources:
- `networking.tf`: VPC, 2 public subnets, 2 private subnets, Lambda security group, RDS security group.
- `storage.tf`: frontend static bucket, CloudFront distribution, KB document bucket.
- `database.tf`: PostgreSQL instance plus DynamoDB table `hexarag-sessions`.
- `compute.tf`: backend Lambda, monitoring Lambda, API Gateway HTTP API routes.
- `scheduler.tf`: EventBridge Scheduler calling the KB sync Lambda.
- `iam.tf`: least-privilege IAM for Lambda access to RDS secrets, DynamoDB, S3, Bedrock, and logs.

Use this DynamoDB example in `database.tf`:

```hcl
resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}-${var.environment}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}
```

- [ ] **Step 3: Add Bedrock sync scripts and scheduler entrypoint**

Create `backend/scripts/sync_knowledge_base.py`:

```python
import boto3
from hexarag_api.config import Settings


def main() -> None:
    settings = Settings()
    client = boto3.client('bedrock-agent')
    client.start_ingestion_job(
        knowledgeBaseId=settings.knowledge_base_id,
        dataSourceId=settings.knowledge_base_data_source_id,
    )


if __name__ == '__main__':
    main()
```

Create `backend/scripts/upload_knowledge_base.py` so it uploads `../xbrain-learners/W4/data_package/knowledge_base/*.md` to the KB S3 bucket using `boto3.client('s3').upload_file(...)`.

- [ ] **Step 4: Document the deployed AWS architecture in `docs/aws.md`**

Write `docs/aws.md` with these sections:

```md
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
```

Also include:
- environment variables by service
- `terraform apply` flow
- KB upload and sync commands
- where to find API URLs and bucket names

- [ ] **Step 5: Validate Terraform formatting and docs-adjacent scripts**

Run from `infra/terraform`:

```bash
terraform fmt -check
terraform validate
```

Run from `hexarag`:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help
```

Expected: Terraform validates and the Python script imports cleanly.

- [ ] **Step 6: Commit the infrastructure layer**

```bash
git add infra docs/aws.md backend/scripts
git commit -m "feat: add terraform deployment and knowledge base sync"
```

---

## Spec Coverage Check

- **FR10 Knowledge base sync** → Task 1
- **AWS/Terraform deployment** → Task 1
- **11.2 Documentation requirement** → Task 1 writes `docs/aws.md`
- **NFR6 Maintainability** → focused Terraform files split by responsibility
- **NFR9 Demo readiness** → deployment docs support reproducible environments for screenshots and evidence capture

## Placeholder Scan

- No `TODO`, `TBD`, or “similar to Task N” placeholders remain.
- The plan names exact Terraform files, scripts, validation commands, and commit boundaries.

## Type Consistency Check

Use these names consistently across infra and deployment scripts:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`
- `${var.project_name}-${var.environment}-sessions`
- the same API and bucket names documented in `outputs.tf` and `docs/aws.md`

Do not invent different resource naming patterns between Terraform and docs.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-06-hexarag-infra.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
