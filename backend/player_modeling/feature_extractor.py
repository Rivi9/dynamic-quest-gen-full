import numpy as np
from backend.models.telemetry import TelemetryBatch


class FeatureExtractor:
    def extract(self, batches: list[TelemetryBatch]) -> dict[str, float]:
        if not batches:
            return {k: 0.5 for k in [
                "kd_ratio", "objective_rate", "explore_rate",
                "dialogue_engage_rate", "ability_accuracy",
                "damage_taken_norm", "idle_ratio", "lore_engage_rate",
                "skill_score", "challenge_score", "challenge_skill_ratio",
            ]}

        kills = sum(b.kills for b in batches)
        deaths = max(sum(b.deaths for b in batches), 1)
        damage_taken = sum(b.damage_taken for b in batches)
        obj_completed = sum(b.objectives_completed for b in batches)
        obj_attempted = max(sum(b.objectives_attempted for b in batches), 1)
        tiles = sum(b.tiles_explored for b in batches)
        total_tiles = batches[-1].total_tiles or 1
        d_shown = max(sum(b.dialogue_lines_shown for b in batches), 1)
        d_skipped = sum(b.dialogue_lines_skipped for b in batches)
        idle = sum(b.idle_seconds for b in batches)
        elapsed = max(batches[-1].session_elapsed, 1.0)
        lore_read = sum(b.lore_items_read for b in batches)
        lore_found = max(sum(b.lore_items_found for b in batches), 1)
        ab_used = max(sum(b.abilities_used for b in batches), 1)
        ab_hit = sum(b.abilities_hit for b in batches)

        kd_ratio = float(np.clip(kills / deaths / 5.0, 0.0, 1.0))
        objective_rate = float(np.clip(obj_completed / obj_attempted, 0.0, 1.0))
        explore_rate = float(np.clip(tiles / total_tiles, 0.0, 1.0))
        dialogue_engage_rate = float(np.clip(1.0 - d_skipped / d_shown, 0.0, 1.0))
        ability_accuracy = float(np.clip(ab_hit / ab_used, 0.0, 1.0))
        damage_taken_norm = float(np.clip(damage_taken / (elapsed / 60.0 + 1) / 200.0, 0.0, 1.0))
        idle_ratio = float(np.clip(idle / elapsed, 0.0, 1.0))
        lore_engage_rate = float(np.clip(lore_read / lore_found, 0.0, 1.0))

        skill_score = (
            0.35 * kd_ratio
            + 0.30 * objective_rate
            + 0.20 * ability_accuracy
            + 0.15 * (1.0 - idle_ratio)
        )
        challenge_score = (
            0.50 * damage_taken_norm
            + 0.30 * (1.0 - objective_rate)
            + 0.20 * float(np.clip(deaths / (deaths + kills + 1), 0.0, 1.0))
        )
        ratio = float(np.clip(challenge_score / max(skill_score, 1e-6), 0.0, 3.0))

        return {
            "kd_ratio": kd_ratio,
            "objective_rate": objective_rate,
            "explore_rate": explore_rate,
            "dialogue_engage_rate": dialogue_engage_rate,
            "ability_accuracy": ability_accuracy,
            "damage_taken_norm": damage_taken_norm,
            "idle_ratio": idle_ratio,
            "lore_engage_rate": lore_engage_rate,
            "skill_score": float(np.clip(skill_score, 0.0, 1.0)),
            "challenge_score": float(np.clip(challenge_score, 0.0, 1.0)),
            "challenge_skill_ratio": ratio,
        }
