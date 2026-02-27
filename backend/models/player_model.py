from pydantic import BaseModel
from enum import Enum

class FlowState(str, Enum):
    FLOW = "FLOW"
    ANXIETY = "ANXIETY"
    BOREDOM = "BOREDOM"
    APATHY = "APATHY"

class CurrentState(str, Enum):
    IN_COMBAT = "IN_COMBAT"
    EXPLORING = "EXPLORING"
    IN_DIALOGUE = "IN_DIALOGUE"
    IDLE = "IDLE"

class HexadProfile(BaseModel):
    achiever: float = 0.5
    explorer: float = 0.5
    socializer: float = 0.5
    free_spirit: float = 0.5
    disruptor: float = 0.5
    philanthropist: float = 0.5

class PlayerModel(BaseModel):
    player_id: str
    session_id: str
    timestamp: float
    current_state: CurrentState
    flow_state: FlowState
    flow_score: float
    challenge_skill_ratio: float
    hexad_profile: HexadProfile
    session_embedding: list[float] = []
    session_elapsed: float = 0.0
