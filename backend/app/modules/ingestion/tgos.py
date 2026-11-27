"""TGOS batch address matching for the stops the local match could not place.

CLI (from backend/):
  python -m app.modules.ingestion.tgos export --geocode <all.csv> --out <upload.csv>
      Writes the TGOS upload file (id,Address,Response_Address,Response_X,Response_Y),
      one row per stop without coordinates. id = source_index.
  python -m app.modules.ingestion.tgos import --result <tgos_result.csv>
      Fills geom for stops that still have none (geocode_source = geocode_level = 'tgos').
      Never overwrites local or manual coordinates. Connects to HOST_DATABASE_URL, commits on success.

TGOS result coordinates are TWD97 TM2 (EPSG:3826). One cell may hold several answers split by ';':
answers within MAX_SPREAD_M of each other are averaged, otherwise the row counts as ambiguous.
"""
import argparse
import csv
import math
import re
import sys
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

CITY = "臺中市"
NOTE = re.compile(r"[（(][^）)]*[）)]")
FIELDS = ["id", "Address", "Response_Address", "Response_X", "Response_Y"]
# Rough Taichung bounding box (WGS84); a point outside it is a wrong match.
LON_RANGE, LAT_RANGE = (120.4, 121.5), (23.9, 24.5)
MAX_SPREAD_M = 50


@dataclass
class TgosReport:
    rows: int = 0
    updated: int = 0
    unmatched: int = 0
    ambiguous: int = 0
    out_of_area: int = 0
    kept_existing: int = 0


def build_address(area: str, caption: str) -> str:
    """Full address for TGOS: city + district + caption without (notes)."""
    street = NOTE.sub("", caption).strip() or caption
    return f"{CITY}{area}{street}"


def export_rows(geocode_rows: list[dict]) -> list[dict]:
    return [{"id": int(r["source_index"]), "Address": build_address(r["area"], r["caption"]),
             "Response_Address": "", "Response_X": "", "Response_Y": ""}
            for r in geocode_rows if not (r.get("lon") and r.get("lat"))]


def read_result(path: str) -> list[dict]:
    """TGOS may return UTF-8 or Big5 (cp950)."""
    for enc in ("utf-8-sig", "cp950"):
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode {path} as UTF-8 or cp950")


SELECT_STOP = text("SELECT area, caption, geom IS NOT NULL AS has_geom, geocode_source "
                   "FROM collection_stops WHERE source_index = :i")
TO_WGS84 = text("SELECT ST_X(g), ST_Y(g) FROM "
                "(SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:x, :y), 3826), 4326) AS g) t")
FILL_GEOM = text("UPDATE collection_stops SET geom = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), "
                 "geocode_source = 'tgos', geocode_level = 'tgos' WHERE source_index = :i")


def _answers(i: int, xs: str, ys: str) -> list[tuple[float, float]]:
    pts = list(zip((float(v) for v in xs.split(";")), (float(v) for v in ys.split(";"))))
    if any(x < 1000 or y < 1000 for x, y in pts):
        raise ValueError(f"id {i}: coordinates look like WGS84, expected TWD97 (EPSG:3826)")
    return pts


def import_result(session: Session, rows: list[dict]) -> TgosReport:
    """Validates every row before use; raises (nothing written by caller) on id or address mismatch.
    Does not commit."""
    report = TgosReport()
    for r in rows:
        i = int(r["id"])
        stop = session.execute(SELECT_STOP, {"i": i}).one_or_none()
        if stop is None:
            raise ValueError(f"unknown id {i}")
        if r["Address"].strip() != build_address(stop.area, stop.caption):
            raise ValueError(f"address mismatch at id {i}")
        report.rows += 1
        x, y = (r.get("Response_X") or "").strip(), (r.get("Response_Y") or "").strip()
        if not x or not y:
            report.unmatched += 1
            continue
        pts = _answers(i, x, y)
        if max(math.dist(a, b) for a in pts for b in pts) > MAX_SPREAD_M:   # TWD97 is in metres
            report.ambiguous += 1
            continue
        mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        lon, lat = session.execute(TO_WGS84, {"x": mx, "y": my}).one()
        if not (LON_RANGE[0] <= lon <= LON_RANGE[1] and LAT_RANGE[0] <= lat <= LAT_RANGE[1]):
            report.out_of_area += 1
            continue
        if stop.has_geom and stop.geocode_source != "tgos":
            report.kept_existing += 1
            continue
        session.execute(FILL_GEOM, {"lon": lon, "lat": lat, "i": i})
        report.updated += 1
    return report


def run_cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="python -m app.modules.ingestion.tgos")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--geocode", required=True)
    e.add_argument("--out", required=True)
    i = sub.add_parser("import")
    i.add_argument("--result", required=True)
    a = p.parse_args(argv)

    if a.cmd == "export":
        with open(a.geocode, encoding="utf-8-sig", newline="") as f:
            rows = export_rows(list(csv.DictReader(f)))
        with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {a.out}")
        return 0

    from app.core.config import get_settings
    from app.db.session import get_engine

    url = get_settings().host_database_url
    if not url:
        print("HOST_DATABASE_URL is not set")
        return 1
    rows = read_result(a.result)
    with Session(get_engine(url)) as session:
        report = import_result(session, rows)
        session.commit()
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(run_cli(sys.argv[1:]))
