import pytest
from datetime import datetime
from sqlalchemy import text
from app.core.clock import TAIPEI, parse_taichung_time
from app.modules.ingestion.gps import parse_observation, insert_observations, import_snapshot_dir

SAMPLE = {"lineid": "24908", "car": "KED-1385", "time": "20261103T193953", "location": "臺中市龍井區 龍昌路",
          "X": "120.504613", "Y": "24.210510", "SpeedValue": "37", "OverSpeed": "N"}
NOW = datetime(2026, 11, 22, 12, 0, tzinfo=TAIPEI)


def test_parse_time_is_taipei():
    assert parse_taichung_time("20261103T193953").isoformat() == "2026-11-03T19:39:53+08:00"


def test_parse_observation_ok():
    o = parse_observation(SAMPLE)
    assert (o.car, o.lon, o.lat, o.speed, o.over_speed) == ("KED-1385", 120.504613, 24.21051, 37, False)


@pytest.mark.parametrize("patch", [{"time": "2026-11-03"}, {"X": "abc"}, {"X": "0", "Y": "0"}, {"Y": "40"}, {"car": ""}])
def test_parse_observation_rejects(patch):
    assert parse_observation({**SAMPLE, **patch}) is None


def test_insert_dedupes(db_session):
    o = parse_observation(SAMPLE)
    assert insert_observations(db_session, [o, o], collected_at=NOW, source="api") == 1


def test_import_skips_empty_and_invalid_files(db_session, snapshot_dir):
    r = import_snapshot_dir(db_session, snapshot_dir)
    assert (r.files, r.skipped_files, r.inserted) == (4, 3, 1)


def test_collected_at_comes_from_csv(db_session, snapshot_dir):
    import_snapshot_dir(db_session, snapshot_dir)      # collected_at.csv: ok.json -> 2026-11-03T19:42:00+08:00
    got = db_session.execute(text("SELECT collected_at FROM vehicle_observations")).scalar()
    assert got.isoformat() == "2026-11-03T19:42:00+08:00"


def test_missing_collected_at_aborts(db_session, snapshot_dir):
    (snapshot_dir / "extra.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="extra.json"):
        import_snapshot_dir(db_session, snapshot_dir)


def test_health_shows_latest_gps(client_with_db, db_session):
    insert_observations(db_session, [parse_observation(SAMPLE)], collected_at=NOW, source="api")
    assert client_with_db.get("/health").json()["latest_gps_at"] == "2026-11-03T19:39:53+08:00"
