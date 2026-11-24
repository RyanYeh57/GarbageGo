"""Parse Taichung 83558 GPS records and import historical snapshots.

Snapshot folder: one JSON file per fetch (the raw API array) plus
collected_at.csv (file,collected_at). collected_at is when WE fetched it;
it is never guessed from file times (plan decision 1).

CLI (from backend/): python -m app.modules.ingestion.gps <snapshot_dir>
Connects to HOST_DATABASE_URL and commits on success.
"""
import csv
import json
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.clock import parse_taichung_time

LON_RANGE = (119.0, 123.0)
LAT_RANGE = (21.0, 26.0)
OVER_SPEED = {"Y": True, "N": False}


@dataclass
class Observation:
    car: str
    line_id: str
    observed_at: datetime
    lon: float
    lat: float
    speed: int | None
    over_speed: bool | None
    location_text: str
    raw: dict


def _speed(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse_observation(raw: dict) -> Observation | None:
    """None when the record cannot be trusted: no car/time, bad time, bad or out-of-area coordinates."""
    if not isinstance(raw, dict) or not raw.get("car") or not raw.get("time"):
        return None
    try:
        observed_at = parse_taichung_time(raw["time"])
        lon, lat = float(raw["X"]), float(raw["Y"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (LON_RANGE[0] <= lon <= LON_RANGE[1] and LAT_RANGE[0] <= lat <= LAT_RANGE[1]):
        return None  # also rejects (0, 0)
    return Observation(
        car=raw["car"], line_id=raw.get("lineid") or "", observed_at=observed_at, lon=lon, lat=lat,
        speed=_speed(raw.get("SpeedValue")), over_speed=OVER_SPEED.get(raw.get("OverSpeed")),
        location_text=raw.get("location") or "", raw=raw,
    )


INSERT = text("""
INSERT INTO vehicle_observations (car, line_id, observed_at, collected_at, geom, speed, over_speed,
                                  location_text, source, raw)
SELECT r.car, r.line_id, r.observed_at, :collected_at, ST_SetSRID(ST_MakePoint(r.lon, r.lat), 4326),
       r.speed, r.over_speed, r.location_text, :source, r.raw
FROM jsonb_to_recordset(CAST(:rows AS jsonb)) AS r(
    car text, line_id text, observed_at timestamptz, lon float8, lat float8, speed int,
    over_speed bool, location_text text, raw jsonb)
ON CONFLICT (car, observed_at) DO NOTHING
RETURNING 1
""")


def insert_observations(session: Session, obs: Iterable[Observation], collected_at: datetime,
                        source: str) -> int:
    """Insert, skipping (car, observed_at) already stored. Returns rows actually added. Does not commit."""
    rows = [{**asdict(o), "observed_at": o.observed_at.isoformat()} for o in obs]
    if not rows:
        return 0
    result = session.execute(INSERT, {"rows": json.dumps(rows, ensure_ascii=False),
                                      "collected_at": collected_at, "source": source})
    return len(result.all())


@dataclass
class GpsImportReport:
    files: int = 0
    skipped_files: int = 0
    parsed: int = 0
    rejected: int = 0
    inserted: int = 0


def _read_collected_at(path: Path) -> dict[str, datetime]:
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            at = datetime.fromisoformat(r["collected_at"])
            if at.tzinfo is None:
                raise ValueError(f"collected_at has no timezone for {r['file']}: {r['collected_at']!r}")
            out[r["file"]] = at
    return out


def import_snapshot_dir(session: Session, path: Path) -> GpsImportReport:
    """Import every *.json in path as source='historical'. Empty, non-array or broken
    files are skipped and counted. Does not commit."""
    path = Path(path)
    collected = _read_collected_at(path / "collected_at.csv")
    files = sorted(path.glob("*.json"))
    missing = [f.name for f in files if f.name not in collected]
    if missing:
        raise ValueError(f"no collected_at for: {', '.join(missing)}")

    report = GpsImportReport(files=len(files))
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = None
        if not isinstance(data, list) or not data:
            report.skipped_files += 1
            continue
        obs = [o for o in map(parse_observation, data) if o is not None]
        report.parsed += len(obs)
        report.rejected += len(data) - len(obs)
        report.inserted += insert_observations(session, obs, collected[f.name], "historical")
    return report


def run_cli(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m app.modules.ingestion.gps <snapshot_dir>")
        return 2
    from app.core.config import get_settings
    from app.db.session import get_engine

    url = get_settings().host_database_url
    if not url:
        print("HOST_DATABASE_URL is not set")
        return 1
    with Session(get_engine(url)) as session:
        report = import_snapshot_dir(session, Path(argv[0]))
        session.commit()
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(run_cli(sys.argv[1:]))
