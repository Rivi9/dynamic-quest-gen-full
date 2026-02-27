from pydantic import BaseModel

class TelemetryBatch(BaseModel):
    player_id: str
    session_id: str
    window_start: float
    window_end: float
    kills: int = 0
    deaths: int = 0
    damage_taken: float = 0.0
    damage_dealt: float = 0.0
    abilities_used: int = 0
    abilities_hit: int = 0
    objectives_completed: int = 0
    objectives_attempted: int = 0
    tiles_explored: int = 0
    total_tiles: int = 100
    npc_interactions_voluntary: int = 0
    dialogue_lines_shown: int = 0
    dialogue_lines_skipped: int = 0
    lore_items_read: int = 0
    lore_items_found: int = 0
    idle_seconds: float = 0.0
    session_elapsed: float = 0.0
    current_location: str = "unknown"
    current_objective: str = "none"
