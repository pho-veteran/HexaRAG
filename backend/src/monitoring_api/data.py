import csv
import os
from pathlib import Path


MONITORING_SERVICES = {
    'PaymentGW': {
        'metrics': {
            'latency_p99_ms': 185,
            'error_rate_percent': 0.08,
            'requests_per_minute': 22000,
            'cpu_percent': 62,
            'memory_percent': 71,
        },
        'status': {
            'service': 'PaymentGW',
            'status': 'healthy',
            'uptime_percent_24h': 99.98,
            'uptime_percent_7d': 99.91,
            'uptime_percent_30d': 99.87,
            'last_incident': '2026-03-05',
            'active_alerts': [],
        },
    },
    'OrderSvc': {
        'metrics': {
            'latency_p99_ms': 210,
            'error_rate_percent': 0.11,
            'requests_per_minute': 18000,
            'cpu_percent': 59,
            'memory_percent': 68,
        },
        'status': {
            'service': 'OrderSvc',
            'status': 'healthy',
            'uptime_percent_24h': 100.0,
            'uptime_percent_7d': 99.95,
            'uptime_percent_30d': 99.92,
            'last_incident': '2026-01-28',
            'active_alerts': [],
        },
    },
    'AuthSvc': {
        'metrics': {
            'latency_p99_ms': 72,
            'error_rate_percent': 0.02,
            'requests_per_minute': 28000,
            'cpu_percent': 45,
            'memory_percent': 58,
        },
        'status': {
            'service': 'AuthSvc',
            'status': 'healthy',
            'uptime_percent_24h': 100.0,
            'uptime_percent_7d': 99.99,
            'uptime_percent_30d': 99.97,
            'last_incident': '2026-02-22',
            'active_alerts': [],
        },
    },
    'NotificationSvc': {
        'metrics': {
            'latency_p99_ms': 3200,
            'error_rate_percent': 2.1,
            'requests_per_minute': 9500,
            'cpu_percent': 88,
            'memory_percent': 82,
        },
        'status': {
            'service': 'NotificationSvc',
            'status': 'degraded',
            'uptime_percent_24h': 98.5,
            'uptime_percent_7d': 99.1,
            'uptime_percent_30d': 99.3,
            'last_incident': '2026-03-20',
            'active_alerts': ['HIGH_LATENCY', 'ELEVATED_ERROR_RATE'],
        },
    },
    'ReportingSvc': {
        'metrics': {
            'latency_p99_ms': 540,
            'error_rate_percent': 0.15,
            'requests_per_minute': 4200,
            'cpu_percent': 64,
            'memory_percent': 73,
        },
        'status': {
            'service': 'ReportingSvc',
            'status': 'healthy',
            'uptime_percent_24h': 99.9,
            'uptime_percent_7d': 99.6,
            'uptime_percent_30d': 99.2,
            'last_incident': '2026-04-02',
            'active_alerts': [],
        },
    },
    'FraudDetector': {
        'metrics': {
            'latency_p99_ms': 880,
            'error_rate_percent': 0.3,
            'requests_per_minute': 6100,
            'cpu_percent': 69,
            'memory_percent': 77,
        },
        'status': {
            'service': 'FraudDetector',
            'status': 'healthy',
            'uptime_percent_24h': 100.0,
            'uptime_percent_7d': 99.97,
            'uptime_percent_30d': 99.93,
            'last_incident': '2026-03-12',
            'active_alerts': [],
        },
    },
}

BASE_METRICS = {service: payload['metrics'] for service, payload in MONITORING_SERVICES.items()}
SERVICE_STATUS = {service: payload['status'] for service, payload in MONITORING_SERVICES.items()}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _incidents_csv_path() -> Path:
    configured_root = os.environ.get('W4_DATA_ROOT')
    if configured_root:
        return Path(configured_root) / 'structured_data' / 'incidents.csv'
    return _repo_root() / 'W4' / 'data_package' / 'structured_data' / 'incidents.csv'


def _load_incidents() -> list[dict[str, str | int]]:
    with _incidents_csv_path().open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        return [
            {
                'incident_id': row['incident_id'],
                'service': row['service'],
                'date': row['date'],
                'severity': row['severity'],
                'duration_minutes': int(row['duration_minutes']),
                'root_cause': row['root_cause'],
                'resolution': row['resolution'],
                'team_responsible': row['team_responsible'],
                'reported_by': row['reported_by'],
            }
            for row in reader
        ]


INCIDENTS = _load_incidents()
