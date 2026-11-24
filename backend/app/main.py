from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import chat, health, recommendations, routes, stops
from app.core.logging import AccessLogMiddleware, configure_logging


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Use only field path + rule text; never echo the input (it may be the user's location).
    message = "; ".join(
        f"{'.'.join(str(p) for p in err['loc'][1:])}: {err['msg']}" for err in exc.errors()
    )
    return _error(422, "validation_error", message)


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Our code raises detail="stop_not_found"; framework errors ("Not Found") become "not_found".
    code = str(exc.detail).lower().replace(" ", "_")
    return _error(exc.status_code, code, HTTPStatus(exc.status_code).phrase)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="GarbageGo API", version="0.1.0")
    app.add_middleware(AccessLogMiddleware)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    for module in (health, stops, recommendations, routes, chat):
        app.include_router(module.router)
    return app


app = create_app()
