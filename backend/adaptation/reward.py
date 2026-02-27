from backend.models.player_model import FlowState

_FLOW_REWARDS: dict[FlowState, float] = {
    FlowState.FLOW:    +1.0,
    FlowState.BOREDOM: -0.3,
    FlowState.ANXIETY: -0.5,
    FlowState.APATHY:  -0.8,
}
_STEP_PENALTY = -0.05
_STREAK_BONUS = 0.20
_TRANSITION_BONUS = 0.30
_REPETITION_PENALTY = -0.15


def compute_reward(
    prev_state: FlowState,
    new_state: FlowState,
    action: int,
    steps_in_state: int,
    last_3_actions: list[int] | None = None,
) -> float:
    r = _FLOW_REWARDS[new_state] + _STEP_PENALTY

    if new_state == FlowState.FLOW and steps_in_state > 2:
        r += _STREAK_BONUS

    if prev_state in (FlowState.ANXIETY, FlowState.BOREDOM) and new_state == FlowState.FLOW:
        r += _TRANSITION_BONUS

    if last_3_actions and len(set(last_3_actions)) == 1 and action in last_3_actions:
        r += _REPETITION_PENALTY

    return float(r)
