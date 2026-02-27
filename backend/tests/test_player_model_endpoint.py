import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def _post_telemetry(session_id: str, kills: int = 3, deaths: int = 1,
                    damage_taken: float = 80.0):
    return client.post("/api/telemetry", json={
        "player_id": "p1",
        "session_id": session_id,
        "window_start": time.time() - 5,
        "window_end": time.time(),
        "kills": kills,
        "deaths": deaths,
        "damage_taken": damage_taken,
        "objectives_completed": 2,
        "objectives_attempted": 3,
        "tiles_explored": 30,
        "total_tiles": 100,
        "session_elapsed": 300.0,
    })


def test_player_model_endpoint_valid_session():
    session = "model-test-session-1"
    _post_telemetry(session)
    resp = client.get(f"/api/player-model/{session}")
    assert resp.status_code == 200
    model = resp.json()
    assert "flow_state" in model
    assert model["flow_state"] in ["FLOW", "ANXIETY", "BOREDOM", "APATHY"]
    assert "hexad_profile" in model
    assert "challenge_skill_ratio" in model


def test_player_model_endpoint_unknown_session_returns_default():
    resp = client.get("/api/player-model/nonexistent-session-xyz")
    assert resp.status_code == 200
    model = resp.json()
    assert model["flow_state"] == "FLOW"
    assert model["challenge_skill_ratio"] == 1.0


def test_player_model_hexad_profile_has_all_fields():
    session = "model-test-session-2"
    _post_telemetry(session)
    resp = client.get(f"/api/player-model/{session}")
    profile = resp.json()["hexad_profile"]
    for field in ["achiever", "explorer", "socializer", "free_spirit", "disruptor", "philanthropist"]:
        assert field in profile
        assert 0.0 <= profile[field] <= 1.0
