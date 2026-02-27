from fastapi import FastAPI
from backend.routers.telemetry import router as telemetry_ws_router, telemetry_http
from backend.routers.player_model import router as player_model_router
from backend.routers.narrative import router as narrative_router

app = FastAPI(title="Narrative Personalization API", version="0.1.0")

app.include_router(telemetry_ws_router, prefix="/ws", tags=["telemetry"])
app.add_api_route("/api/telemetry", telemetry_http, methods=["POST"], tags=["telemetry"])
app.include_router(player_model_router, prefix="/api", tags=["player-model"])
app.include_router(narrative_router, prefix="/api", tags=["narrative"])


@app.get("/health")
async def health():
    return {"status": "ok"}
