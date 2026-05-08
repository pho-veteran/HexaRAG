from typing import Any, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    version: str | None = None
    recency_note: str | None = None


class InlineCitationAnchor(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    source_ids: list[str] = Field(default_factory=list)


class ToolCallTrace(BaseModel):
    name: str
    status: Literal['success', 'error']
    summary: str
    input: dict[str, Any]
    output: dict[str, Any] | None


class ConflictResolution(BaseModel):
    chosen_source: str
    rationale: str
    competing_sources: list[str] = Field(default_factory=list)


class RuntimeTrace(BaseModel):
    mode: str
    provider: str
    region: str | None = None
    agent_id: str | None = None
    agent_alias_id: str | None = None
    model: str | None = None


class ReasoningTrace(BaseModel):
    evidence_types: list[str] = Field(default_factory=list)
    selected_sources: list[str] = Field(default_factory=list)
    tool_basis: list[str] = Field(default_factory=list)
    memory_applied: bool = False
    memory_summary: str | None = None
    uncertainty_reason: str | None = None
    answer_strategy: str = 'grounded-answer'
    runtime_label: str | None = None
    caveat: str | None = None
    source_summary: str | None = None
    tool_summary: str | None = None
    explanation_summary: str | None = None
    narrative_focus: str = 'evidence-synthesis'
    next_step: str | None = None
    conflict_summary: str | None = None


class TracePayload(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    inline_citations: list[InlineCitationAnchor] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    memory_window: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)
    uncertainty: str | None = None
    conflict_resolution: ConflictResolution | None = None
    runtime: RuntimeTrace
    reasoning: ReasoningTrace


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatMessage(BaseModel):
    role: Literal['assistant']
    content: str
    trace: TracePayload


class ChatResponse(BaseModel):
    session_id: str
    message: ChatMessage


class ErrorTrace(BaseModel):
    request: ChatRequest
    details: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str
    trace: ErrorTrace
