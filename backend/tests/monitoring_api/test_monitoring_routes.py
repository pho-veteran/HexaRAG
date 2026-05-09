from fastapi.testclient import TestClient

from monitoring_api.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_paymentgw_shape():
    response = client.get('/metrics/PaymentGW')
    assert response.status_code == 200
    payload = response.json()
    assert 'latency_p99_ms' in payload
    assert 'error_rate_percent' in payload


def test_services_endpoint_lists_all_six_services():
    response = client.get('/services')
    assert response.status_code == 200
    assert len(response.json()['services']) == 6


def test_status_endpoint_returns_service_health_shape():
    response = client.get('/status/PaymentGW')

    assert response.status_code == 200
    assert response.json() == {
        'service': 'PaymentGW',
        'status': 'healthy',
        'uptime_percent_24h': 99.98,
        'uptime_percent_7d': 99.91,
        'uptime_percent_30d': 99.87,
        'last_incident': '2026-03-05',
        'active_alerts': [],
    }


def test_incidents_endpoint_returns_all_w4_incidents():
    response = client.get('/incidents')

    assert response.status_code == 200
    payload = response.json()
    assert len(payload['incidents']) == 8
    assert payload['incidents'][0]['incident_id'] == 'INC-001'
    assert payload['incidents'][0]['service'] == 'PaymentGW'


def test_monitoring_module_exposes_lambda_handler():
    from monitoring_api.main import handler

    assert handler is not None
