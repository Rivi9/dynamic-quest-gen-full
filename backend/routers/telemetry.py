from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from backend.models.telemetry import TelemetryBatch
from backend.db.telemetry_store import TelemetryStore
from backend.config import settings

router = APIRouter()
_store = TelemetryStore(settings.sqlite_path)


@router.websocket("/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            try:
                batch = TelemetryBatch(**data)
                _store.insert(batch)
                await websocket.send_json(
                    {"status": "received", "session_id": batch.session_id}
                )
            except (ValidationError, Exception) as e:
                await websocket.send_json({"status": "error", "detail": str(e)})
    except WebSocketDisconnect:
        pass


@router.post("/telemetry")
async def telemetry_http(batch: TelemetryBatch):
    _store.insert(batch)
    return {"status": "received", "session_id": batch.session_id}


def get_store() -> TelemetryStore:
    """Expose the module-level store for dependency injection in other routers."""
    return _store
