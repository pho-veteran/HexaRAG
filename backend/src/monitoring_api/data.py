BASE_METRICS = {
    'PaymentGW': {
        'latency_p99_ms': 185,
        'error_rate_percent': 0.08,
        'requests_per_minute': 22000,
        'cpu_percent': 62,
        'memory_percent': 71,
    },
    'OrderSvc': {
        'latency_p99_ms': 210,
        'error_rate_percent': 0.11,
        'requests_per_minute': 18000,
        'cpu_percent': 59,
        'memory_percent': 68,
    },
    'AuthSvc': {
        'latency_p99_ms': 72,
        'error_rate_percent': 0.02,
        'requests_per_minute': 28000,
        'cpu_percent': 45,
        'memory_percent': 58,
    },
    'NotificationSvc': {
        'latency_p99_ms': 3200,
        'error_rate_percent': 2.1,
        'requests_per_minute': 9500,
        'cpu_percent': 88,
        'memory_percent': 82,
    },
    'ReportingSvc': {
        'latency_p99_ms': 540,
        'error_rate_percent': 0.15,
        'requests_per_minute': 4200,
        'cpu_percent': 64,
        'memory_percent': 73,
    },
    'FraudDetector': {
        'latency_p99_ms': 880,
        'error_rate_percent': 0.3,
        'requests_per_minute': 6100,
        'cpu_percent': 69,
        'memory_percent': 77,
    },
}
