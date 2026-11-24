from sqlalchemy import inspect, text


def test_tables_exist(db_engine):
    names = set(inspect(db_engine).get_table_names())
    assert {"collection_stops", "collection_schedules", "vehicle_observations", "stop_arrivals"} <= names


def test_observation_unique_car_time(db_session):
    sql = text("INSERT INTO vehicle_observations (car, observed_at, collected_at, geom, source, raw) "
               "VALUES ('KED-1385', '2026-11-03 19:39:53+08', now(), ST_SetSRID(ST_MakePoint(120.5, 24.2), 4326), 'api', '{}') "
               "ON CONFLICT (car, observed_at) DO NOTHING")
    db_session.execute(sql)
    db_session.execute(sql)
    assert db_session.execute(text("SELECT count(*) FROM vehicle_observations")).scalar() == 1


def test_stop_geom_nullable(db_session):
    db_session.execute(text("INSERT INTO collection_stops (source_index, area, village, caption, task_type, car_licence) "
                            "VALUES (0, '中區', '中華里', '中華路一段143號', '沿街', '312-UX')"))
    assert db_session.execute(text("SELECT geom IS NULL FROM collection_stops")).scalar() is True
