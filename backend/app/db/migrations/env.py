from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.config import get_settings

config = context.config
if config.config_file_name and not config.attributes.get("url"):
    fileConfig(config.config_file_name)  # CLI run; tests keep pytest's logging


def run_migrations_online() -> None:
    url = config.attributes.get("url") or get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("offline migrations are not supported")
run_migrations_online()
