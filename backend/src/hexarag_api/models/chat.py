from typing import Any, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    version: str | None = None
    recency_note: str | None = None


class ToolCallTrace(BaseModel):
    name: str
    status: Literal['success', 'error']
    summary: str
    input: dict[str, Any]
    output: dict[str, Any] | None


class TracePayload(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    memory_window: list[str] = Field(default_factory=list)
    grounding_notes: list[str] = Field(default_factory=list)
    uncertainty: str | None = None


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
