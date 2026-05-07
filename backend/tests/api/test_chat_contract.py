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
    payload = response.json()
    assert payload['session_id'] == 'phase1-session'
    assert payload['message']['role'] == 'assistant'
    assert 'trace' in payload['message']
    assert 'citations' in payload['message']['trace']


def test_chat_returns_grounded_failure_when_runtime_errors() -> None:
    response = client.post(
        '/chat',
        json={
            'session_id': 's-1',
            'message': 'What is NotificationSvc status?',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 'could not complete the live tool step' in payload['message']['content'].lower()
    assert payload['message']['trace']['citations'] == []
    assert payload['message']['trace']['tool_calls'][0] == {
        'name': 'monitoring_snapshot',
        'status': 'error',
        'summary': 'Live monitoring call failed.',
        'input': {'question': 'What is NotificationSvc status?'},
        'output': None,
    }
    assert payload['message']['trace']['grounding_notes'] == [
        'Returned fallback answer because the live tool step failed.'
    ]
    assert payload['message']['trace']['uncertainty'] == 'Live monitoring data is temporarily unavailable.'


def test_chat_keeps_memory_window_when_degraded_after_a_successful_turn() -> None:
    session_id = 's-memory'

    first_response = client.post(
        '/chat',
        json={
            'session_id': session_id,
            'message': 'What is PaymentGW latency?',
        },
    )
    assert first_response.status_code == 200

    degraded_response = client.post(
        '/chat',
        json={
            'session_id': session_id,
            'message': 'What is NotificationSvc status?',
        },
    )

    assert degraded_response.status_code == 200
    payload = degraded_response.json()
    assert payload['message']['trace']['memory_window'] == [
        'What is PaymentGW latency?',
        'Stub answer for: What is PaymentGW latency?',
    ]
    assert payload['message']['trace']['tool_calls'][0]['status'] == 'error'
