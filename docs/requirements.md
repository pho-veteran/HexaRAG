# HexaRAG Requirements

## 1. Product Overview

HexaRAG is a cloud-hosted AI question-answering application for the W4 GeekBrain project. It is designed as a polished, production-ish app that allows trainers and team members to ask freeform questions in a familiar chat interface while inspecting how the answer was produced.

The product experience is a ChatGPT-like chat UI with an always-visible observability panel. The chat area presents the conversation naturally. The observability panel exposes the retrieval, tool, memory, and grounding pipeline in a concise but evidence-rich format suitable for demos, debugging, and grading.

HexaRAG is AWS-native, Bedrock-first, and Terraform-deployed. It should primarily use Amazon Bedrock and Bedrock AgentCore for orchestration, retrieval/tool routing, and response generation. The frontend should be built with Vite and React. Local development, data seeding, and test execution must run through Docker Compose rather than directly on the host machine.

## 2. Goals

### 2.1 Primary goals
- Deliver a complete cloud-hosted app for the W4 project.
- Support W4 L1-L4 question patterns reliably.
- Make answer provenance and system behavior visible through the UI.
- Use AWS-native services with Bedrock and Bedrock AgentCore as the primary orchestration backbone.
- Be structured cleanly enough to feel maintainable and production-ish, not just a one-off demo script.

### 2.2 Secondary goals
- Support Bonus A through the built-in observability panel.
- Support Bonus C through scheduled knowledge base synchronization.
- Leave architectural room for L5-style multi-step investigations later.

## 3. Non-Goals

HexaRAG v1 does not need to include:
- user authentication or user accounts
- multi-tenant support
- admin dashboards or internal operations consoles
- generic bring-your-own-dataset workflows
- long-term memory or profile memory across sessions
- full L5 investigation support as a delivery requirement
- autonomous agent behavior beyond the W4 interaction model

## 4. Primary Users

### 4.1 Trainers
Trainers are external-facing users during the presentation and evaluation flow. They should be able to ask freeform questions, inspect supporting evidence, and understand how the system arrived at an answer.

### 4.2 Team members
Team members use HexaRAG to build, test, verify, and present the W4 solution. They need a clean chat UX plus enough observability to debug retrieval, tool use, and memory behavior.

## 5. Core User Experience

### 5.1 Main layout
HexaRAG v1 should provide a single primary screen.

- **Left side:** ChatGPT-like conversation interface
- **Right side:** Always-visible observability panel

The interface should be simple, concise, and readable. It should feel like a real product rather than a debugging dashboard with a chat box attached.

### 5.2 Chat experience requirements
The chat experience must:
- support freeform user questions
- show conversation history clearly
- support streamed or progressively revealed assistant responses
- preserve session continuity for follow-up questions
- avoid requiring predefined workflows or canned demos

### 5.3 Observability panel requirements
The observability panel must remain visible during the conversation and should expose the full trace for each answer, including:
- retrieved documents and chunks
- source metadata such as document name, version, and recency when available
- contradiction/conflict handling notes
- tool calls and returned data
- conversation memory context used for the turn
- final grounding summary
- uncertainty, failure, or degraded-mode notes

The panel must be concise enough for demo use but detailed enough to serve as evidence.

## 6. Source-of-Truth Model

HexaRAG must respect the W4 data boundaries.

### 6.1 Knowledge base documents
The markdown knowledge base documents are the source of truth for:
- policies
- team ownership
- service descriptions
- architecture context
- postmortem narratives
- qualitative planning and review notes

They are not the source of truth for exact historical numeric answers such as costs or daily metric values.

### 6.2 Structured data
The structured data source is the source of truth for exact historical and tabular values, including:
- monthly costs
- incidents
- SLA targets
- daily metrics

### 6.3 Live service data
The live monitoring service path is the source of truth for current operational state, including:
- service lists
- current status
- current latency
- current error rate
- current request volume
- current CPU and memory values where applicable

### 6.4 Session memory
Recent conversation turns are the source of truth for pronoun resolution and contextual follow-up references in L4-style chat.

## 7. W4 Capability Coverage

### 7.1 L1 — Retrieval
HexaRAG must answer single-document questions with the correct fact and cite the relevant source.

### 7.2 L2 — Multi-source retrieval
HexaRAG must synthesize information across multiple documents and resolve contradictions.

When multiple documents conflict, HexaRAG must follow the project announcement rule:
- check dates and version numbers
- prefer the most recent applicable source
- explain which source was trusted and why

### 7.3 L3 — Retrieval plus tools
HexaRAG must answer grounded numeric and live-state questions using tools and managed data integrations rather than relying on document retrieval alone.

### 7.4 L4 — Memory
HexaRAG must support recent-turn conversational continuity, including follow-up questions such as:
- “Why did its costs spike?”
- “Is it running normally right now?”
- “Which team is responsible for it?”

### 7.5 L5 stretch-readiness
L5-style investigation workflows are not required for v1 acceptance. However, the architecture and trace model should be designed so that future work can support:
- multiple tool calls per question
- multi-step investigation traces
- structured recommendation/report outputs
- more explicit execution sequencing in the observability panel

## 8. Functional Requirements

### FR1. Chat interaction
- The app must provide a single chat interface for freeform questioning.
- The app must support session-based conversation continuity.
- The app must return answers in a readable natural-language format.

### FR2. Bedrock and AgentCore orchestration
- The system must primarily use Amazon Bedrock and Bedrock AgentCore.
- AgentCore should serve as the main orchestration layer for deciding retrieval, tool use, and answer flow.
- HexaRAG must still define the tools, instructions, KB integration, session behavior, and UI-facing trace structure.

### FR3. Retrieval support
- The system must retrieve from the W4 knowledge base content stored in AWS.
- The system must surface source citations in the user answer and/or observability panel.
- The system must support multi-document retrieval and synthesis.

### FR4. Conflict resolution
- When documents conflict, the system must explicitly surface the discrepancy.
- The system must prefer the latest valid versioned source.
- The system must explain why that source was selected.

### FR5. Tool support
The system must support the W4 tool categories through AWS-first integrations or equivalent managed service-backed implementations:
- Service Status
- Service Metrics
- List Services
- Incident History
- Team Info
- Compare Services
- Database Query

### FR6. Grounded numeric answers
- Exact numbers must come from structured/live data, not from document-only retrieval.
- The app must support multi-source answers that combine live metrics, historical structured data, and document context.
- The system must clearly distinguish between current and historical values when both appear in the same answer.

### FR7. Observability
- Every answer must produce a structured trace that can be shown in the right-side panel.
- The trace must include retrieval activity, tool usage, memory context, and answer grounding.
- The trace must be readable by both team members and trainers.

### FR8. Session memory
- The system must include recent conversation context when appropriate.
- The system must resolve follow-up references using the active session window.
- The observability panel should show what memory context was used for the current answer.

### FR9. Graceful failure behavior
- If a tool fails, the system must not silently guess.
- If the system has partial evidence, it should provide the best grounded answer possible and clearly mark uncertainty.
- If the system cannot answer confidently, it must say so and expose what failed.

### FR10. Knowledge base synchronization
- The system must support scheduled KB synchronization.
- KB sync is a v1 requirement tied to Bonus C.
- The synchronization path should be schedule-driven rather than event-driven.

### FR11. Testing support
- Requirements must assume that the app will be validated against the W4 question sets under `W4/questions/student/`.
- The app should be testable against L1, L2, L3, and L4 scripts/questions.
- The product design should not block future validation against the L5 investigation prompts.

## 9. Non-Functional Requirements

### NFR1. Explainability
Every answer must be inspectable through visible evidence in the UI.

### NFR2. Reliability
The system must degrade visibly and safely when retrieval or tool operations fail.

### NFR3. No silent hallucination
The product must favor grounded incompleteness over confident fabrication.

### NFR4. Performance
The app should feel interactive in demo conditions and should avoid long silent waits. Streaming or visible progress is preferred.

### NFR5. Simplicity
The product should remain a single-surface chat app in v1.

### NFR6. Maintainability
The architecture should keep orchestration, retrieval, tools, memory, and UI concerns cleanly separated.

### NFR7. Containerized developer workflow
Local development, dependency installation, test execution, and data seeding must run through Docker Compose services rather than directly on the host machine.

### NFR8. Reusability
The implementation should be W4-optimized but should keep boundaries clean enough that the data sources or prompts could later be adapted.

### NFR9. Demo readiness
The UI and observability output should be usable directly for presentation screenshots and evidence capture.

## 10. System Architecture Requirements

HexaRAG should be implemented as an AWS-native system with Bedrock/AgentCore-centered orchestration.

### 10.1 Required component groups
The requirements assume these major component groups:
- Vite + React frontend web application
- backend application/API layer
- Bedrock/AgentCore orchestration layer
- knowledge base retrieval layer
- tool/data integration layer
- session memory handling
- trace/observability shaping layer
- Terraform-managed infrastructure

### 10.2 Architecture expectations
- The frontend should be implemented as a Vite + React single-page application and present one coherent product surface.
- The backend should shape requests and responses for the UI.
- AgentCore should handle as much orchestration as practical.
- Retrieval, tool usage, and memory context must be inspectable.
- The system must be designed around AWS-managed services where possible.

## 11. AWS Architecture Requirements

The app must be designed for all-cloud deployment on AWS.

### 11.1 Platform direction
- AWS-native hosting and service integration
- Bedrock and Bedrock AgentCore as primary AI platform services
- S3-backed knowledge base source content
- Terraform for repeatable provisioning

### 11.2 Documentation requirement
The project must include `aws.md` describing:
- which AWS services are provisioned
- how the app is deployed
- how networking and access are configured
- how Bedrock, KB sync, and tool integrations are wired together

This document should cover the configured AWS pieces such as networking, IAM, API/application routing, compute/runtime, and scheduled sync behavior.

## 12. Testing and Evaluation Requirements

### 12.1 Question-set alignment
HexaRAG must be designed to validate against:
- `L1_questions.json`
- `L2_questions.json`
- `L3_questions.json`
- `L4_conversation_scripts.json`

The design should also leave room for future evaluation against:
- `L5_investigation_prompts.json`

### 12.2 Behavior under test
The system must be able to demonstrate:
- single-doc retrieval accuracy
- multi-doc contradiction handling
- exact numeric grounding from tools/data
- session continuity across mixed retrieval/tool workflows

### 12.3 Test execution model
- Local test runs must execute through Docker Compose services.
- Frontend tests, backend tests, evaluator runs, and data-seeding flows must be available as containerized commands.
- The project should not require host-installed Node, Python, or database tooling for normal local development.

## 13. Success Criteria

HexaRAG v1 is successful if:
- trainers and team members can use it as a real chat app
- the app supports W4 L1-L4 patterns reliably
- the observability panel makes the answer pipeline visible and defensible
- contradiction handling follows the assignment policy exactly
- the system distinguishes docs vs structured data vs live state correctly
- the AWS deployment story is clear and Terraform-backed
- the product is polished enough for presentation without losing engineering transparency

## 14. Fixed Decisions

The following decisions are already fixed for HexaRAG v1:
- product direction: AWS-native product app for W4 with built-in observability
- deployment model: all cloud on AWS
- orchestration approach: primarily Bedrock and Bedrock AgentCore
- primary UI: single chat page
- frontend stack: Vite + React single-page application
- local developer workflow: Docker Compose only for app runtime, seeding, and tests
- layout: chat on the left, observability panel on the right
- auth: no authentication in v1
- memory model: session-window memory only
- capability balance: L1-L4 all treated as first-class requirements
- contradiction policy: prefer newer/versioned documents and explain why
- bonus scope: include observability and scheduled KB sync
- stretch scope: L5 investigation-readiness only, not full L5 delivery

## 15. Implementation Artifacts Expected Later

Beyond this requirements document, the project is expected to later include:
- `aws.md` for AWS deployment and architecture guidance
- Terraform configuration for provisioning the app infrastructure
- implementation plans derived from these requirements
- evidence-producing behaviors aligned with the W4 grading model
