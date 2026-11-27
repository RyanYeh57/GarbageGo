import csv

import pytest
from sqlalchemy import text

from app.modules.ingestion.stops import import_stops
from app.modules.ingestion.tgos import build_address, export_rows, import_result, read_result


def test_build_address_adds_city_and_area_and_drops_notes():
    assert build_address("北區", "進化北路63巷6號(進化北路與進化北路63巷口)") == "臺中市北區進化北路63巷6號"


def test_build_address_keeps_caption_when_only_a_note():
    assert build_address("中區", "(定點)") == "臺中市中區(定點)"


def test_export_rows_only_rows_without_coordinates():
    geo = [
        {"source_index": "0", "area": "中區", "caption": "A路1號", "lon": "120.6", "lat": "24.1"},
        {"source_index": "7", "area": "北區", "caption": "B路2號", "lon": "", "lat": ""},
    ]
    assert export_rows(geo) == [
        {"id": 7, "Address": "臺中市北區B路2號", "Response_Address": "", "Response_X": "", "Response_Y": ""}]


def test_read_result_falls_back_to_cp950(tmp_path):
    p = tmp_path / "r.csv"
    p.write_bytes("id,Address\n1,臺中市\n".encode("cp950"))
    assert read_result(str(p)) == [{"id": "1", "Address": "臺中市"}]


def _row(i, address, x="", y=""):
    return {"id": str(i), "Address": address, "Response_Address": "", "Response_X": x, "Response_Y": y}


def _twd97(db_session, lon, lat):
    """(x, y) strings in TWD97 TM2 (EPSG:3826), the format TGOS returns."""
    x, y = db_session.execute(text(
        "SELECT ST_X(g), ST_Y(g) FROM (SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 3826) g) t"),
        {"lon": lon, "lat": lat}).one()
    return f"{x:.3f}", f"{y:.3f}"


def _addr(db_session, i):
    area, caption = db_session.execute(
        text("SELECT area, caption FROM collection_stops WHERE source_index = :i"), {"i": i}).one()
    return build_address(area, caption)


def _geo(db_session, i):
    return tuple(db_session.execute(text(
        "SELECT ST_X(geom), ST_Y(geom), geocode_source, geocode_level FROM collection_stops "
        "WHERE source_index = :i"), {"i": i}).one())


def test_import_fills_null_geom_from_twd97(db_session, small_inputs):   # row 1 has no coordinates
    import_stops(db_session, *small_inputs)
    x, y = _twd97(db_session, 120.7, 24.2)
    report = import_result(db_session, [_row(1, _addr(db_session, 1), x, y)])
    assert report.updated == 1
    lon, lat, source, level = _geo(db_session, 1)
    assert (round(lon, 5), round(lat, 5), source, level) == (120.7, 24.2, "tgos", "tgos")


def test_import_two_close_answers_uses_midpoint(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    x, y = _twd97(db_session, 120.7, 24.2)
    xs, ys = f"{float(x) - 10:.3f};{float(x) + 10:.3f}", f"{y};{y}"     # 20 m apart
    report = import_result(db_session, [_row(1, _addr(db_session, 1), xs, ys)])
    assert report.updated == 1
    lon, lat, *_ = _geo(db_session, 1)
    assert (round(lon, 5), round(lat, 5)) == (120.7, 24.2)


def test_import_two_far_answers_is_ambiguous(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    x, y = _twd97(db_session, 120.7, 24.2)
    xs, ys = f"{x};{float(x) + 51:.3f}", f"{y};{y}"                     # 51 m apart
    report = import_result(db_session, [_row(1, _addr(db_session, 1), xs, ys)])
    assert (report.ambiguous, report.updated) == (1, 0)
    assert _geo(db_session, 1) == (None, None, None, None)


def test_import_never_overwrites_local_geom(db_session, small_inputs):   # row 0 is local
    import_stops(db_session, *small_inputs)
    before = _geo(db_session, 0)
    report = import_result(db_session, [_row(0, _addr(db_session, 0), *_twd97(db_session, 120.7, 24.2))])
    assert (report.updated, report.kept_existing) == (0, 1)
    assert _geo(db_session, 0) == before


def test_import_counts_unmatched_and_out_of_area(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    a = _addr(db_session, 1)
    report = import_result(db_session, [_row(1, a), _row(1, a, *_twd97(db_session, 121.9, 25.0))])
    assert (report.unmatched, report.out_of_area, report.updated) == (1, 1, 0)


def test_import_rejects_wgs84(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    with pytest.raises(ValueError, match="TWD97"):
        import_result(db_session, [_row(1, _addr(db_session, 1), "120.7", "24.2")])


def test_import_aborts_on_address_mismatch(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    with pytest.raises(ValueError, match="address mismatch"):
        import_result(db_session, [_row(1, "臺中市北區別的路1號", "217000", "2670000")])


def test_import_aborts_on_unknown_id(db_session, small_inputs):
    import_stops(db_session, *small_inputs)
    with pytest.raises(ValueError, match="unknown id"):
        import_result(db_session, [_row(999, "x", "217000", "2670000")])
