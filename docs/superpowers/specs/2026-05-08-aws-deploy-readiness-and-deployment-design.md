# AWS Deploy Readiness and Deployment Design

## Goal
Prepare HexaRAG so the repository can be deployed to AWS in a way that truthfully matches the live product behavior described in `docs/app-functionality.md`, then execute the AWS deployment with a clear operator path.

This design is intentionally not a docs-only pass. It covers the minimum code, infrastructure, packaging, and documentation work required so a deployed environment does not merely create AWS resources, but actually supports the expected frontend behavior and backend runtime contract.

## Why this work is needed
The repository currently has a mismatch between documented capability and deployed behavior:

- `backend/src/hexarag_api/api/chat.py` still hardcodes a stub runtime path for `/chat`.
- `backend/src/hexarag_api/services/agent_runtime.py` exists, but is not the active chat path.
- `frontend/src/lib/api.ts` falls back to `http://localhost:8000` unless `VITE_API_BASE_URL` is supplied at build time.
- `backend/src/hexarag_api/config.py` and `backend/src/hexarag_api/main.py` currently model CORS as a single origin, which is not robust for local plus deployed operation.
- `infra/terraform/outputs.tf` does not expose the CloudFront domain, which forces console lookup during deployment.
- `docs/aws.md` still treats Bedrock prerequisites and Lambda packaging as manual checkpoints rather than a repo-owned deployment path.

Because of those gaps, deploying the repository as-is would stand up infrastructure but still leave the user-visible app short of the intended runtime behavior.

## Scope
This design covers two tracks that must be executed together.

### Track A: Make the deployed runtime truthful
Bring the actual `/chat` runtime path in line with the documented application behavior.

In scope:
- replace the permanently stub-backed chat path with an explicit runtime-selection service
- keep the existing request and response contract centered on `session_id` and `ChatResponse.message.trace`
- preserve the frontend-facing trace shape for citations, inline citations, tool calls, memory window, grounding notes, and uncertainty
- ensure deployed AWS mode uses the real Bedrock/AgentCore-backed runtime path
- keep a clearly named local stub mode for development or fallback scenarios only

### Track B: Close deployment-critical gaps
Make the AWS deployment flow deterministic enough that the frontend and backend work together correctly after deployment.

In scope:
- deployment-safe frontend API URL wiring
- deployment-safe backend origin/CORS configuration
- complete Terraform outputs for operator use
- repo-owned Lambda packaging flow
- Bedrock prerequisite and knowledge-base sequencing clarity
- documentation and tracker updates that match the real post-change state

## Out of scope
- expanding scope into L5 multi-step investigation features
- redesigning the frontend UI
- broad refactoring unrelated to chat/runtime/deployment readiness
- inventing alternate host-native workflows outside Docker Compose
- replacing the AWS-native architecture with a different deployment model

## Design overview
The work should be executed as a two-track readiness pass followed by deployment.

1. Make the deployed backend truthful about how `/chat` is answered.
2. Remove the deployment wiring gaps that would break the frontend in AWS.
3. Verify the contract locally through Docker Compose.
4. Create or locate AWS Bedrock prerequisites.
5. Package Lambda artifacts from a repo-owned flow.
6. Apply Terraform and publish the frontend.
7. Upload and ingest knowledge-base data.
8. Verify backend, monitoring, retrieval, and browser behavior end to end.

This keeps the code changes focused on deploy-readiness rather than turning the task into a broad product rewrite.

## Workstream A: Backend runtime truthfulness
The current route in `backend/src/hexarag_api/api/chat.py` mixes HTTP handling, in-memory session persistence, stub runtime invocation, and fallback behavior in one module. The deployment-ready design separates those responsibilities.

### Intended architecture
Introduce a chat service boundary responsible for:
- loading recent turns from session storage
- invoking the selected runtime implementation
- normalizing runtime output into the expected app contract
- shaping the trace through the trace formatter
- persisting new turns after the response is produced

The `/chat` route should be reduced to request parsing, service invocation, and response construction.

### Runtime mode model
Add explicit runtime mode selection in backend settings.

Required modes:
- `stub` for local deterministic fallback behavior
- `aws` for the real Bedrock/AgentCore path

The deployed Lambda path must use `aws` mode by configuration rather than silently falling back to stub behavior.

### Fallback behavior
Fallback behavior should remain explicit and honest. If a live runtime or tool call fails, the response may still return a grounded fallback message, but it must surface uncertainty and tool failure information through the trace contract rather than pretending the answer came from a healthy live path.

## Workstream B: Runtime capability alignment
The frontend already expects a richer trace contract than a plain text chat response. That contract should continue to be shaped centrally by backend services rather than patched in the frontend.

### Required response contract properties
The live runtime path must preserve support for:
- citations
- inline citation anchors
- tool call traces
- `memory_window`
- `grounding_notes`
- `uncertainty`

### Boundary rule
The trace formatter remains the single backend boundary that shapes the UI-facing trace payload. If runtime output needs normalization, that normalization belongs in backend service code, not in ad hoc frontend mapping changes beyond the existing centralized aliasing.

### Success condition for this workstream
A frontend built against the deployed backend should still be able to render the observability panel, referenced document rows, inline citations, thinking-process narrative inputs, and degraded-mode surfaces without requiring a UI redesign.

## Workstream C: AWS deployment correctness
The current deployment flow has frontend/backend coordination gaps that can make a successful infrastructure deployment behave like a broken app.

### Frontend API base URL
Keep the frontend API wiring build-time based, but make the deployment path deterministic:
- the backend API URL must be easy to retrieve from Terraform outputs
- deployment docs must show the exact build step that injects `VITE_API_BASE_URL`
- frontend deployment verification must explicitly catch localhost fallback mistakes

### Backend origin handling
Replace the single-origin configuration with an intentional origin list model.

The configuration should support:
- local frontend origin during development
- deployed CloudFront origin in AWS
- explicit operator configuration rather than hidden behavior

This keeps the backend safe while allowing normal browser operation from the deployed frontend.

### Terraform operator usability
Extend outputs so operators can retrieve all critical deployed values without opening the AWS Console for guesswork.

At minimum expose:
- backend API URL
- monitoring API URL
- frontend bucket name
- knowledge-base bucket name
- CloudFront distribution domain
- session table name
- PostgreSQL endpoint

If Terraform already knows a value that operators need in the documented flow, it should be exposed as an output rather than delegated to manual console discovery.

## Workstream D: Bedrock and packaging readiness
The current deployment guide still leaves two major gaps: Bedrock setup is partially externalized and Lambda packaging is not owned by the repo workflow.

### Bedrock prerequisites
The deployment sequence must clearly describe how to create or locate:
- `knowledge_base_id`
- `knowledge_base_data_source_id`
- `agent_runtime_arn`

The documentation must be precise about what Terraform consumes versus what this repo does not create directly.

### Knowledge-base sequencing
The deployment path must make these dependencies explicit:
1. create or locate the Bedrock resources
2. apply infrastructure that provisions the knowledge-base S3 bucket
3. upload knowledge-base markdown into the bucket
4. trigger ingestion only after the upload is complete
5. verify ingestion finishes successfully before trusting retrieval behavior

### Packaging
Add a repo-owned packaging flow that predictably creates:
- `infra/terraform/backend.zip`
- `infra/terraform/monitoring.zip`
- `infra/terraform/kb-sync.zip`

The exact implementation can be a script, a Docker Compose driven helper, or another repo-native step, but it must be documented as the canonical packaging path. The goal is to eliminate the current vague “assemble artifacts somehow, then zip them manually” checkpoint.

## Workstream E: Documentation and tracker truthfulness
Documentation is part of the deliverable, not cleanup after the fact.

Required document updates:
- `docs/aws.md`
- `docs/app-functionality.md`
- `TASKS.md`
- any active plan file whose sequencing or ownership assumptions materially change

### Documentation rule
After the readiness pass, those documents must describe the same reality:
- what the repo can do locally
- what the repo can do when deployed to AWS
- which app-functionality expectations are now working, partial, unwired, or missing
- which deployment steps are still manual versus automated

## Technical decisions

### Decision 1: explicit runtime mode instead of implicit stub behavior
The system should never infer that stub mode is acceptable in production. Production readiness requires a named AWS mode and a named stub mode so failures are operationally visible.

### Decision 2: chat route stays thin
The route layer should remain an HTTP boundary only. Orchestration belongs in services so runtime selection, fallback policy, memory loading, trace shaping, and persistence stay inspectable and testable.

### Decision 3: preserve the current response contract
The frontend already expects a stable contract. This pass should preserve that shape and make the backend more truthful rather than forcing a new UI protocol.

### Decision 4: deployment information comes from Terraform outputs where possible
If the deployment guide tells an operator to fetch a value that Terraform can already expose, the preferred fix is an output, not more console instructions.

### Decision 5: packaging must be repo-owned
A deployable repository should provide its own artifact creation path. Operator instructions may still be manual at the outermost layer, but the zip creation process itself should no longer be vague.

## Rollout sequence
1. Implement backend runtime selection and chat service composition.
2. Update configuration for multi-origin operation and AWS mode selection.
3. Add or update the packaging path for Lambda artifacts.
4. Extend Terraform outputs and any required env wiring.
5. Update `docs/aws.md`, `docs/app-functionality.md`, and `TASKS.md` to match the new state.
6. Verify locally through Docker Compose that the contract and build steps still work.
7. Use AWS credentials to create or locate Bedrock prerequisites.
8. Package artifacts, apply Terraform, build the frontend with the deployed backend URL, and publish assets.
9. Upload knowledge-base documents and run ingestion.
10. Verify backend, monitoring, retrieval, and frontend behavior in the deployed environment.

## Verification strategy
Verification must happen in layers rather than treating “Terraform apply succeeded” as proof that the product works.

### Local verification
- backend tests for chat contract, trace shaping, and session behavior
- frontend tests for chat rendering, trace rendering, and inline citation handling
- frontend build with Docker Compose
- packaging output existence checks

### Deployment verification
- Terraform init, fmt, and validate
- Terraform apply success
- frontend asset upload success
- backend API responds from deployed URL
- monitoring API responds from deployed URL
- browser frontend loads through CloudFront and does not call localhost
- deployed `/chat` is not permanently stub-backed
- retrieval path works only after knowledge-base ingestion is complete

### Product verification
Confirm the deployed app still supports the expected user-visible surfaces:
- chat UI renders
- observability panel renders
- assistant response selection works
- citations render when provided
- tool-call trace data renders when provided
- uncertainty and degraded-mode surfaces appear when required

## Risks and controls

### Risk: the real AgentCore runtime response shape may differ from the stub assumptions
Control: normalize runtime output in the backend service layer before trace formatting instead of leaking raw runtime payloads into route code.

### Risk: deployed frontend/browser requests fail due to CORS misconfiguration
Control: move from single-origin config to explicit multi-origin configuration and verify against the deployed CloudFront origin.

### Risk: packaging becomes environment-specific or undocumented
Control: make one canonical packaging path and document it as the only supported deployment artifact flow.

### Risk: docs drift away from code during implementation
Control: treat docs and tracker updates as part of the same task and verify them before declaring readiness.

## Success criteria
This work is complete when:
1. `/chat` is no longer permanently stub-backed in deployed mode.
2. the backend has explicit runtime selection with a real AWS mode and a clearly bounded stub mode.
3. the frontend can be built against the deployed backend URL without localhost fallback mistakes.
4. the backend accepts the intended deployed browser origin configuration.
5. Terraform outputs expose the operator values needed for deployment and verification, including the CloudFront domain.
6. the repo has a canonical packaging path for the required Lambda zip artifacts.
7. `docs/aws.md`, `docs/app-functionality.md`, and `TASKS.md` all match the post-change reality.
8. the AWS deployment can be executed from the repo with Bedrock prerequisites, packaging, infrastructure apply, frontend publish, KB upload, and KB ingestion in a clear sequence.
9. the deployed frontend can talk to the deployed backend and render the expected trace-driven experience.

## Non-goals reminder
This design intentionally stops short of unrelated feature work. It is about making the existing v1 architecture truthful and deployable on AWS, not turning the project into a larger platform rewrite.
