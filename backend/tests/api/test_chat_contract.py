from fastapi.testclient import TestClient

from hexarag_api.main import create_app
from hexarag_api.models.chat import ChatMessage, ChatResponse, TracePayload


class FakeChatService:
    def answer(self, session_id: str, message: str) -> ChatResponse:
        return ChatResponse(
            session_id=session_id,
            message=ChatMessage(
                role='assistant',
                content=f'Factory answer for: {message}',
                trace=TracePayload(
                    citations=[],
                    inline_citations=[],
                    tool_calls=[],
                    memory_window=['prior turn'],
                    grounding_notes=['Returned by the fake chat service.'],
                    uncertainty=None,
                    conflict_resolution=None,
                    runtime={
                        'mode': 'stub',
                        'provider': 'stub-runtime',
                        'region': None,
                        'agent_id': None,
                        'agent_alias_id': None,
                        'model': 'deterministic-stub',
                    },
                    reasoning={
                        'evidence_types': ['memory'],
                        'selected_sources': [],
                        'tool_basis': [],
                        'memory_applied': True,
                        'memory_summary': 'Used the prior turn to scope the answer.',
                        'uncertainty_reason': None,
                        'answer_strategy': 'grounded-answer',
                        'runtime_label': 'deterministic-stub via stub-runtime',
                        'caveat': None,
                        'source_summary': 'No citations were available for this answer.',
                        'tool_summary': 'No tool calls were needed for this answer.',
                        'explanation_summary': 'The answer combined recent conversation context.',
                        'narrative_focus': 'evidence-synthesis',
                        'next_step': None,
                        'conflict_summary': None,
                    },
                ),
            ),
        )


def test_chat_route_delegates_to_factory_service(monkeypatch) -> None:
    from hexarag_api.api import chat as chat_api

    monkeypatch.setattr(chat_api, 'get_chat_service', lambda: FakeChatService())
    client = TestClient(create_app())

    response = client.post(
        '/chat',
        json={
            'session_id': 'route-session',
            'message': 'Who owns Notifications?',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'session_id': 'route-session',
        'message': {
            'role': 'assistant',
            'content': 'Factory answer for: Who owns Notifications?',
            'trace': {
                'citations': [],
                'inline_citations': [],
                'tool_calls': [],
                'memory_window': ['prior turn'],
                'grounding_notes': ['Returned by the fake chat service.'],
                'uncertainty': None,
                'conflict_resolution': None,
                'runtime': {
                    'mode': 'stub',
                    'provider': 'stub-runtime',
                    'region': None,
                    'agent_id': None,
                    'agent_alias_id': None,
                    'model': 'deterministic-stub',
                },
                'reasoning': {
                    'evidence_types': ['memory'],
                    'selected_sources': [],
                    'tool_basis': [],
                    'memory_applied': True,
                    'memory_summary': 'Used the prior turn to scope the answer.',
                    'uncertainty_reason': None,
                    'answer_strategy': 'grounded-answer',
                    'runtime_label': 'deterministic-stub via stub-runtime',
                    'caveat': None,
                    'source_summary': 'No citations were available for this answer.',
                    'tool_summary': 'No tool calls were needed for this answer.',
                    'explanation_summary': 'The answer combined recent conversation context.',
                    'narrative_focus': 'evidence-synthesis',
                    'next_step': None,
                    'conflict_summary': None,
                },
            },
        },
    }
