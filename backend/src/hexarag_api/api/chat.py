from fastapi import APIRouter

from hexarag_api.config import get_settings
from hexarag_api.models.chat import ChatMessage, ChatRequest, ChatResponse
from hexarag_api.services.trace_formatter import build_trace_payload

FAILURE_TRIGGER_MESSAGE = 'trigger failure'
router = APIRouter()


class InMemoryTable:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, list[str]]] = {}

    def get_item(self, Key: dict[str, str]) -> dict[str, dict[str, list[str]]]:
        item = self.items.get(Key['session_id'])
        return {'Item': item} if item else {}

    def put_item(self, Item: dict[str, list[str] | str]) -> None:
        session_id = Item['session_id']
        turns = Item['turns']
        self.items[session_id] = {'session_id': session_id, 'turns': turns}


class StubAgentRuntime:
    def answer(self, session_id: str, message: str, memory_window: list[str]) -> dict:
        if message in {FAILURE_TRIGGER_MESSAGE, 'What is NotificationSvc status?'}:
            raise RuntimeError('live tool unavailable')

        return {
            'answer': f'Stub answer for: {message}',
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-architecture',
                        'title': 'architecture.md',
                        'excerpt': 'Current p95 latency sits below the alert threshold.',
                        'recency_note': 'Stubbed knowledge base note.',
                    }
                ],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'success',
                        'summary': 'Prepared stub observability data',
                        'input': {'question': message},
                        'output': {'mode': 'stub', 'latency_p95_ms': 185},
                    }
                ],
                'grounding_notes': ['This is a deterministic stub response for the Phase 2 runtime slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        }


session_store_table = InMemoryTable()
agent_runtime = StubAgentRuntime()


@router.post('/chat', response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    from hexarag_api.services.session_store import SessionStore

    settings = get_settings()
    session_store = SessionStore(session_store_table)
    memory_window = session_store.load_recent_turns(request.session_id, limit=settings.recent_turn_limit)

    try:
        runtime_output = agent_runtime.answer(request.session_id, request.message, memory_window)
        trace = build_trace_payload(runtime_output['trace'], memory_window)
        content = runtime_output['answer']
    except RuntimeError:
        content = settings.failure_message
        trace = build_trace_payload(
            {
                'citations': [],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'error',
                        'summary': 'Live monitoring call failed.',
                        'input': {'question': request.message},
                        'output': None,
                    }
                ],
                'grounding_notes': ['Returned fallback answer because the live tool step failed.'],
                'uncertainty': 'Live monitoring data is temporarily unavailable.',
            },
            memory_window,
        )

    session_store.append_turns(request.session_id, request.message, content)
    return ChatResponse(
        session_id=request.session_id,
        message=ChatMessage(role='assistant', content=content, trace=trace),
    )
