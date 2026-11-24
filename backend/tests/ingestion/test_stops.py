import pytest
from datetime import time
from sqlalchemy import text
from app.modules.ingestion.stops import parse_schedule, import_stops, run_cli


def test_parse_schedule_flattens_days():
    rec = {"g_d1_time_s": "15:25", "g_d1_time_e": "15:30", "g_d2_time_s": "", "g_d2_time_e": "",
           "r_d1_time_s": "15:25", "r_d1_time_e": "15:30"}
    assert parse_schedule(rec) == [(1, "general", time(15, 25), time(15, 30)),
                                   (1, "recycle", time(15, 25), time(15, 30))]


def test_parse_schedule_skips_bad_time():
    assert parse_schedule({"g_d1_time_s": "25:99", "g_d1_time_e": "15:30"}) == []


def test_import_counts_and_null_geom(db_session, small_inputs):      # 3 rows, 1 without coordinates
    report = import_stops(db_session, *small_inputs)
    assert (report.stops, report.with_geom) == (3, 2)


def test_import_is_idempotent(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    import_stops(db_session, *small_inputs)
    assert db_session.execute(text("SELECT count(*) FROM collection_stops")).scalar() == 3


def test_duplicate_rows_both_imported(db_session, dup_inputs):       # two identical rows
    assert import_stops(db_session, *dup_inputs).stops == 2


def test_suspect_level(db_session, small_inputs):
    stops, geo, _, at = small_inputs
    import_stops(db_session, stops, geo, {0}, at)
    assert db_session.execute(text("SELECT geocode_level FROM collection_stops WHERE source_index = 0")).scalar() == "suspect"


def test_caption_mismatch_aborts(db_session, small_inputs):
    stops, geo, sus, at = small_inputs
    geo[0] = {**geo[0], "caption": "別的地址"}
    with pytest.raises(ValueError, match="caption mismatch"):
        import_stops(db_session, stops, geo, sus, at)


def test_reimport_keeps_filled_geom_when_file_has_none(db_session, small_inputs):   # row 1 has no coordinates
    import_stops(db_session, *small_inputs)
    db_session.execute(text("UPDATE collection_stops SET geom = ST_SetSRID(ST_MakePoint(120.6, 24.1), 4326), "
                            "geocode_source = 'tgos', geocode_level = 'tgos' WHERE source_index = 1"))
    import_stops(db_session, *small_inputs)
    row = db_session.execute(text("SELECT ST_X(geom), ST_Y(geom), geocode_source, geocode_level "
                                  "FROM collection_stops WHERE source_index = 1")).one()
    assert tuple(row) == (120.6, 24.1, "tgos", "tgos")


def test_reimport_updates_geom_when_file_has_one(db_session, small_inputs):   # row 0 has coordinates
    stops, geo, sus, at = small_inputs
    import_stops(db_session, stops, geo, sus, at)
    geo[0] = {**geo[0], "lon": "120.7", "lat": "24.2"}
    import_stops(db_session, stops, geo, sus, at)
    row = db_session.execute(text("SELECT ST_X(geom), ST_Y(geom) FROM collection_stops WHERE source_index = 0")).one()
    assert tuple(row) == (120.7, 24.2)


def test_blank_car_licence_is_null(db_session, small_inputs):   # 3rd row has car_licence ""
    import_stops(db_session, *small_inputs)
    assert db_session.execute(text("SELECT car_licence IS NULL FROM collection_stops WHERE source_index = 2")).scalar() is True


def test_cli_refuses_unexpected_sha256(tmp_path, small_files):
    code = run_cli(["--stops", small_files.stops, "--geocode", small_files.geocode, "--expect-sha256", "0" * 64])
    assert code == 1
