import pytest

from hexarag_api.tools.analytics import (
    fetch_q1_average_latency,
    fetch_q1_incident_summary,
    fetch_sla_target,
    summarize_q1_costs,
)


class AnalyticsCursor:
    def __init__(self, connection) -> None:
        self.connection = connection
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        normalized = ' '.join(query.split())
        self.connection.executed.append((normalized, params))

        if 'SUM(total_cost)' in normalized:
            self.result = (56350,)
            return

        if 'FROM sla_targets' in normalized:
            service = params[0]
            self.result = self.connection.sla_targets[service]
            return

        if 'AVG(latency_p99_ms)' in normalized:
            service = params[0]
            self.result = (self.connection.average_latency[service],)
            return

        if 'FROM incidents' in normalized:
            service = params[2] if params and len(params) == 3 else None
            self.result = self.connection.incident_summaries[service]
            return

        raise AssertionError(f'Unexpected query: {normalized}')

    def fetchone(self):
        return self.result


class AnalyticsConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...] | None]] = []
        self.sla_targets = {
            'PaymentGW': (200.0, 0.1),
            'OrderSvc': (500.0, 0.5),
        }
        self.average_latency = {
            'PaymentGW': 183.0,
            'OrderSvc': 281.33,
        }
        self.incident_summaries = {
            'PaymentGW': (3, 255, 1),
            'OrderSvc': (1, 120, 2),
            None: (7, 570, 1),
        }

    def cursor(self) -> AnalyticsCursor:
        return AnalyticsCursor(self)


@pytest.fixture
def analytics_connection() -> AnalyticsConnection:
    return AnalyticsConnection()


@pytest.fixture
def fake_db_connection() -> AnalyticsConnection:
    return AnalyticsConnection()


def test_summarize_q1_costs_returns_expected_total(fake_db_connection):
    result = summarize_q1_costs(fake_db_connection)
    assert result['total_cost'] == 56350


def test_fetch_sla_target_returns_paymentgw_threshold(analytics_connection):
    result = fetch_sla_target(analytics_connection, 'PaymentGW')

    assert result == {
        'service': 'PaymentGW',
        'latency_p99_ms': 200.0,
        'error_rate_percent': 0.1,
    }


def test_fetch_q1_average_latency_returns_paymentgw_average(analytics_connection):
    result = fetch_q1_average_latency(analytics_connection, 'PaymentGW')

    assert result == {
        'service': 'PaymentGW',
        'average_latency_p99_ms': 183.0,
    }


def test_fetch_q1_incident_summary_returns_paymentgw_totals(analytics_connection):
    result = fetch_q1_incident_summary(analytics_connection, 'PaymentGW')

    assert result == {
        'service': 'PaymentGW',
        'incident_count': 3,
        'total_duration_minutes': 255,
        'highest_severity': 'P1',
    }


def test_fetch_q1_incident_summary_without_service_returns_q1_totals(analytics_connection):
    result = fetch_q1_incident_summary(analytics_connection)

    assert result == {
        'service': 'all',
        'incident_count': 7,
        'total_duration_minutes': 570,
        'highest_severity': 'P1',
    }


def test_fetch_q1_incident_summary_maps_ranked_severity_to_label(analytics_connection):
    result = fetch_q1_incident_summary(analytics_connection, 'OrderSvc')

    assert result == {
        'service': 'OrderSvc',
        'incident_count': 1,
        'total_duration_minutes': 120,
        'highest_severity': 'P2',
    }
