# AWS Docs and App Functionality Tracking Design

## Goal
Update the project documentation so deployment guidance matches the real AWS/Bedrock flow in this repository and so the project has a single tracking document for all expected app capabilities.

This design covers two outputs:
- a corrected `docs/aws.md`
- a new `docs/app-functionality.md`

## Why this work is needed
The current `docs/aws.md` is not fully aligned with the repository and the W4 data package.

Known issues include:
- the Bedrock knowledge base and data source order is wrong relative to the Terraform-created S3 bucket
- Bedrock setup is described too narrowly as manual console work even though CLI-driven setup should also be documented
- the knowledge base upload and ingestion dependency is underexplained
- current repo caveats are not documented clearly enough for operators

The project also lacks a single document that tracks all expected app functionality across frontend, backend, tool integrations, retrieval, session memory, observability, and deployment/runtime dependencies. That gap makes future Bedrock agent configuration harder because the expected product surface is spread across code and multiple docs.

## Scope
This design covers documentation changes only.

In scope:
- rewrite `docs/aws.md` to reflect the actual AWS deployment flow and current repo constraints
- add `docs/app-functionality.md` to track all expected app capabilities and their implementation state
- update `TASKS.md` and any relevant documentation references if needed so the repo tracking stays consistent

Out of scope:
- changing Terraform, Lambda packaging, backend runtime wiring, or frontend behavior in this task
- implementing missing product capabilities
- committing changes unless explicitly requested by the user

## Output 1: `docs/aws.md`

### Purpose
`docs/aws.md` remains the deployment source of truth for this repository.

It should be a practical operator runbook for deploying HexaRAG to AWS as the repo exists today, including honest caveats where the infrastructure or runtime still has known limitations.

### Required structure

#### 1. Current deployment model
Open with a short explanation of what this repo actually deploys today:
- frontend static assets in S3 behind CloudFront
- backend FastAPI API on Lambda behind API Gateway
- monitoring API on Lambda behind API Gateway
- PostgreSQL for structured historical data
- DynamoDB for session memory
- S3 bucket for knowledge base documents
- scheduled sync Lambda for knowledge base ingestion
- Bedrock-side identifiers that are external inputs rather than Terraform-managed resources in this repo

#### 2. Bedrock prerequisites with two valid setup paths
Replace console-only framing with two valid options:
- AWS CLI path
- AWS Console path

Both paths must clearly produce the same required values:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`

The doc must state that Terraform in this repo consumes these values but does not create those Bedrock resources directly.

#### 3. Corrected deployment order
The runbook must fix the current sequencing problem and make the dependency chain explicit.

The documented flow should be:
1. verify local tools
2. authenticate AWS access and region
3. establish the S3/Bedrock setup order explicitly
4. create or configure the Bedrock knowledge base, data source, and AgentCore runtime using either CLI or console
5. prepare `terraform.tfvars`
6. prepare Lambda zip artifacts
7. run Terraform commands
8. publish the frontend assets
9. upload knowledge base documents to S3
10. trigger knowledge base ingestion
11. load or verify structured data as documented by the repo’s real capabilities
12. perform infrastructure and product verification

The runbook must explicitly call out that knowledge base document upload must happen before ingestion sync.

#### 4. Current repo limitations and caveats
Include a dedicated section that documents known deployment caveats instead of burying them in troubleshooting. This section should cover only caveats that are supported by the current repo state.

Expected caveats to document include:
- CloudFront/S3 hosting or access-policy gaps if still present
- frontend-to-backend origin/CORS caveats for deployed environments
- manual or incomplete Lambda artifact packaging flow
- structured-data loading scope limits relative to the W4 package
- any confirmed runtime or verification mismatch that materially affects operators

This section should make it obvious that successful infrastructure creation does not automatically mean the full app is production-usable.

#### 5. Verification split
Separate verification into distinct stages:
- infrastructure verification
- Bedrock and data verification
- browser and product verification

This helps operators distinguish “resources exist” from “the app works as expected.”

### Style requirements
The rewritten `docs/aws.md` should remain checklist-oriented and beginner-friendly.

It should:
- use numbered steps
- use exact commands where possible
- label each step by operator mode
- include expected results after important steps
- tell the operator when to stop and verify before continuing
- avoid presenting unresolved repo limitations as fully solved deployment behavior

## Output 2: `docs/app-functionality.md`

### Purpose
Create a single source of truth for all expected app functionality.

This document should track not only what is fully working, but also:
- partially wired frontend features
- backend or tool capabilities that exist but are not fully surfaced in the UI
- expected behaviors that are still missing
- the Bedrock-side capabilities needed to support each product behavior later

This document is intended to make future Bedrock agent configuration easier by mapping the product surface to retrieval, tool use, memory, grounding, and trace requirements.

### Required structure

#### 1. Narrative overview by product area
Start with short narrative sections for the major app areas:
- chat experience
- citations and grounding
- inspection console / observability
- live monitoring and structured data answers
- session memory and follow-up continuity
- degraded-mode and uncertainty behavior
- deployment/runtime dependencies that affect visible product behavior

Each section should summarize the expected behavior and the current repo state at a high level.

#### 2. Functionality status matrix
After the narrative overview, include a status matrix with one row per expected capability.

Required columns:
- Area
- Functionality
- Expected behavior
- User surface
- Backend or tool dependency
- Current state
- Current implementation notes
- Known gap or blocker
- Bedrock agent mapping
- Phase or priority

#### 3. Standardized status vocabulary
Use a fixed set of status values:
- `working`
- `partial`
- `mocked`
- `unwired`
- `missing`

This vocabulary should be defined once near the top of the document and used consistently in the matrix.

#### 4. Bedrock mapping requirements
Each functionality row should include a clear note about the Bedrock-side behavior needed to support that capability, such as:
- retrieval from the knowledge base only
- multi-source synthesis and contradiction handling
- structured historical data tool use
- live monitoring tool use
- session memory use
- trace shaping for the UI contract
- degraded-mode or uncertainty signaling

This turns the document into a future Bedrock configuration checklist instead of a passive inventory.

#### 5. Explicit tracking of partial wiring
The document should include two specific sections after the matrix:
- frontend features present but not fully wired
- backend or tooling capabilities present but not fully surfaced

These sections should summarize the key mismatches that the matrix captures in detail. Their purpose is to make current integration gaps easy to scan without reading the whole matrix.

### Content selection rules
The tracker should cover all expected app functionality, not only what is already implemented.

That includes:
- user-visible frontend behaviors
- backend response and trace behavior that the UI expects
- tool-backed product capabilities implied by W4 and project docs
- data-loading and retrieval-dependent functionality
- observability and explanation features expected in the right-side panel

It should not become a raw code inventory. Each row must be phrased as a product capability or expected system behavior.

## Document boundaries
- `docs/aws.md` is the deployment runbook
- `docs/app-functionality.md` is the product-capability tracker
- `docs/requirements.md` remains the higher-level requirements source

The new documents should cross-link where useful:
- `docs/aws.md` can point to `docs/app-functionality.md` when deployment outcomes affect product capabilities
- `docs/app-functionality.md` can point to `docs/aws.md` where runtime or deployment state affects feature availability

## Documentation update rules for implementation
When implementing this design:
- verify the final wording against the current repo state rather than copying assumptions from older docs
- keep statements precise when a capability is partial, mocked, or blocked
- avoid claiming support for data flows or agent behaviors that the repo does not currently prove
- update `TASKS.md` and any directly affected docs if the new documentation changes the repository’s tracking picture

## Success criteria
This work is complete when:
1. `docs/aws.md` has corrected deployment sequencing
2. `docs/aws.md` documents Bedrock setup as CLI-or-console rather than console-only
3. `docs/aws.md` makes the knowledge base upload and ingestion dependency explicit
4. `docs/aws.md` documents current repo limitations honestly
5. `docs/app-functionality.md` exists and tracks all expected app capabilities using a narrative overview plus a status matrix
6. the functionality tracker includes Bedrock agent mapping notes for each capability
7. tracking docs in the repo remain consistent after the change

## Implementation notes
- This task is documentation-only unless the user later asks for code or infrastructure fixes.
- The implementation should inspect the current frontend surface, backend response types, W4 package expectations, Terraform wiring, and deployment helper scripts before finalizing exact wording.
- The implementation should prefer a dedicated `docs/app-functionality.md` file rather than merging capability tracking into `docs/aws.md` or `docs/requirements.md`.
