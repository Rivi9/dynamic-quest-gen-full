import time
import pytest
from backend.db.telemetry_store import TelemetryStore
from backend.models.telemetry import TelemetryBatch

def _batch(session_id="s1", kills=0, window_offset=0):
    return TelemetryBatch(
        player_id="p1", session_id=session_id,
        window_start=float(window_offset), window_end=float(window_offset + 5),
        kills=kills
    )

def test_store_inserts_and_retrieves():
    store = TelemetryStore(":memory:")
    store.insert(_batch(kills=3))
    rows = store.get_session("s1")
    assert len(rows) == 1
    assert rows[0].kills == 3

def test_get_session_returns_all_for_session():
    store = TelemetryStore(":memory:")
    for i in range(4):
        store.insert(_batch(kills=i, window_offset=i*5))
    rows = store.get_session("s1")
    assert len(rows) == 4
    assert rows[0].kills == 0
    assert rows[-1].kills == 3

def test_get_session_isolates_by_session_id():
    store = TelemetryStore(":memory:")
    store.insert(_batch(session_id="s1", kills=1))
    store.insert(_batch(session_id="s2", kills=99))
    rows = store.get_session("s1")
    assert len(rows) == 1
    assert rows[0].kills == 1

def test_get_last_n_returns_most_recent():
    store = TelemetryStore(":memory:")
    for i in range(5):
        store.insert(_batch(kills=i, window_offset=i*5))
    recent = store.get_last_n("s1", n=3)
    assert len(recent) == 3
    # Must be in ascending time order, most recent last
    assert recent[-1].kills == 4
    assert recent[0].kills == 2

def test_get_last_n_returns_all_if_fewer_than_n():
    store = TelemetryStore(":memory:")
    store.insert(_batch(kills=7))
    recent = store.get_last_n("s1", n=10)
    assert len(recent) == 1

def test_telemetry_store_preserves_all_fields():
    store = TelemetryStore(":memory:")
    original = TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=0.0, window_end=5.0,
        kills=2, deaths=1, damage_taken=45.5,
        tiles_explored=30, total_tiles=100,
        current_location="The Vault",
        session_elapsed=300.0
    )
    store.insert(original)
    retrieved = store.get_session("s1")[0]
    assert retrieved.kills == 2
    assert retrieved.damage_taken == 45.5
    assert retrieved.current_location == "The Vault"
    assert retrieved.session_elapsed == 300.0
