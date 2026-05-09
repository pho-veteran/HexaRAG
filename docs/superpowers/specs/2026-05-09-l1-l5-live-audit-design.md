# L1-L5 Live Audit and Tuning Design

## Goal
Run a full live audit of HexaRAG against the W4 student question sets from L1 through L5, tune the deployed system based on the findings, and produce evidence-backed readiness guidance for both grading fit and product quality.

This design is intentionally broader than the existing local evaluator pass. The goal is not only to prove that the repo can replay prompts, but to verify that the deployed product behaves correctly, visibly, and defensibly under the real W4 question patterns.

## Why this work is needed
The repository already includes local evaluation tooling and deployment tracking, but the current state still leaves gaps between “deployed and answering” and “ready for L1-L5 expectations in a real product.”

Known reasons this work is needed include:
- `docs/requirements.md` defines L1-L4 as first-class requirements and L5 as stretch-readiness rather than full v1 delivery.
- `docs/app-functionality.md` still marks several relevant capabilities as `partial` or `unwired`, especially citations, live monitoring coverage, structured historical data coverage, mixed-source synthesis, and follow-up resolution consistency.
- `aws-tracking.md` records that deployed retrieval answers can still miss normalized citations and that structured-data and monitoring coverage remain narrower than the full W4 package.
- The existing evaluation path in `backend/scripts/evaluate_w4.py` is useful for replay and smoke validation, but it is not yet the source of truth for a full deployed-product readiness judgment.

Because of those gaps, the next step should be a real audit-and-tuning loop against the live product rather than another repo-local-only verification pass.

## Scope
This design covers one coordinated audit-and-tuning project with six connected outputs:
- a deployed API audit over the full L1-L5 question corpus
- a curated live-UI validation pass for representative high-risk cases
- a scoring model for both W4 grading fit and product quality
- a root-cause taxonomy for failures by system layer
- a tuning loop that can change any layer needed to improve readiness
- a final readiness report with evidence, blockers, and prioritized improvements

In scope:
- reading and organizing the W4 student fixtures under `W4/questions/student`
- running the deployed `/chat` surface against the question corpus
- validating representative cases through the deployed CloudFront UI
- recording raw outputs, traces, timings, and visible UI behavior
- classifying failures by layer: agent config, knowledge base content, structured data coverage, monitoring/tooling coverage, backend shaping, frontend rendering, or AWS/runtime drift
- tuning the live system by changing the Bedrock agent configuration, backend code, frontend code, AWS wiring, knowledge-base ingestion inputs, data/tool coverage, evaluation tooling, and repo docs where necessary
- re-running targeted and broader verification after each tuning pass
- updating tracking and documentation so the final repo state truthfully describes readiness

Out of scope:
- unrelated cleanup or refactoring not tied to observed audit failures
- broad product expansion beyond the W4 expectations being evaluated
- claiming full autonomous L5 delivery if the result is only investigation-readiness
- inventing a host-native workflow outside the Docker Compose rules in this repo

## Audit objective model
The audit should judge the system on two dimensions at the same time.

### Dimension A: W4 grading fit
This dimension checks whether a given answer behaves in the way the W4 level expects.

Examples:
- L1 must retrieve the correct fact from the right document and support it with source evidence.
- L2 must synthesize across sources and resolve contradictions by preferring the newest valid source.
- L3 must use structured or live sources for exact numeric and current-state questions rather than relying on docs alone.
- L4 must preserve session continuity across follow-up turns in one active session.
- L5 must show credible investigation-oriented behavior, evidence gathering, and recommendation structure, while staying honest about limits.

### Dimension B: Product quality
This dimension checks whether the deployed product is presentation-ready and inspectable.

Examples:
- the answer is readable and useful on its own
- citations and trace data are visible and coherent
- the UI does not crash, hang, or hide relevant evidence
- degraded paths are explicit and honest rather than silently wrong
- runtime, grounding, and memory surfaces are inspectable enough for demos and grading defense

A question can therefore be “technically close” but still fail overall if the visible product behavior is weak, misleading, or unstable.

## Design overview
The audit should use a staged hybrid model.

1. Build an executable audit matrix from the L1-L5 fixture files.
2. Run the full corpus against the deployed API as the main repeatable evaluation surface.
3. Re-run a curated subset through the deployed UI to validate the real trainer-facing experience.
4. Score each case across grading fit and product quality.
5. Cluster failures by root cause layer.
6. Tune only the layers implicated by observed failures.
7. Re-run impacted cases first, then broader sweeps.
8. Publish a readiness report with evidence, blockers, and prioritized next actions.

This structure gives breadth from the API sweep and realism from the UI pass without making the UI the bottleneck for every question.

## Workstream A: Build the audit matrix
The current W4 fixture set is the source of truth for what must be tested.

### Inputs
The matrix should be built from:
- `W4/questions/student/L1_questions.json`
- `W4/questions/student/L2_questions.json`
- `W4/questions/student/L3_questions.json`
- `W4/questions/student/L4_conversation_scripts.json`
- `W4/questions/student/L5_investigation_prompts.json`

### Matrix contents
Each test case in the matrix should include:
- level and case identifier
- original prompt or script
- expected behavior type
- expected source-of-truth boundary
- expected trace/evidence pattern
- expected contradiction-handling or memory behavior when applicable
- audit surface requirements: API only, UI only, or both
- pass/partial/fail result slots for grading fit and product quality
- notes for root cause and recommended fix layer

### Boundary rule
The matrix should not reduce expectations to a brittle exact-answer string check. It must evaluate whether the answer came from the correct evidence path and whether the result is defensible in the product.

## Workstream B: Full deployed API audit
The live `/chat` API should be the primary audit surface because it is broad, repeatable, and captures the normalized trace contract.

### Why the API is primary
The API gives the best leverage for:
- full corpus execution
- repeatable re-runs after tuning
- structured capture of message, trace, error, and runtime metadata
- easier clustering of failures by source-of-truth or trace behavior

### Required execution behavior
The API audit should:
- use the deployed backend URL, not a local service URL
- preserve L4 and L5 conversational continuity where the script requires it
- capture raw response payloads in a durable results ledger
- capture request timing and failure modes
- keep level-specific session behavior explicit rather than mixing unrelated conversations into one session

### Session rules
- L1-L3 single-turn cases can use isolated sessions per case.
- L4 scripts must reuse one session per script.
- L5 prompts may require a judgment about whether a single turn or a short structured follow-up sequence is needed to evaluate investigation behavior; that should be recorded explicitly per case.

## Workstream C: Curated live UI validation
The deployed CloudFront UI should be the secondary audit surface for representative, high-risk cases.

### Purpose
The UI pass exists to verify that product behavior matches backend capability rather than assuming the API contract is enough.

### Required UI coverage
The UI subset should include at least:
- L1 cases where citations are expected to be visible
- L2 cases with contradiction handling and recency selection
- L3 cases requiring historical numeric grounding and live-state grounding
- L4 follow-up chains that rely on memory and mixed evidence types
- L5 prompts that test whether the interface presents a credible investigation-oriented response with visible evidence and caveats

### UI behaviors under audit
The UI validation should check:
- answer rendering
- sending/loading behavior
- visible citation behavior
- trace panel completeness
- memory panel usefulness
- contradiction/conflict visibility
- uncertainty and degraded-mode behavior
- whether the UI crashes, hangs, or obscures the evidence needed for defense

## Workstream D: Scoring model
The scoring model should be structured enough for repeatability but flexible enough to reflect real product quality.

### Per-case result fields
Each case should record:
- `grading_fit`: pass / partial / fail
- `product_quality`: pass / partial / fail
- `overall_readiness`: pass / partial / fail
- `primary_failure_layer`
- `secondary_failure_layers`
- `evidence_summary`
- `improvement_insight`
- `retest_priority`

### Decision rules
- **Pass** means the behavior meets the level expectation and is defensible in the product.
- **Partial** means the system got part of the behavior right but still violated an expectation, used the wrong evidence path, or exposed weak/unclear product behavior.
- **Fail** means the answer was materially wrong, ungrounded, unstable, or unsupported by the visible product surfaces.

### L5 scoring rule
L5 should be evaluated as investigation-readiness, not full autonomous research completion.

A strong L5 result should show:
- a useful investigation structure
- credible evidence gathering or evidence-grounded recommendations
- correct distinction between facts, assumptions, and uncertainty
- trace quality that makes the reasoning process defensible

A weak L5 result includes:
- pretending to have performed multi-step evidence gathering when it did not
- generic advice with no grounding in the W4 corpus or tools
- no visible structure, no caveats, or no inspectable evidence

## Workstream E: Failure taxonomy
The audit should classify failures by the layer most likely to fix them.

### Expected failure layers
Use a fixed taxonomy such as:
- `agent_instruction_or_behavior`
- `knowledge_base_content_or_ingestion`
- `structured_data_coverage`
- `monitoring_or_tool_coverage`
- `backend_runtime_or_trace_shaping`
- `session_memory_behavior`
- `frontend_rendering_or_interaction`
- `aws_runtime_or_configuration`
- `evaluation_or_scoring_gap`

### Why this matters
Without a stable taxonomy, tuning turns into anecdotal debugging. With a stable taxonomy, patterns become visible across levels, such as:
- L1/L2 failures clustering around citation normalization
- L3 failures clustering around missing structured datasets or missing tool routes
- L4 failures clustering around session state handling
- L5 failures clustering around weak investigation structure or mixed-source synthesis gaps

## Workstream F: Tuning loop
The tuning loop should be evidence-driven and intentionally narrow.

### Tuning policy
For each failed or partial case:
1. identify the source-of-truth violation or product-quality violation
2. map it to one or more failure layers
3. choose the smallest effective fix
4. verify the fix against the impacted cases first
5. run a broader regression sweep before claiming improvement

### Allowed tuning surfaces
Because the user explicitly allowed “anything needed,” the tuning phase may modify:
- Bedrock agent instructions and configuration
- agent/KB association and ingestion inputs
- backend tool/data logic
- backend runtime normalization and trace shaping
- session memory behavior
- frontend rendering and interaction paths
- AWS configuration that affects observed behavior
- evaluation scripts, scoring logic, and audit artifacts
- tracking and documentation

### Guardrail
This is not a license for unrelated cleanup. Every change must tie back to an observed audit failure or to a prerequisite needed to make the audit trustworthy.

## Workstream G: Artifacts and reporting
The audit should produce durable artifacts rather than one-off notes.

### Required artifacts
- an audit matrix derived from the W4 fixtures
- raw deployed API results for the full corpus
- a curated UI validation checklist and findings log
- a per-case results ledger
- a failure taxonomy summary by level and by system layer
- a prioritized improvement backlog
- a final readiness report

### Final readiness report
The final report should summarize:
- pass/partial/fail distribution by level
- the biggest blockers to product readiness
- the most effective fixes that improved readiness
- remaining risks and open caveats
- whether the deployed system is ready to be presented as L1-L4 reliable and L5 investigation-ready

## Technical decisions

### Decision 1: the deployed API is the main evaluation surface
A live product audit needs breadth and repeatability. The deployed API provides that better than a UI-only flow.

### Decision 2: the UI is a validation surface, not the main batch runner
The product must still be judged through the UI, but the UI should validate representative high-risk cases rather than serve as the full-corpus execution bottleneck.

### Decision 3: score source-of-truth behavior, not only text similarity
The important question is not just whether an answer sounds plausible. It is whether the answer used the correct evidence path and exposed it clearly.

### Decision 4: L5 is investigation-readiness, not full autonomous delivery
This keeps the audit aligned with `docs/requirements.md` and avoids grading the product against a scope the repo has not claimed as complete.

### Decision 5: tune by observed failure clusters
The best next fixes should come from repeated patterns across the corpus, not from whichever individual answer happened to look worst first.

## Rollout sequence
1. inventory the L1-L5 fixture files and build the audit matrix
2. define the scoring schema and failure taxonomy
3. run the first full deployed API sweep
4. inspect the results and identify high-risk representative UI cases
5. run the first UI validation pass
6. cluster failures by layer and prioritize fixes
7. implement the highest-impact tuning changes
8. re-run impacted cases and confirm improvement
9. run broader regression sweeps across the affected levels
10. update docs and tracking files to match the new readiness state
11. publish the final readiness report and improvement insights

## Verification strategy
Verification should happen in rings.

### Ring 1: audit-runner trustworthiness
Confirm that the audit tooling itself correctly loads W4 fixtures, preserves session boundaries, records traces, and emits stable structured results.

### Ring 2: targeted regression after each fix
After each tuning change, re-run only the impacted cases first so cause and effect stay clear.

### Ring 3: level-wide regression
Once targeted fixes hold, re-run the affected level or levels to check for collateral regressions.

### Ring 4: final cross-level readiness sweep
At the end, run a final sweep across L1-L5 and the curated UI subset to produce the readiness summary.

## Risks and controls

### Risk: overfitting to a few benchmark answers
Control: keep the full-corpus API sweep as the main benchmark and avoid judging success from a small handpicked set.

### Risk: confusing backend correctness with product readiness
Control: always pair the API audit with a curated live UI pass that checks the user-visible experience.

### Risk: blaming the wrong system layer
Control: use a stable failure taxonomy and require evidence before making cross-layer changes.

### Risk: scope blow-up through open-ended tuning
Control: allow any layer to change, but only when the change is linked to a documented observed failure or audit prerequisite.

### Risk: claiming L5 support beyond what the product truly provides
Control: keep L5 framed as investigation-readiness and document limits honestly in the final report.

## Success criteria
This work is complete when:
1. the full L1-L5 fixture set has been audited against the deployed API with recorded results
2. a curated representative subset has been validated through the deployed UI
3. each case has a structured grading-fit and product-quality result
4. failures have been clustered into a stable root-cause taxonomy
5. the highest-impact failure clusters have been tuned and re-tested
6. the repo docs and trackers truthfully describe the post-audit readiness state
7. the final report can defend whether HexaRAG is product-ready for L1-L4 and investigation-ready for L5
8. remaining limitations are explicit rather than hidden behind optimistic summary language

## Non-goals reminder
This design does not promise that every L5 prompt will become a fully autonomous investigation workflow. It is focused on making the deployed HexaRAG product reliable, inspectable, and defensible against the W4 L1-L5 expectations it actually claims to support.