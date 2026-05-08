from hexarag_api.models.chat import ChatMessage, ChatResponse
from hexarag_api.services.trace_formatter import build_trace_payload


class ChatService:
    def __init__(self, session_store, runtime, recent_turn_limit: int, failure_message: str) -> None:
        self.session_store = session_store
        self.runtime = runtime
        self.recent_turn_limit = recent_turn_limit
        self.failure_message = failure_message

    def answer(self, session_id: str, message: str) -> ChatResponse:
        memory_window = self.session_store.load_recent_turns(session_id, limit=self.recent_turn_limit)

        try:
            runtime_output = self.runtime.answer(session_id, message, memory_window)
            content = runtime_output['answer']
            trace = build_trace_payload(runtime_output.get('trace', {}), memory_window)
        except RuntimeError:
            content = self.failure_message
            trace = build_trace_payload(
                {
                    'citations': [],
                    'inline_citations': [],
                    'tool_calls': [
                        {
                            'name': 'monitoring_snapshot',
                            'status': 'error',
                            'summary': 'Live monitoring call failed.',
                            'input': {'question': message},
                            'output': None,
                        }
                    ],
                    'grounding_notes': ['Returned fallback answer because the live tool step failed.'],
                    'uncertainty': 'Live monitoring data is temporarily unavailable.',
                },
                memory_window,
            )

        self.session_store.append_turns(session_id, message, content)
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(role='assistant', content=content, trace=trace),
        )
