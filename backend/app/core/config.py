"""Settings read from environment variables, falling back to the repo-root .env file."""
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_dotenv(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines; skip blanks and comments. Missing file -> {}."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class Settings:
    database_url: str = ""
    host_database_url: str = ""
    test_database_url: str = ""
    # 84004 d1..d7 -> ISO weekday (1 = Monday). Checked with GPS in plan Task 6:
    # d1..d7 = Monday..Sunday (docs/research/opendata-api-check.md §10).
    schedule_day_index_to_iso_weekday: dict[int, int] = field(
        default_factory=lambda: {i: i for i in range(1, 8)}
    )


@lru_cache
def get_settings() -> Settings:
    env = {**load_dotenv(REPO_ROOT / ".env"), **os.environ}
    return Settings(
        database_url=env.get("DATABASE_URL", ""),
        host_database_url=env.get("HOST_DATABASE_URL", ""),
        test_database_url=env.get("TEST_DATABASE_URL", ""),
    )
