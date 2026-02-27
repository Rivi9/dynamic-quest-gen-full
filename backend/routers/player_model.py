from fastapi import APIRouter
from backend.models.player_model import PlayerModel
from backend.player_modeling.modeling_service import PlayerModelingService
from backend.routers.telemetry import get_store

router = APIRouter()
_service = PlayerModelingService(get_store())


@router.get("/player-model/{session_id}", response_model=PlayerModel)
async def get_player_model(session_id: str, player_id: str = "unknown") -> PlayerModel:
    return _service.get_model(session_id, player_id)
