from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_engine, get_session
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
    yield get_engine(url)


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


@pytest.fixture
def client_with_db(db_session):
    """TestClient whose requests use db_session, so they see uncommitted test data."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as c:
        yield c
