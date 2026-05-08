# HexaRAG AWS Deployment Guide

This guide is a beginner-friendly runbook for deploying HexaRAG to AWS as the repository exists today.

It is written for:
- AWS region `us-east-1`
- app name `hexarag`
- AWS-generated URLs only
- a beginner operator with admin access to their AWS account

This repo is not a one-click deployment yet. Some steps are CLI-driven, some can be done in the AWS Console, and some depend on current repo limitations that are called out explicitly below.

## Label legend
Each step is marked with one or more labels so you always know who does the work.

- **AWS CLI or SDK** — use terminal commands or scripts against AWS services.
- **Manual in AWS Console** — use the AWS web console instead of CLI.
- **Run locally yourself** — run the command on your machine.
- **Claude can help/run** — Claude can help prepare files, explain values, or run repo commands with you.
- **Verify manually** — stop and confirm the result before continuing.

## Current deployment model
This repo currently targets the following AWS deployment shape:

- S3 + CloudFront host the frontend assets.
- API Gateway + Lambda expose the FastAPI chat API.
- API Gateway + Lambda expose the monitoring API.
- PostgreSQL stores structured historical data.
- DynamoDB stores recent session memory.
- An S3 bucket stores knowledge base markdown documents.
- A scheduled sync Lambda exists for knowledge base ingestion support.
- The current checked-in Terraform wiring consumes `knowledge_base_id`, `knowledge_base_data_source_id`, `agent_id`, and `agent_alias_id`.
- This repo does not currently create those Bedrock resources directly.

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
**AWS CLI or SDK**
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
**AWS CLI or SDK**
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

This project uses Docker Compose for local runtime, tests, build steps, and helper scripts. Do not switch to a host-installed Python, Node, or PostgreSQL workflow.

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

## Step 5: Create or locate the Bedrock prerequisites
Terraform does not create these Bedrock resources for you in this repo. You must create or locate these values before you can finish the deployment inputs:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_id`
- `agent_alias_id`

The rest of this guide reflects the current checked-in Bedrock Agents-based backend and Terraform inputs unless a section explicitly says otherwise.

Before you create the Bedrock data source, decide which S3 bucket path it will target.

If you want the data source to point at the Terraform-managed knowledge-base bucket, document that this requires a deployment sequence where the bucket exists before the data source is finalized.

The knowledge-base upload step must finish before you trigger ingestion.

### Option A: AWS CLI or SDK path
**AWS CLI or SDK**
**Verify manually**

Use AWS CLI or an SDK workflow to create or locate:
- the Bedrock Knowledge Base
- the Bedrock Knowledge Base data source
- the Bedrock Agent
- the Bedrock Agent alias

Relevant command families to review before you run them:
- `aws bedrock-agent create-knowledge-base`
- `aws bedrock-agent create-data-source`
- `aws bedrock-agent create-agent`
- `aws bedrock-agent create-agent-alias`

Save the resulting values for the path you actually deploy.

Expected result: you have the Bedrock identifiers required by the checked-in backend wiring before editing Terraform inputs.

### Option B: AWS Console path
**Manual in AWS Console**
**Verify manually**

Use AWS Console to create or locate:
- the Bedrock Knowledge Base
- the Bedrock Knowledge Base data source
- the Bedrock Agent
- the Bedrock Agent alias

Save the resulting values for the path you actually deploy.

Expected result: you have the Bedrock identifiers required by the checked-in backend wiring before editing Terraform inputs.

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

Edit `infra/terraform/terraform.tfvars` and set the current checked-in inputs:

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

What these mean in the current wiring:
- `aws_region`: AWS region for this deployment
- `project_name`: prefix used in resource names
- `environment`: environment suffix like `dev`
- `database_password`: password Terraform uses for PostgreSQL
- `agent_id`: Bedrock Agent ID consumed by the backend Lambda config
- `agent_alias_id`: Bedrock Agent alias ID consumed by the backend Lambda config
- `knowledge_base_id`: Bedrock Knowledge Base ID
- `knowledge_base_data_source_id`: Bedrock data source ID

**Verify manually**

Before moving on, confirm the file exists and none of the Bedrock fields still use placeholder values.

## Step 7: Package the Lambda artifacts
**Run locally yourself**
**Verify manually**

Use the repo-owned packaging command from the repo root:

```bash
docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py
```

Expected result: the command prints three artifact paths and creates these files in `infra/terraform`:
- `backend.zip`
- `monitoring.zip`
- `kb-sync.zip`

Verify the files exist before continuing:

```powershell
Get-ChildItem .\infra\terraform\*.zip
```

## Step 8: Initialize Terraform
**Run locally yourself**

From `infra/terraform`:

```bash
terraform init
```

What this does: downloads the provider plugins Terraform needs.

Expected result: Terraform finishes successfully and tells you initialization is complete.

## Step 9: Check Terraform formatting
**Run locally yourself**

```bash
terraform fmt -check
```

Expected result: no errors.

## Step 10: Validate Terraform configuration
**Run locally yourself**

```bash
terraform validate
```

Expected result: Terraform reports that the configuration is valid.

If this fails, do not continue to apply. Fix the validation error first.

## Step 11: Apply Terraform
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

## Step 12: Save the Terraform outputs
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
terraform output cloudfront_domain_name
terraform output cloudfront_distribution_id
```

Save all of them.

You will need them later.

### Frontend and CloudFront outputs
Terraform now exposes both:
- `cloudfront_domain_name`
- `cloudfront_distribution_id`

Use those outputs for browser verification and cache invalidation after uploading frontend assets.

## Step 13: Build the frontend for deployment
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

## Step 14: Upload the frontend assets to S3
**Run locally yourself**
**Verify manually**

Use the frontend bucket name from Terraform outputs and upload the built files.

Example:

```bash
aws s3 sync frontend/dist s3://<frontend-bucket-name> --delete
```

Expected result: your built frontend files upload to the S3 bucket.

## Step 15: Open the frontend through CloudFront
**Manual in AWS Console**
**Verify manually**

Open the CloudFront domain from Terraform outputs in your browser.

Expected result: the HexaRAG frontend loads.

## Step 16: Upload the knowledge base markdown files
**Claude can help/run**
**Run locally yourself**

Use the knowledge base bucket name from Terraform outputs.

From the repo root:

```bash
docker compose run --rm backend uv run python scripts/upload_knowledge_base.py --bucket <knowledge-base-bucket>
```

Expected result: the markdown files from the W4 knowledge base folder upload into the S3 bucket.

## Step 17: Trigger a manual knowledge base sync
**Claude can help/run**
**Run locally yourself**
**Verify manually**

Only run this after the knowledge base markdown files have been uploaded to S3.

Run:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py
```

Expected result: the script triggers a Bedrock ingestion job.

Then verify in AWS Console or your AWS tooling that the ingestion job starts and completes successfully.

## Step 18: Load structured historical data if needed
**Claude can help/run**
**Run locally yourself**

The current repo loader imports `monthly_costs.csv` into `monthly_costs` only.

Run:

```bash
docker compose run --rm backend uv run python scripts/load_structured_data.py
```

Confirm the target database schema and connection settings before running the loader against AWS-hosted PostgreSQL.

Expected result: the repo’s current monthly-cost data load completes against the intended database.

## Infrastructure verification
**Run locally yourself**
**Verify manually**

Use the deployment outputs to confirm the infrastructure responds where the repo expects it to.

### Backend API
```bash
curl -X POST "https://your-backend-api-url/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What changed in EC2 cost last month?","session_id":"demo-session"}'
```

Expected result: you receive a JSON chat response instead of an infrastructure error.

### Monitoring API
```bash
curl "https://your-monitoring-api-url/services"
```

Expected result: you receive the monitoring service list.

### Browser verification
Open the frontend through the Terraform output `cloudfront_domain_name` and confirm the browser talks to the deployed backend instead of `localhost`.

Expected result: the chat UI loads, submits successfully, and the inspection console renders the returned trace.

## Product verification
**Verify manually**

Before calling the deployment usable, confirm all of these in the browser:
- chat UI renders correctly
- assistant responses appear in the transcript
- the inspection console stays visible
- sources render when provided
- tool-call traces render when provided
- uncertainty appears when the runtime signals it
- contradiction details appear when the runtime returns `conflict_resolution`
- the frontend is not calling `http://localhost:8000`

## Current repo limitations and caveats
- Bedrock resource creation is still external to Terraform in this repo.
- The current checked-in deployment path still requires externally supplied `knowledge_base_id`, `knowledge_base_data_source_id`, `agent_id`, and `agent_alias_id` before deployment.
- The Bedrock Agents migration is already landed in the backend and Terraform wiring; the remaining work is supplying real AWS Bedrock identifiers and verifying deployed behavior.
- The frontend still depends on build-time injection of `VITE_API_BASE_URL`. If you skip that value, the deployed browser bundle will call `http://localhost:8000`.
- Retrieval readiness still depends on running the knowledge-base upload step before ingestion and waiting for ingestion to complete successfully.
- The current structured-data loader only imports monthly costs, so historical numeric coverage is narrower than the full W4 package.
- Full contradiction handling quality still depends on the deployed runtime consistently returning `conflict_resolution` metadata.

## Browser and product verification split
Use this checklist to distinguish infrastructure creation from user-visible success:
- infrastructure verification: Terraform apply succeeds and the API/monitoring endpoints respond
- Bedrock and data verification: KB upload succeeds, ingestion completes, and any needed structured-data load finishes
- browser and product verification: CloudFront frontend loads, browser requests succeed, and the visible trace-driven product surfaces work end to end

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
The current Terraform outputs expose the backend API URL, monitoring API URL, frontend bucket name, knowledge-base bucket name, session table name, and PostgreSQL endpoint.

They do not expose the CloudFront distribution domain, so you must retrieve that separately until Terraform outputs are extended.

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

Only run this after the knowledge base markdown files have been uploaded to S3.

Run:

```bash
docker compose run --rm backend uv run python scripts/sync_knowledge_base.py
```

Expected result: the script triggers a Bedrock ingestion job.

Then verify in AWS Console or your AWS tooling that the ingestion job starts and completes successfully.

## Step 19: Load structured historical data if needed
**Claude can help/run**
**Run locally yourself**

The current repo loader imports `monthly_costs.csv` into `monthly_costs`.

It does not fully populate every structured dataset described in the W4 package.

Run:

```bash
docker compose run --rm backend uv run python scripts/load_structured_data.py
```

Confirm the target database schema and connection settings before running the loader against AWS-hosted PostgreSQL.

Expected result: the repo’s current monthly-cost data load completes against the intended database.

## Infrastructure verification
**Run locally yourself**
**Verify manually**

Use the deployment outputs to confirm the infrastructure responds where the repo expects it to.

### Backend API
```bash
curl -X POST "https://your-backend-api-url/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What changed in EC2 cost last month?","session_id":"demo-session"}'
```

Expected result: you receive a JSON chat response instead of an infrastructure error.

### Monitoring API
```bash
curl "https://your-monitoring-api-url/services"
```

Expected result: the monitoring endpoint responds successfully.

## Bedrock and data verification
**Run locally yourself**
**Verify manually**

Use these checks to confirm the knowledge base and data path are ready.

Checklist:
- the knowledge base files were uploaded to the knowledge-base S3 bucket
- the knowledge base upload completed before ingestion was triggered
- the Bedrock ingestion job started successfully
- the Bedrock ingestion job completed successfully
- the database load you ran matches the current repo capability you intended to seed

## Browser and product verification
**Verify manually**

Open the CloudFront frontend URL and test the app end to end.

Checklist:
- the page loads
- the chat UI renders
- the right-side inspection console is visible
- sending a chat request works
- trace and citation context appears in the UI
- there are no obvious frontend runtime errors

## Current repo limitations and caveats
These are known caveats in the current repo state. They are not necessarily deployment mistakes.

- CloudFront private S3 access is wired through `infra/terraform/storage.tf` with an OAC-scoped bucket policy. If the frontend starts returning `AccessDenied`, re-apply Terraform and verify the frontend bucket policy still grants `s3:GetObject` to the current distribution ARN.
- The frontend build must use `VITE_API_BASE_URL`; otherwise it falls back to `http://localhost:8000`.
- The backend browser path depends on two layers of origin handling: the Lambda app allowlist and the API Gateway HTTP API `cors_configuration`. Terraform currently injects `http://localhost:5173` plus the deployed CloudFront default domain into the Lambda and configures API Gateway preflight for that CloudFront origin. If you replace the distribution or add a custom frontend domain, update both pieces in `infra/terraform/compute.tf`.
- The current structured-data loader only loads `monthly_costs.csv`; it does not populate every structured dataset described in `W4/data_package/README.md`.
- The monitoring API routes in Terraform currently expose `/services` and `/metrics/{service_name}` only.
- Lambda packaging depends on `backend/scripts/package_lambda_artifacts.py`; if a deployed Lambda fails with `Runtime.ImportModuleError`, rebuild the artifacts and confirm `backend/src/hexarag_api/services/lambda_packaging.py` still includes the required FastAPI runtime dependencies such as `annotated_doc` and `dotenv`.
- Some Bedrock Anthropic models must be attached to the agent through an inference profile rather than an on-demand model ID. If `/chat` keeps returning the fallback contract after Lambda health is restored, verify the agent model selection and run `prepare-agent` again.

## Troubleshooting

### Bedrock resources are missing or unavailable
- Confirm you are in `us-east-1`.
- Confirm your AWS account has Bedrock access enabled.
- Confirm the Knowledge Base, data source, Bedrock Agent, and Bedrock Agent alias really exist.
- Re-check the values copied into `terraform.tfvars`.

### Terraform apply fails because zip files are missing
- Confirm `backend.zip`, `monitoring.zip`, and `kb-sync.zip` exist in `infra/terraform`.
- Re-run your PowerShell `Compress-Archive` or `7z` commands.
- Confirm the filenames match Terraform exactly.

### Frontend loads but still calls localhost
- Rebuild the frontend with `VITE_API_BASE_URL` set to the deployed backend API URL.
- Re-upload the rebuilt `frontend/dist` assets to S3.
- Refresh through CloudFront again.

### Frontend loads but still calls `http://backend:8000`
- This means a production build inherited the Docker-only dev URL instead of an AWS API URL.
- Keep the Docker-local `VITE_API_BASE_URL=http://backend:8000` scoped to the frontend dev-server command only; do not leave it as a service-level environment variable for `docker compose run` builds.
- Rebuild with an explicit deploy URL, for example: `VITE_API_BASE_URL="https://your-backend-api-url" docker compose run --rm frontend sh -lc 'node node_modules/vite/bin/vite.js build'`.
- Re-upload the rebuilt `frontend/dist` assets to S3 and invalidate CloudFront.
- Verify in the browser that requests go to the HTTPS API Gateway URL and that the inspection console renders a successful response.

### Frontend does not load through CloudFront
- Confirm the frontend build files were uploaded to the correct S3 bucket.
- Confirm the CloudFront distribution points to that bucket.
- Confirm the frontend S3 bucket policy still grants `cloudfront.amazonaws.com` access scoped to the current distribution ARN.
- Allow time for CloudFront propagation after changes.

### Deployed Lambda fails to import FastAPI runtime modules
- Rebuild the artifacts with `docker compose run --rm backend uv run python scripts/package_lambda_artifacts.py`.
- Confirm the generated zip was the one Terraform or `aws lambda update-function-code` actually deployed.
- Check `backend/src/hexarag_api/services/lambda_packaging.py` for missing dependency globs before rebuilding again.
- Check the failing Lambda's CloudWatch logs for the exact missing module name before changing the packaging list.

### Bedrock-backed chat keeps returning the fallback message
- Confirm the backend Lambda itself is healthy first; import failures and env wiring problems surface before Bedrock invocation.
- Confirm the configured `AGENT_ID` and `AGENT_ALIAS_ID` are correct.
- Check whether the agent model is using an inference profile when the selected foundation model requires one.
- Run `prepare-agent` after changing the model or core agent configuration.
- Re-test with a tool-backed question and inspect the returned `tool_calls` trace.

### Backend cannot reach PostgreSQL
- Check the database endpoint from Terraform output.
- Check the Lambda security group and RDS security group.
- Confirm the generated `DATABASE_URL` is correct.
- Check backend Lambda logs in CloudWatch.

### Knowledge base files uploaded but retrieval still fails
- Confirm the files exist in the knowledge base S3 bucket.
- Confirm the ingestion job actually ran.
- Confirm the ingestion job completed successfully.
- Re-check `knowledge_base_id` and `knowledge_base_data_source_id`.

### Monitoring API works but chat API does not
- Check backend Lambda logs separately from monitoring Lambda logs.
- Confirm the backend is configured with the correct `AGENT_ID` and `AGENT_ALIAS_ID` values.
- Confirm the backend Lambda environment variables are correct.
- Confirm the `/chat` route is deployed on the backend API Gateway.

## Where the deployed values come from
Use Terraform outputs for:
- `backend_api_url` → chat API base URL
- `monitoring_api_url` → monitoring API base URL
- `frontend_bucket_name` → S3 bucket for frontend assets
- `knowledge_base_bucket_name` → S3 bucket for KB markdown files
- `session_table_name` → DynamoDB session storage table
- `postgres_endpoint` → PostgreSQL host

For the current product-capability inventory, partial wiring notes, and Bedrock mapping checklist, see `docs/app-functionality.md`.

## Repo files this guide matches
- `infra/terraform/terraform.tfvars.example`
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
- `backend/src/hexarag_api/config.py`
- `backend/src/monitoring_api/main.py`
- `frontend/src/lib/api.ts`
- `W4/data_package/README.md`
