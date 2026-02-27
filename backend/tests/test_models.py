from backend.models.telemetry import TelemetryBatch
from backend.models.player_model import PlayerModel, FlowState, CurrentState, HexadProfile
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType
import time

def test_telemetry_batch_defaults():
    batch = TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=time.time()-5, window_end=time.time()
    )
    assert batch.kills == 0
    assert batch.deaths == 0
    assert batch.total_tiles == 100

def test_player_model_flow_state_enum():
    model = PlayerModel(
        player_id="p1", session_id="s1",
        timestamp=time.time(),
        current_state=CurrentState.IN_COMBAT,
        flow_state=FlowState.ANXIETY,
        flow_score=0.8,
        challenge_skill_ratio=1.6,
        hexad_profile=HexadProfile()
    )
    assert model.flow_state == FlowState.ANXIETY
    assert model.hexad_profile.explorer == 0.5

def test_narrative_content_fallback_default():
    content = NarrativeContent(
        action_taken=NarrativeAction.ADD_MYSTERY,
        content_type=NarrativeContentType.DIALOGUE,
        content="Something stirs."
    )
    assert content.fallback == False
    assert content.lore_refs == []

def test_narrative_action_enum_values():
    actions = [a.value for a in NarrativeAction]
    assert "PROVIDE_GUIDANCE" in actions
    assert "NO_CHANGE" in actions
    assert len(actions) == 8
