from fastapi.testclient import TestClient

from hexarag_api.main import app

client = TestClient(app)


def test_chat_returns_stubbed_message_and_trace() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 'phase1-session',
            'message': 'What is PaymentGW latency?',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'session_id': 'phase1-session',
        'message': {
            'role': 'assistant',
            'content': 'Stub answer for: What is PaymentGW latency?',
            'trace': {
                'citations': [
                    {
                        'source_id': 'doc-architecture',
                        'title': 'architecture.md',
                        'excerpt': 'Current p95 latency sits below the alert threshold.',
                        'version': None,
                        'recency_note': 'Stubbed knowledge base note.',
                    }
                ],
                'tool_calls': [
                    {
                        'name': 'monitoring_snapshot',
                        'status': 'success',
                        'summary': 'Prepared stub observability data',
                        'input': {'question': 'What is PaymentGW latency?'},
                        'output': {'mode': 'stub', 'latency_p95_ms': 185},
                    }
                ],
                'memory_window': ['No prior turns in Phase 1 single-turn mode.'],
                'grounding_notes': ['This is a deterministic stub response for the Phase 1 vertical slice.'],
                'uncertainty': 'Live systems are not wired in this slice.',
            },
        },
    }


def test_chat_returns_structured_error_details_for_failure_mode() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 'phase1-session',
            'message': 'trigger failure',
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        'error': 'Unable to generate stub response.',
        'trace': {
            'request': {
                'session_id': 'phase1-session',
                'message': 'trigger failure',
            },
            'details': ['Stub failure requested for UI error-state coverage.'],
        },
    }
