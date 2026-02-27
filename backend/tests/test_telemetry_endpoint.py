import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def _batch_dict(**kwargs):
    base = {
        "player_id": "p1", "session_id": "test-ws-session",
        "window_start": time.time()-5, "window_end": time.time(),
    }
    base.update(kwargs)
    return base

def test_websocket_accepts_valid_batch():
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.send_json(_batch_dict(kills=2, deaths=0))
        resp = ws.receive_json()
    assert resp["status"] == "received"
    assert resp["session_id"] == "test-ws-session"

def test_websocket_rejects_missing_player_id():
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.send_json({"session_id": "s1", "window_start": 0.0, "window_end": 5.0})
        resp = ws.receive_json()
    assert resp["status"] == "error"

def test_http_telemetry_post_accepts_valid_batch():
    resp = client.post("/api/telemetry", json=_batch_dict(kills=1))
    assert resp.status_code == 200
    assert resp.json()["status"] == "received"

def test_http_telemetry_post_rejects_invalid():
    resp = client.post("/api/telemetry", json={"bad": "data"})
    assert resp.status_code == 422
