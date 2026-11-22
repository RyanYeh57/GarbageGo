from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@lru_cache
def _engine_for(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def get_engine(url: str | None = None) -> Engine:
    url = url or get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return _engine_for(url)


def get_session() -> Iterator[Session]:
    """FastAPI dependency. With no DATABASE_URL the session is unbound and
    fails on first use, so callers like /health can report the error."""
    bind = get_engine() if get_settings().database_url else None
    with Session(bind=bind) as session:
        yield session
