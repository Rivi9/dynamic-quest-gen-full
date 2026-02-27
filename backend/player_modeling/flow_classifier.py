from backend.models.player_model import FlowState


class FlowClassifier:
    BOREDOM_THRESHOLD = 0.75
    ANXIETY_THRESHOLD = 1.30
    APATHY_IDLE_THRESHOLD = 0.4

    def classify(self, features: dict[str, float]) -> tuple[FlowState, float]:
        ratio = features["challenge_skill_ratio"]
        idle = features["idle_ratio"]
        dialogue = features["dialogue_engage_rate"]

        if idle > self.APATHY_IDLE_THRESHOLD and dialogue < 0.3 and ratio < 0.6:
            return FlowState.APATHY, 0.70

        if ratio < self.BOREDOM_THRESHOLD:
            conf = float(min(1.0, 0.6 + (self.BOREDOM_THRESHOLD - ratio) * 0.8))
            return FlowState.BOREDOM, conf

        if ratio > self.ANXIETY_THRESHOLD:
            conf = float(min(1.0, 0.6 + (ratio - self.ANXIETY_THRESHOLD) * 0.4))
            return FlowState.ANXIETY, conf

        distance = abs(ratio - 1.0)
        conf = float(max(0.55, 1.0 - distance * 1.2))
        return FlowState.FLOW, conf
