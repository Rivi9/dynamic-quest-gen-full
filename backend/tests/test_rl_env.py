import numpy as np
import gymnasium as gym
import pytest
from backend.adaptation.rl_env import NarrativeAdaptationEnv
from backend.adaptation.reward import compute_reward
from backend.models.player_model import FlowState


def test_env_observation_space_shape():
    env = NarrativeAdaptationEnv()
    obs, _ = env.reset()
    assert obs.shape == (7,)
    assert env.observation_space.contains(obs)


def test_env_action_space_has_8_actions():
    env = NarrativeAdaptationEnv()
    assert env.action_space.n == 8


def test_env_step_returns_valid_tuple():
    env = NarrativeAdaptationEnv()
    env.reset()
    obs, reward, terminated, truncated, info = env.step(0)
    assert isinstance(reward, float)
    assert terminated is False
    assert isinstance(truncated, bool)
    assert env.observation_space.contains(obs)
    assert "flow_state" in info


def test_env_truncates_at_max_steps():
    env = NarrativeAdaptationEnv(max_steps=3)
    env.reset()
    for _ in range(2):
        _, _, _, truncated, _ = env.step(7)
        assert not truncated
    _, _, _, truncated, _ = env.step(7)
    assert truncated


def test_reward_flow_is_positive():
    r = compute_reward(FlowState.FLOW, FlowState.FLOW, action=7, steps_in_state=1)
    assert r > 0


def test_reward_anxiety_is_negative():
    r = compute_reward(FlowState.FLOW, FlowState.ANXIETY, action=1, steps_in_state=1)
    assert r < 0


def test_reward_boredom_is_negative():
    r = compute_reward(FlowState.FLOW, FlowState.BOREDOM, action=0, steps_in_state=1)
    assert r < 0


def test_reward_flow_streak_bonus():
    r_no_streak = compute_reward(FlowState.FLOW, FlowState.FLOW, action=7, steps_in_state=1)
    r_streak    = compute_reward(FlowState.FLOW, FlowState.FLOW, action=7, steps_in_state=5)
    assert r_streak > r_no_streak


def test_reward_transition_bonus_from_anxiety_to_flow():
    r_normal     = compute_reward(FlowState.FLOW, FlowState.FLOW, action=4, steps_in_state=1)
    r_transition = compute_reward(FlowState.ANXIETY, FlowState.FLOW, action=4, steps_in_state=1)
    assert r_transition > r_normal


def test_reward_repetition_penalty():
    r_varied = compute_reward(FlowState.FLOW, FlowState.FLOW, action=2, steps_in_state=1, last_3_actions=[0, 1, 2])
    r_repeat = compute_reward(FlowState.FLOW, FlowState.FLOW, action=2, steps_in_state=1, last_3_actions=[2, 2, 2])
    assert r_repeat < r_varied


# --- Task 11: PPO Agent ---
from backend.adaptation.agent import NarrativeAgent
from backend.models.player_model import PlayerModel, FlowState, CurrentState, HexadProfile
from backend.models.narrative import NarrativeAction
import time


def _make_model(flow: FlowState = FlowState.ANXIETY, elapsed: float = 60.0) -> PlayerModel:
    return PlayerModel(
        player_id="p1", session_id="s1",
        timestamp=time.time(),
        current_state=CurrentState.IN_COMBAT,
        flow_state=flow,
        flow_score=0.8,
        challenge_skill_ratio=1.5,
        hexad_profile=HexadProfile(),
        session_elapsed=elapsed,
    )


def test_agent_uses_heuristic_before_cold_start():
    agent = NarrativeAgent(auto_train=False)
    action = agent.select_action(_make_model(FlowState.ANXIETY, elapsed=60.0))
    assert action == NarrativeAction.PROVIDE_GUIDANCE


def test_agent_heuristic_boredom_selects_urgency():
    agent = NarrativeAgent(auto_train=False)
    action = agent.select_action(_make_model(FlowState.BOREDOM, elapsed=60.0))
    assert action == NarrativeAction.INCREASE_URGENCY


def test_agent_returns_narrative_action():
    agent = NarrativeAgent(auto_train=False)
    action = agent.select_action(_make_model(FlowState.FLOW, elapsed=60.0))
    assert isinstance(action, NarrativeAction)
