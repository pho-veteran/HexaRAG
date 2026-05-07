SERVICES = [
    'AuthSvc',
    'FraudDetector',
    'NotificationSvc',
    'OrderSvc',
    'PaymentGW',
    'ReportingSvc',
]


def list_services() -> list[str]:
    return SERVICES.copy()
