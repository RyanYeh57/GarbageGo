def test_nearby_returns_candidates(client):
    r = client.get("/stops/nearby", params={"lat": 24.1477, "lon": 120.6736})
    assert r.status_code == 200
    assert {"id", "address", "lat", "lon", "geocode_level", "today_slots", "distance_m"} <= set(r.json()[0])


def test_recommendation_shape(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736})
    body = r.json()
    assert r.status_code == 200
    assert body["primary"]["eta"]["status"] in {"live", "historical", "schedule_only", "stale", "passed", "no_data"}
    assert len(body["alternatives"]) <= 2


def test_at_param_is_echoed(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736, "at": "2026-11-23T11:00:00Z"})
    assert r.json()["at"] == "2026-11-23T19:00:00+08:00"


def test_naive_at_is_read_as_taipei(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736, "at": "2026-11-23T19:00:00"})
    assert r.json()["at"] == "2026-11-23T19:00:00+08:00"


def test_datetimes_have_taipei_offset(client):
    r = client.post("/recommendations", json={"lat": 24.1477, "lon": 120.6736})
    assert r.json()["at"].endswith("+08:00")


def test_invalid_lat_returns_error_format(client):
    r = client.get("/stops/nearby", params={"lat": 999, "lon": 120.6})
    assert r.status_code == 422
    assert set(r.json()) == {"error"}
    assert set(r.json()["error"]) == {"code", "message"}
    assert r.json()["error"]["code"] == "validation_error"


def test_validation_message_does_not_echo_location(client):
    r = client.get("/stops/nearby", params={"lat": 999.123456, "lon": 120.6})
    assert "999.123456" not in r.json()["error"]["message"]


def test_unknown_stop_404(client):
    r = client.get("/stops/999999999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "stop_not_found"


def test_walk_route_coordinates_are_lon_lat(client):
    r = client.get("/routes/walk", params={"from_lat": 24.1477, "from_lon": 120.6736, "to_lat": 24.15, "to_lon": 120.68})
    lon, lat = r.json()["coordinates"][0]
    assert 119 < lon < 123 and 21 < lat < 26


def test_stop_eta_shape(client):
    stop_id = client.get("/stops/nearby", params={"lat": 24.1477, "lon": 120.6736}).json()[0]["id"]
    r = client.get(f"/stops/{stop_id}/eta")
    assert r.status_code == 200
    assert r.json()["status"] in {"live", "historical", "schedule_only", "stale", "passed", "no_data"}
    assert {"eta", "eta_low", "eta_high", "data_time", "scheduled_start", "scheduled_end", "method"} <= set(r.json())


def test_openapi_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/health", "/stops/nearby", "/stops/{stop_id}", "/stops/{stop_id}/eta", "/recommendations", "/routes/walk", "/chat"} <= set(paths)


def test_eta_status_has_historical_fallback(client):
    # No live GPS -> historical average first, schedule only when there is no history (backend-architecture.md §4)
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert schemas["EtaStatus"]["enum"] == ["live", "historical", "schedule_only", "stale", "passed", "no_data"]
    risks = schemas["RecommendationItem"]["properties"]["risks"]["items"]["enum"]
    assert "historical_only" in risks
