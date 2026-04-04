import time
from backend.db.telemetry_store import TelemetryStore
from backend.player_modeling.feature_extractor import FeatureExtractor
from backend.player_modeling.flow_classifier import FlowClassifier
from backend.player_modeling.hexad_profiler import HexadProfiler
from backend.models.player_model import (
    PlayerModel, CurrentState, FlowState, HexadProfile
)
from backend.models.telemetry import TelemetryBatch


class PlayerModelingService:
    def __init__(self, store: TelemetryStore):
        self.store = store
        self.extractor = FeatureExtractor()
        self.flow_clf = FlowClassifier()
        self.hexad = HexadProfiler()

    def get_model(self, session_id: str, player_id: str = "unknown") -> PlayerModel:
        all_batches = self.store.get_session(session_id)
        if not all_batches:
            return self._default_model(player_id, session_id)

        recent_batches = all_batches[-6:]  # ~30s sliding window for Flow
        features = self.extractor.extract(recent_batches)
        flow_state, flow_score = self.flow_clf.classify(features)
        hexad_profile = self.hexad.compute(all_batches)  # cumulative session
        current_state = self._infer_current_state(all_batches[-1])

        return PlayerModel(
            player_id=player_id,
            session_id=session_id,
            timestamp=time.time(),
            current_state=current_state,
            flow_state=flow_state,
            flow_score=flow_score,
            challenge_skill_ratio=features["challenge_skill_ratio"],
            hexad_profile=hexad_profile,
            session_elapsed=all_batches[-1].session_elapsed,
        )

    def _infer_current_state(self, batch: TelemetryBatch) -> CurrentState:
        if batch.kills > 0 or batch.damage_taken > 10:
            return CurrentState.IN_COMBAT
        if batch.npc_interactions_voluntary > 0 or batch.dialogue_lines_shown > 0:
            return CurrentState.IN_DIALOGUE
        if batch.tiles_explored > 0:
            return CurrentState.EXPLORING
        return CurrentState.IDLE

    def _default_model(self, player_id: str, session_id: str) -> PlayerModel:
        return PlayerModel(
            player_id=player_id,
            session_id=session_id,
            timestamp=time.time(),
            current_state=CurrentState.IDLE,
            flow_state=FlowState.FLOW,
            flow_score=0.5,
            challenge_skill_ratio=1.0,
            hexad_profile=HexadProfile(),
        )
