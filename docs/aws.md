# HexaRAG AWS Deployment Guide

This guide is a beginner-friendly, step-by-step runbook for deploying HexaRAG to AWS.

It is written for:
- AWS region `us-east-1`
- app name `hexarag`
- AWS-generated URLs only
- a beginner operator with admin access to their AWS account

This repo is **not** a one-click deploy yet. Some steps are manual in the AWS Console, and some steps can be run locally or with Claude helping you in the terminal.

## Label legend
Each step is marked with one or more labels so you always know who does the work.

- **Manual in AWS Console** — you click in AWS yourself.
- **Run locally yourself** — you run the command on your own machine.
- **Claude can help/run** — Claude can help prepare files, explain values, or run repo commands with you.
- **Verify manually** — stop and confirm the result before continuing.

## What this deployment creates
Terraform in this repo provisions:
- S3 + CloudFront for the Vite frontend
- API Gateway + Lambda for the FastAPI chat API
- API Gateway + Lambda for the monitoring API
- PostgreSQL for structured historical data
- DynamoDB for session memory
- S3 bucket for knowledge base files
- EventBridge Scheduler + Lambda for knowledge base sync
- IAM roles, security groups, and CloudWatch logs

Important repo detail: Terraform in this repo **expects you to supply** these Bedrock-side values yourself:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`

## Before you start
You need:
- an AWS account with admin-level access
- AWS CLI installed
- Terraform installed
- Docker Desktop installed and running
- Git installed
- this repository cloned locally

## Step 1: Check your local tools
**Run locally yourself**

Confirm the required tools are installed.

```bash
aws --version
terraform version
docker --version
docker compose version
git --version
```

Expected result: every command prints a version instead of failing.

If Docker Desktop is installed but Docker commands fail, start Docker Desktop and wait until it is fully running.

## Step 2: Configure AWS CLI
**Run locally yourself**

Run:

```bash
aws configure
```

Use:
- AWS Access Key ID: your AWS access key
- AWS Secret Access Key: your AWS secret key
- Default region name: `us-east-1`
- Default output format: `json`

## Step 3: Verify the AWS account and region
**Run locally yourself**
**Verify manually**

Run:

```bash
aws sts get-caller-identity
aws configure get region
```

Expected result:
- `aws sts get-caller-identity` returns your AWS account and ARN
- `aws configure get region` returns `us-east-1`

Do not continue until both look correct.

## Step 4: Clone the repo and confirm the local workflow
**Run locally yourself**

If you have not cloned the repo yet:

```bash
git clone <your-repo-url>
cd hexarag
```

This project uses Docker Compose for local runtime, tests, build steps, and helper scripts. Do not switch to a host-installed Python/Node/Postgres workflow.

Run a local frontend build check:

```bash
docker compose run --rm frontend npm run build
```

Expected result: the frontend build completes successfully.

Optional backend script import check:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py --help
```

Expected result: the command exits cleanly and prints help text.

## Step 5: Create the Bedrock prerequisites manually
Terraform does **not** create these identifiers for you in this repo.

You must create or locate all of the following before Terraform apply:
- Knowledge Base
- Knowledge Base data source
- AgentCore runtime

### Step 5.1: Create or locate the Knowledge Base
**Manual in AWS Console**
**Verify manually**

In AWS Console, go to Amazon Bedrock and create a Knowledge Base if you do not already have one.

At the end of this step, save the:
- `knowledge_base_id`

### Step 5.2: Create or locate the Knowledge Base data source
**Manual in AWS Console**
**Verify manually**

Inside the Knowledge Base, create or locate the data source that will point to the S3 bucket used for HexaRAG knowledge base markdown files.

At the end of this step, save the:
- `knowledge_base_data_source_id`

### Step 5.3: Create or locate the AgentCore runtime
**Manual in AWS Console**
**Verify manually**

Create or locate the Bedrock AgentCore runtime that HexaRAG will invoke.

At the end of this step, save the:
- `agent_runtime_arn`

Do not continue until you have all three values saved somewhere safe.

## Step 6: Prepare Terraform inputs
**Claude can help/run**
**Run locally yourself**

From the repo root, create a real Terraform variables file from the example.

Example PowerShell:

```powershell
Copy-Item infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Or in bash:

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Edit `infra/terraform/terraform.tfvars` and set:

```hcl
aws_region                    = "us-east-1"
project_name                  = "hexarag"
environment                   = "dev"
database_password             = "replace-with-a-real-password"
agent_runtime_arn             = "your-agent-runtime-arn"
knowledge_base_id             = "your-knowledge-base-id"
knowledge_base_data_source_id = "your-data-source-id"
```

What these mean:
- `aws_region`: AWS region for this deployment
- `project_name`: prefix used in resource names
- `environment`: environment suffix like `dev`
- `database_password`: password Terraform uses for PostgreSQL
- `agent_runtime_arn`: Bedrock AgentCore runtime ARN
- `knowledge_base_id`: Bedrock Knowledge Base ID
- `knowledge_base_data_source_id`: Bedrock data source ID

**Verify manually**

Before moving on, confirm the file exists and none of the Bedrock fields still use placeholder values.

## Step 7: Understand the Lambda zip packaging requirement
Terraform expects zip files for the Lambda functions. It does **not** build them for you automatically.

The current Terraform files reference:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

These filenames are referenced in:
- `infra/terraform/compute.tf`
- `infra/terraform/scheduler.tf`

That means you need to create those zip files before `terraform apply`.

## Step 8: Build the Lambda zip files on Windows
**Run locally yourself**
**Verify manually**

For beginner-friendly Windows instructions, prefer either:
- PowerShell `Compress-Archive`, or
- `7z`

### Important note before zipping
This repo does not currently include a documented one-command packaging pipeline for these Lambda zip artifacts.

So this runbook treats packaging as a manual checkpoint.

Before running `terraform apply`, make sure these files exist inside `infra/terraform`:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

### Recommended packaging approach for now
Because the repo currently documents the Lambda filenames but not a finalized packaging script, use one of these approaches:

#### Option A: PowerShell `Compress-Archive`
**Run locally yourself**

Create zip files from the prepared Lambda artifact folders if you have already assembled them.

Example pattern:

```powershell
Compress-Archive -Path .\path-to-backend-artifact\* -DestinationPath .\infra\terraform\backend.zip -Force
Compress-Archive -Path .\path-to-monitoring-artifact\* -DestinationPath .\infra\terraform\monitoring.zip -Force
Compress-Archive -Path .\path-to-kb-sync-artifact\* -DestinationPath .\infra\terraform\kb-sync.zip -Force
```

#### Option B: `7z`
**Run locally yourself**

```powershell
7z a .\infra\terraform\backend.zip .\path-to-backend-artifact\*
7z a .\infra\terraform\monitoring.zip .\path-to-monitoring-artifact\*
7z a .\infra\terraform\kb-sync.zip .\path-to-kb-sync-artifact\*
```

### What goes into each zip
At minimum, your implementation work must package code so Terraform can upload the matching Lambda runtime payloads:
- `backend.zip` → the backend Lambda application code
- `monitoring.zip` → the monitoring Lambda code
- `kb-sync.zip` → the sync Lambda entrypoint code

Because the repo does not yet fully document the exact Windows packaging recipe, treat this as a required manual build checkpoint.

**Verify manually**

Before continuing, confirm all three zip files exist:

```powershell
Get-ChildItem .\infra\terraform\*.zip
```

Expected result: you can see `backend.zip`, `monitoring.zip`, and `kb-sync.zip`.

## Step 9: Initialize Terraform
**Run locally yourself**

From `infra/terraform`:

```bash
terraform init
```

What this does: downloads the provider plugins Terraform needs.

Expected result: Terraform finishes successfully and tells you initialization is complete.

## Step 10: Check Terraform formatting
**Run locally yourself**

```bash
terraform fmt -check
```

Expected result: no errors.

## Step 11: Validate Terraform configuration
**Run locally yourself**

```bash
terraform validate
```

Expected result: Terraform reports that the configuration is valid.

If this fails, do not continue to apply. Fix the validation error first.

## Step 12: Apply Terraform
**Run locally yourself**
**Verify manually**

Run:

```bash
terraform apply
```

Review the plan carefully and approve it only if it matches the expected resources.

Expected resources include:
- VPC, subnets, route table, and security groups
- PostgreSQL database
- DynamoDB table
- frontend S3 bucket
- knowledge base S3 bucket
- CloudFront distribution
- backend Lambda + API Gateway
- monitoring Lambda + API Gateway
- sync Lambda + EventBridge Scheduler
- IAM roles and policies
- SSM parameters for the Bedrock identifiers

When apply completes, save the output values.

## Step 13: Save the Terraform outputs
**Run locally yourself**
**Verify manually**

Run:

```bash
terraform output backend_api_url
terraform output monitoring_api_url
terraform output frontend_bucket_name
terraform output knowledge_base_bucket_name
terraform output session_table_name
terraform output postgres_endpoint
```

Save all of them.

You will need them later.

### Important frontend URL caveat
The current Terraform outputs file does **not** expose the CloudFront domain name.

That means you may need to open AWS Console and manually copy the CloudFront distribution domain for your frontend URL unless Terraform is extended later.

## Step 14: Build the frontend for deployment
**Run locally yourself**

From the repo root:

```bash
docker compose run --rm frontend npm run build
```

Important frontend config detail: the frontend uses `VITE_API_BASE_URL` during build time. If you do not set it, it falls back to `http://localhost:8000`.

That behavior comes from `frontend/src/lib/api.ts`.

For an AWS deployment, you must build with the deployed backend API URL.

### Example build with API URL
**Run locally yourself**

Use the backend API URL you saved from Terraform.

PowerShell example:

```powershell
$env:VITE_API_BASE_URL="https://your-backend-api-url"
docker compose run --rm frontend npm run build
Remove-Item Env:VITE_API_BASE_URL
```

Bash example:

```bash
VITE_API_BASE_URL="https://your-backend-api-url" docker compose run --rm frontend npm run build
```

Expected result: the frontend build completes successfully.

## Step 15: Upload the frontend assets to S3
**Run locally yourself**
**Verify manually**

Use the frontend bucket name from Terraform outputs and upload the built files.

Example:

```bash
aws s3 sync frontend/dist s3://<frontend-bucket-name> --delete
```

Expected result: your built frontend files upload to the S3 bucket.

## Step 16: Open the frontend through CloudFront
**Manual in AWS Console**
**Verify manually**

Open CloudFront in AWS Console.

Find the distribution created for the frontend and copy its default domain name.

Open that URL in your browser.

Expected result: the HexaRAG frontend loads.

### Important hosting caveat
The current Terraform config creates:
- the S3 bucket
- the CloudFront distribution
- the Origin Access Control

But it does **not** currently show the S3 bucket policy wiring that CloudFront typically needs for private OAC-backed access.

If the site does not load correctly through CloudFront, check the S3 bucket policy and CloudFront origin access configuration first.

## Step 17: Upload the knowledge base markdown files
**Claude can help/run**
**Run locally yourself**

Use the knowledge base bucket name from Terraform outputs.

From the repo root:

```bash
docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket <knowledge-base-bucket>
```

Expected result: the markdown files from the W4 knowledge base folder upload into the S3 bucket.

## Step 18: Trigger a manual knowledge base sync
**Claude can help/run**
**Run locally yourself**
**Verify manually**

Run:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py
```

Expected result: the script triggers a Bedrock ingestion job.

Then verify in AWS Console that the ingestion job starts and completes successfully.

## Step 19: Load structured historical data if needed
**Claude can help/run**
**Run locally yourself**

The backend includes a structured data loader script:

```bash
docker compose run --rm backend uv run python scripts/load_structured_data.py
```

Important caveat: this command uses the repo’s configured `DATABASE_URL` and data root. For a deployed AWS database, you should confirm the command is pointed at the intended PostgreSQL instance before loading data.

Expected result: the required structured data rows are inserted into PostgreSQL.

## Step 20: Verify the backend API
**Run locally yourself**
**Verify manually**

Use the backend API URL from Terraform outputs and test the `/chat` route.

Example `curl` pattern:

```bash
curl -X POST "https://your-backend-api-url/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What changed in EC2 cost last month?","session_id":"demo-session"}'
```

Expected result: you receive a JSON chat response instead of an infrastructure error.

## Step 21: Verify the monitoring API
**Run locally yourself**
**Verify manually**

Use the monitoring API URL from Terraform outputs.

Example:

```bash
curl "https://your-monitoring-api-url/services"
```

Expected result: the monitoring endpoint responds successfully.

## Step 22: Verify the app in the browser
**Verify manually**

Open the CloudFront frontend URL and test the app end to end.

Checklist:
- the page loads
- the chat UI renders
- the right-side observability panel is visible
- sending a chat request works
- trace/citation context appears in the UI
- there are no obvious frontend runtime errors

## Step 23: Check CloudWatch logs if something fails
**Manual in AWS Console**
**Verify manually**

If anything fails:
- open CloudWatch Logs
- check the backend Lambda log group
- check the monitoring Lambda log group
- check the sync Lambda log group

This helps you separate:
- frontend build/config problems
- API Gateway/Lambda invocation problems
- database connectivity problems
- Bedrock/knowledge-base ingestion problems

## Troubleshooting

### Bedrock resources are missing or unavailable
- Confirm you are in `us-east-1`
- Confirm your AWS account has Bedrock access enabled
- Confirm the Knowledge Base, data source, and AgentCore runtime really exist
- Re-check the values copied into `terraform.tfvars`

### Terraform apply fails because zip files are missing
- Confirm `backend.zip`, `monitoring.zip`, and `kb-sync.zip` exist in `infra/terraform`
- Re-run your PowerShell `Compress-Archive` or `7z` commands
- Confirm the filenames match Terraform exactly

### Frontend loads but still calls localhost
- Rebuild the frontend with `VITE_API_BASE_URL` set to the deployed backend API URL
- Re-upload the rebuilt `frontend/dist` assets to S3
- Refresh through CloudFront again

### Frontend does not load through CloudFront
- Confirm the frontend build files were uploaded to the correct S3 bucket
- Confirm the CloudFront distribution points to that bucket
- Check whether the S3 bucket policy/OAC configuration is complete
- Allow time for CloudFront propagation after changes

### Backend cannot reach PostgreSQL
- Check the database endpoint from Terraform output
- Check the Lambda security group and RDS security group
- Confirm the generated `DATABASE_URL` is correct
- Check backend Lambda logs in CloudWatch

### Knowledge base files uploaded but retrieval still fails
- Confirm the files exist in the knowledge base S3 bucket
- Confirm the Bedrock ingestion job actually ran
- Confirm the ingestion job completed successfully
- Re-check `knowledge_base_id` and `knowledge_base_data_source_id`

### Monitoring API works but chat API does not
- Check backend Lambda logs separately from monitoring Lambda logs
- Confirm `AGENT_RUNTIME_ARN` is valid
- Confirm the backend Lambda environment variables are correct
- Confirm the `/chat` route is deployed on the backend API Gateway

## Where the deployed values come from
Use Terraform outputs for:
- `backend_api_url` → chat API base URL
- `monitoring_api_url` → monitoring API base URL
- `frontend_bucket_name` → S3 bucket for frontend assets
- `knowledge_base_bucket_name` → S3 bucket for KB markdown files
- `session_table_name` → DynamoDB session storage table
- `postgres_endpoint` → PostgreSQL host

## Repo files this guide matches
- `infra/terraform/providers.tf`
- `infra/terraform/networking.tf`
- `infra/terraform/storage.tf`
- `infra/terraform/database.tf`
- `infra/terraform/compute.tf`
- `infra/terraform/bedrock.tf`
- `infra/terraform/iam.tf`
- `infra/terraform/scheduler.tf`
- `infra/terraform/outputs.tf`
- `backend/scripts/upload_knowledge_base.py`
- `backend/scripts/sync_knowledge_base.py`
- `backend/scripts/load_structured_data.py`
- `frontend/src/lib/api.ts`
