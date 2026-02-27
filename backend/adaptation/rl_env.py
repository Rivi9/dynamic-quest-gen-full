import numpy as np
import gymnasium as gym
from gymnasium import spaces
from backend.models.player_model import FlowState
from backend.models.narrative import NarrativeAction
from backend.adaptation.reward import compute_reward

_ACTIONS = list(NarrativeAction)

_HEURISTIC: dict[FlowState, int] = {
    FlowState.ANXIETY:  4,  # PROVIDE_GUIDANCE
    FlowState.BOREDOM:  5,  # INCREASE_URGENCY
    FlowState.APATHY:   2,  # ADD_MYSTERY
    FlowState.FLOW:     7,  # NO_CHANGE
}

_HELPFUL_ACTIONS: dict[FlowState, list[int]] = {
    FlowState.ANXIETY: [4, 0],
    FlowState.BOREDOM: [5, 1, 2],
    FlowState.APATHY:  [2, 6],
    FlowState.FLOW:    [7],
}


class NarrativeAdaptationEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, max_steps: int = 360):
        super().__init__()
        self.max_steps = max_steps
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(7,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(len(_ACTIONS))
        self._reset_state()

    def _reset_state(self) -> None:
        self._flow_state = FlowState.FLOW
        self._step_count = 0
        self._steps_in_state = 0
        self._last_3_actions: list[int] = []

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self._reset_state()
        return self._obs(), {}

    def step(self, action: int):
        prev = self._flow_state
        self._flow_state = self._simulate_transition(action, prev)
        self._steps_in_state = (
            self._steps_in_state + 1 if self._flow_state == prev else 1
        )
        self._last_3_actions = (self._last_3_actions + [action])[-3:]
        reward = compute_reward(
            prev, self._flow_state, action,
            self._steps_in_state, self._last_3_actions
        )
        self._step_count += 1
        truncated = self._step_count >= self.max_steps
        return self._obs(), reward, False, truncated, {"flow_state": self._flow_state.value}

    def _obs(self) -> np.ndarray:
        score_map = {
            FlowState.FLOW: 1.0, FlowState.BOREDOM: 0.3,
            FlowState.ANXIETY: 0.2, FlowState.APATHY: 0.1,
        }
        return np.array([
            score_map[self._flow_state],
            0.5, 0.5, 0.5, 0.5, 0.5,
            min(self._step_count / self.max_steps, 1.0),
        ], dtype=np.float32)

    def _simulate_transition(self, action: int, current: FlowState) -> FlowState:
        rng = self.np_random
        helpful = _HELPFUL_ACTIONS.get(current, [])
        if action in helpful:
            return FlowState.FLOW if rng.random() < 0.75 else current
        if current == FlowState.FLOW:
            return FlowState.BOREDOM if rng.random() < 0.1 else FlowState.FLOW
        return current
