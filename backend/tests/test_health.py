def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db"] in {"ok", "error"}
    assert r.json()["latest_gps_at"] is None
