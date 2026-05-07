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
    assert 'could not complete the live tool step' in response.json()['message']['content'].lower()
