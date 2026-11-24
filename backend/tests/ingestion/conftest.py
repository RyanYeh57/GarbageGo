import csv
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.clock import TAIPEI

FIXTURES = Path(__file__).resolve().parent / "fixtures"
DATASET_AT = datetime(2026, 11, 16, 9, 21, tzinfo=TAIPEI)


def _load(stops_name: str, geocode_name: str):
    stops = json.loads((FIXTURES / stops_name).read_text(encoding="utf-8-sig"))
    with open(FIXTURES / geocode_name, encoding="utf-8-sig", newline="") as f:
        geo = {int(r["source_index"]): r for r in csv.DictReader(f)}
    with open(FIXTURES / "suspects.csv", encoding="utf-8-sig", newline="") as f:
        suspects = {int(r["source_index"]) for r in csv.DictReader(f)}
    return stops, geo, suspects, DATASET_AT


@pytest.fixture
def small_inputs():
    """(stops, geocode_rows, suspects, dataset_at): 3 rows, row 1 has no coordinates, row 2 has blank car_licence."""
    return _load("pts.json", "geocode.csv")


@pytest.fixture
def dup_inputs():
    """Two identical 84004 rows (84004 really has 64 such rows)."""
    return _load("pts_dup.json", "geocode_dup.csv")


@pytest.fixture
def small_files():
    return SimpleNamespace(stops=str(FIXTURES / "pts.json"), geocode=str(FIXTURES / "geocode.csv"),
                           suspects=str(FIXTURES / "suspects.csv"))
