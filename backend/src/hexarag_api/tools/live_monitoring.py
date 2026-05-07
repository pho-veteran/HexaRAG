import httpx


class LiveMonitoringClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def get_metrics(self, service_name: str) -> dict:
        response = httpx.get(f'{self.base_url}/metrics/{service_name}', timeout=10.0)
        response.raise_for_status()
        return response.json()

    def list_services(self) -> list[str]:
        response = httpx.get(f'{self.base_url}/services', timeout=10.0)
        response.raise_for_status()
        return response.json()['services']
