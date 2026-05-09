from fastapi import FastAPI, HTTPException
from mangum import Mangum

from monitoring_api.data import BASE_METRICS, INCIDENTS, SERVICE_STATUS

app = FastAPI(title='HexaRAG Monitoring API')


@app.get('/services')
def list_services() -> dict[str, list[str]]:
    return {'services': sorted(BASE_METRICS.keys())}


@app.get('/status/{service_name}')
def get_status(service_name: str) -> dict[str, str | float | list[str]]:
    if service_name not in SERVICE_STATUS:
        raise HTTPException(status_code=404, detail='Unknown service')

    return SERVICE_STATUS[service_name]


@app.get('/metrics/{service_name}')
def get_metrics(service_name: str) -> dict[str, int | float]:
    if service_name not in BASE_METRICS:
        raise HTTPException(status_code=404, detail='Unknown service')

    return BASE_METRICS[service_name]


@app.get('/incidents')
def list_recent_incidents() -> dict[str, list[dict[str, str | int]]]:
    return {'incidents': INCIDENTS}


handler = Mangum(app)
