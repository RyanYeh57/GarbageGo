from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(scope="session")
def db_engine():
    """Test database migrated to head. Skips when TEST_DATABASE_URL is not set."""
    url = get_settings().test_database_url
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.attributes["url"] = url
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """One transaction per test, rolled back at the end. Code under test may
    call session.commit(); it only releases a savepoint."""
    with db_engine.connect() as conn:
        trans = conn.begin()
        session = Session(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            trans.rollback()
