from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hexarag_api.api.chat import router as chat_router
from hexarag_api.api.health import router as health_router
from hexarag_api.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origin_list,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
