"""Import 84004 collection points, weekly slots and local geocodes.

CLI (from backend/):
  python -m app.modules.ingestion.stops --stops <84004.json> --geocode <all.csv>
      --expect-sha256 <sha> [--suspects <suspects.csv>] [--dataset-at <ISO>] [--allow-new-dataset]
Connects to HOST_DATABASE_URL and commits on success.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

KINDS = (("g", "general"), ("r", "recycle"))
HHMM = re.compile(r"^(\d{1,2}):(\d{2})$")


@dataclass
class ImportReport:
    stops: int = 0
    with_geom: int = 0
    suspects: int = 0
    schedules: int = 0
    skipped_slots: int = 0


def _parse_hhmm(s: str) -> time | None:
    m = HHMM.match(s or "")
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return time(h, mi) if h < 24 and mi < 60 else None


def _schedule(record: dict) -> tuple[list[tuple[int, str, time, time]], int]:
    """(slots, skipped). A slot with both fields empty is no slot; anything else unparsable is skipped."""
    slots, skipped = [], 0
    for prefix, kind in KINDS:
        for day in range(1, 8):
            s = record.get(f"{prefix}_d{day}_time_s", "")
            e = record.get(f"{prefix}_d{day}_time_e", "")
            if not s and not e:
                continue
            start, end = _parse_hhmm(s), _parse_hhmm(e)
            if start is None or end is None:
                skipped += 1
                continue
            slots.append((day, kind, start, end))
    return slots, skipped


def parse_schedule(record: dict) -> list[tuple[int, str, time, time]]:
    return _schedule(record)[0]


UPSERT_STOP = text("""
INSERT INTO collection_stops (source_index, area, village, caption, task_type, car_licence,
                              geom, geocode_source, geocode_level, source_dataset_at)
VALUES (:source_index, :area, :village, :caption, :task_type, :car_licence,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :geocode_source, :geocode_level, :dataset_at)
ON CONFLICT (source_index) DO UPDATE SET
  area = EXCLUDED.area, village = EXCLUDED.village, caption = EXCLUDED.caption,
  task_type = EXCLUDED.task_type, car_licence = EXCLUDED.car_licence, geom = EXCLUDED.geom,
  geocode_source = EXCLUDED.geocode_source, geocode_level = EXCLUDED.geocode_level,
  source_dataset_at = EXCLUDED.source_dataset_at
RETURNING id
""")
DELETE_SLOTS = text("DELETE FROM collection_schedules WHERE stop_id = :stop_id")
INSERT_SLOT = text("INSERT INTO collection_schedules (stop_id, day_index, kind, start_time, end_time) "
                   "VALUES (:stop_id, :day_index, :kind, :start_time, :end_time)")


def _check_alignment(stops: list[dict], geocode_rows: dict[int, dict]) -> None:
    """Coordinates must belong to the same row; otherwise write nothing."""
    for i, stop in enumerate(stops):
        row = geocode_rows.get(i)
        if row is None:
            raise ValueError(f"missing geocode row at source_index {i}")
        if row["caption"] != stop["caption"]:
            raise ValueError(f"caption mismatch at source_index {i}")


def import_stops(session: Session, stops: list[dict], geocode_rows: dict[int, dict],
                 suspects: set[int], dataset_at: datetime | None) -> ImportReport:
    """Upsert by source_index; replaces each stop's slots. Does not commit (decision 8)."""
    _check_alignment(stops, geocode_rows)
    report = ImportReport()
    for i, stop in enumerate(stops):
        geo = geocode_rows[i]
        has_geom = bool(geo.get("lon")) and bool(geo.get("lat"))
        level = None
        if has_geom:
            level = "suspect" if i in suspects else geo["level"]
        stop_id = session.execute(UPSERT_STOP, {
            "source_index": i, "area": stop["area"], "village": stop["village"],
            "caption": stop["caption"], "task_type": stop["task_type"],
            "car_licence": stop.get("car_licence") or None,
            "lon": float(geo["lon"]) if has_geom else None,
            "lat": float(geo["lat"]) if has_geom else None,
            "geocode_source": "local" if has_geom else None, "geocode_level": level,
            "dataset_at": dataset_at,
        }).scalar_one()
        slots, skipped = _schedule(stop)
        session.execute(DELETE_SLOTS, {"stop_id": stop_id})
        if slots:
            session.execute(INSERT_SLOT, [
                {"stop_id": stop_id, "day_index": d, "kind": k, "start_time": s, "end_time": e}
                for d, k, s, e in slots])
        report.stops += 1
        report.with_geom += has_geom
        report.suspects += level == "suspect"
        report.schedules += len(slots)
        report.skipped_slots += skipped
    return report


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="python -m app.modules.ingestion.stops")
    p.add_argument("--stops", required=True)
    p.add_argument("--geocode", required=True)
    p.add_argument("--expect-sha256", required=True)
    p.add_argument("--suspects")
    p.add_argument("--dataset-at", type=datetime.fromisoformat)
    p.add_argument("--allow-new-dataset", action="store_true")
    a = p.parse_args(argv)

    sha = file_sha256(Path(a.stops))
    if sha != a.expect_sha256 and not a.allow_new_dataset:
        print(f"sha256 mismatch: file is {sha}, expected {a.expect_sha256}. Nothing written.")
        print("A new 84004 file means a new dataset version: rebuild everything, then pass --allow-new-dataset.")
        return 1

    stops = json.loads(Path(a.stops).read_text(encoding="utf-8-sig"))
    geocode_rows = {int(r["source_index"]): r for r in _read_csv(a.geocode)}
    suspects = {int(r["source_index"]) for r in _read_csv(a.suspects)} if a.suspects else set()

    from app.core.config import get_settings
    from app.db.session import get_engine

    url = get_settings().host_database_url
    if not url:
        print("HOST_DATABASE_URL is not set")
        return 1
    with Session(get_engine(url)) as session:
        report = import_stops(session, stops, geocode_rows, suspects, a.dataset_at)
        session.commit()
    print(report)
    print(f"sha256={sha}")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli(sys.argv[1:]))
