from fastapi.testclient import TestClient

from app.config import clear_settings_cache
from app.main import app


def test_health_and_scan_and_stats(mock_settings):
    clear_settings_cache()
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["mocks"] == "true"

        scan = client.post("/scan")
        assert scan.status_code == 200
        body = scan.json()
        assert body["new_saved"] >= 1
        assert body["qualified"] >= 1
        assert body["notified"] == body["qualified"]
        assert body["error"] is None

        stats = client.get("/stats")
        assert stats.status_code == 200
        payload = stats.json()
        assert payload["scanned_today"] == body["new_saved"]
        assert payload["qualified"] == body["qualified"]
