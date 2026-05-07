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
