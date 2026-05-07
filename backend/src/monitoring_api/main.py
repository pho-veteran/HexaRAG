from fastapi import FastAPI, HTTPException

from monitoring_api.data import BASE_METRICS

app = FastAPI(title='HexaRAG Monitoring API')


@app.get('/services')
def list_services() -> dict[str, list[str]]:
    return {'services': sorted(BASE_METRICS.keys())}


@app.get('/metrics/{service_name}')
def get_metrics(service_name: str) -> dict[str, int | float]:
    if service_name not in BASE_METRICS:
        raise HTTPException(status_code=404, detail='Unknown service')

    return BASE_METRICS[service_name]
