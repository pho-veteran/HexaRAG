from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from hexarag_api.models.chat import (
    Citation,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ErrorTrace,
    ToolCallTrace,
    TracePayload,
)

FAILURE_TRIGGER_MESSAGE = 'trigger failure'

router = APIRouter()


@router.post('/chat', response_model=ChatResponse, responses={502: {'model': ErrorResponse}})
async def post_chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    if request.message == FAILURE_TRIGGER_MESSAGE:
        error_payload = ErrorResponse(
            error='Unable to generate stub response.',
            trace=ErrorTrace(
                request=request,
                details=['Stub failure requested for UI error-state coverage.'],
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=error_payload.model_dump(),
        )

    return ChatResponse(
        session_id=request.session_id,
        message=ChatMessage(
            role='assistant',
            content=f'Stub answer for: {request.message}',
            trace=TracePayload(
                citations=[
                    Citation(
                        source_id='doc-architecture',
                        title='architecture.md',
                        excerpt='Current p95 latency sits below the alert threshold.',
                        recency_note='Stubbed knowledge base note.',
                    )
                ],
                tool_calls=[
                    ToolCallTrace(
                        name='monitoring_snapshot',
                        status='success',
                        summary='Prepared stub observability data',
                        input={'question': request.message},
                        output={'mode': 'stub', 'latency_p95_ms': 185},
                    )
                ],
                memory_window=['No prior turns in Phase 1 single-turn mode.'],
                grounding_notes=['This is a deterministic stub response for the Phase 1 vertical slice.'],
                uncertainty='Live systems are not wired in this slice.',
            ),
        ),
    )
