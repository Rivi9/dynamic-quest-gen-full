import numpy as np
from backend.models.player_model import HexadProfile
from backend.models.telemetry import TelemetryBatch


def _norm(x: float, max_val: float) -> float:
    return float(np.clip(x / max_val, 0.0, 1.0))


class HexadProfiler:
    def compute(self, batches: list[TelemetryBatch]) -> HexadProfile:
        if not batches:
            return HexadProfile()

        kills = sum(b.kills for b in batches)
        deaths = sum(b.deaths for b in batches)
        damage_dealt = sum(b.damage_dealt for b in batches)
        tiles = max(b.tiles_explored for b in batches)
        total_tiles = max(batches[-1].total_tiles, 1)
        lore_read = sum(b.lore_items_read for b in batches)
        lore_found = max(sum(b.lore_items_found for b in batches), 1)
        voluntary_npc = sum(b.npc_interactions_voluntary for b in batches)
        obj_completed = sum(b.objectives_completed for b in batches)
        obj_attempted = max(sum(b.objectives_attempted for b in batches), 1)
        d_shown = max(sum(b.dialogue_lines_shown for b in batches), 1)
        d_skipped = sum(b.dialogue_lines_skipped for b in batches)
        dialogue_engage = float(np.clip(1.0 - d_skipped / d_shown, 0.0, 1.0))
        explore_rate = _norm(tiles, total_tiles)
        lore_rate = _norm(lore_read, lore_found)
        obj_rate = obj_completed / obj_attempted

        achiever     = float(np.clip(0.7 * obj_rate + 0.3 * _norm(kills, 20), 0.0, 1.0))
        explorer     = float(np.clip(0.5 * explore_rate + 0.5 * lore_rate, 0.0, 1.0))
        socializer   = float(np.clip(0.6 * _norm(voluntary_npc, 10) + 0.4 * dialogue_engage, 0.0, 1.0))
        free_spirit  = float(np.clip(0.5 * explore_rate + 0.5 * (1.0 - obj_rate), 0.0, 1.0))
        disruptor    = float(np.clip(0.5 * _norm(kills, 20) + 0.2 * _norm(deaths, 10) + 0.3 * _norm(damage_dealt, 1000.0), 0.0, 1.0))
        philanthropist = float(np.clip(0.6 * dialogue_engage + 0.4 * lore_rate, 0.0, 1.0))

        return HexadProfile(
            achiever=round(achiever, 3),
            explorer=round(explorer, 3),
            socializer=round(socializer, 3),
            free_spirit=round(free_spirit, 3),
            disruptor=round(disruptor, 3),
            philanthropist=round(philanthropist, 3),
        )
