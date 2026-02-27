import numpy as np
from pathlib import Path
from backend.models.player_model import PlayerModel, FlowState
from backend.models.narrative import NarrativeAction

_ACTIONS = list(NarrativeAction)

_HEURISTIC: dict[FlowState, int] = {
    FlowState.ANXIETY:  4,
    FlowState.BOREDOM:  5,
    FlowState.APATHY:   2,
    FlowState.FLOW:     7,
}

MODEL_PATH = "./data/ppo_narrative_agent"


class NarrativeAgent:
    def __init__(self, auto_train: bool = False):
        self._model = None
        if auto_train:
            self._model = self._load_or_train()

    def _load_or_train(self):
        from stable_baselines3 import PPO
        from backend.adaptation.rl_env import NarrativeAdaptationEnv

        path = Path(MODEL_PATH + ".zip")
        if path.exists():
            return PPO.load(MODEL_PATH, env=NarrativeAdaptationEnv())

        from stable_baselines3.common.env_util import make_vec_env
        env = make_vec_env(NarrativeAdaptationEnv, n_envs=4)
        model = PPO(
            "MlpPolicy", env,
            learning_rate=3e-4,
            n_steps=512,
            batch_size=64,
            n_epochs=10,
            gamma=0.95,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=0,
        )
        Path("./data").mkdir(exist_ok=True)
        model.learn(total_timesteps=200_000)
        model.save(MODEL_PATH)
        return model

    def select_action(self, player_model: PlayerModel) -> NarrativeAction:
        if player_model.session_elapsed < 120 or self._model is None:
            idx = _HEURISTIC[player_model.flow_state]
            return _ACTIONS[idx]

        obs = self._to_obs(player_model)
        action_idx, _ = self._model.predict(obs, deterministic=False)
        return _ACTIONS[int(action_idx)]

    def _to_obs(self, pm: PlayerModel) -> np.ndarray:
        score_map = {
            FlowState.FLOW: 1.0, FlowState.BOREDOM: 0.3,
            FlowState.ANXIETY: 0.2, FlowState.APATHY: 0.1,
        }
        return np.array([
            pm.flow_score,
            min(pm.challenge_skill_ratio / 3.0, 1.0),
            pm.hexad_profile.explorer,
            pm.hexad_profile.socializer,
            pm.hexad_profile.achiever,
            pm.hexad_profile.disruptor,
            min(pm.session_elapsed / 1800.0, 1.0),
        ], dtype=np.float32)
