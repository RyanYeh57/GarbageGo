"""Access log without query strings, so user coordinates never reach the log."""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

ACCESS_LOGGER = "garbagego.access"


def configure_logging() -> None:
    logger = logging.getLogger(ACCESS_LOGGER)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            ms = round((time.perf_counter() - start) * 1000)
            # request.url.path only: never the query string or body.
            logging.getLogger(ACCESS_LOGGER).info(
                "%s %s %s %sms", request.method, request.url.path, status, ms
            )
