from fastapi import FastAPI

from app.api import health
from app.core.logging import AccessLogMiddleware, configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="GarbageGo API", version="0.1.0")
    app.add_middleware(AccessLogMiddleware)
    app.include_router(health.router)
    return app


app = create_app()
