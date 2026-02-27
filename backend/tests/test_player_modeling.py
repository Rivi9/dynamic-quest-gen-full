import time
import pytest
from backend.player_modeling.feature_extractor import FeatureExtractor
from backend.player_modeling.flow_classifier import FlowClassifier
from backend.models.telemetry import TelemetryBatch
from backend.models.player_model import FlowState


def _batch(kills=3, deaths=1, damage_taken=50.0, objectives_completed=2,
           objectives_attempted=3, tiles_explored=30, lore_read=1, lore_found=2,
           dialogue_shown=10, dialogue_skipped=2, idle_seconds=5.0,
           session_elapsed=300.0, abilities_used=10, abilities_hit=7):
    return TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=0.0, window_end=5.0,
        kills=kills, deaths=deaths,
        damage_taken=damage_taken,
        objectives_completed=objectives_completed,
        objectives_attempted=objectives_attempted,
        tiles_explored=tiles_explored,
        total_tiles=100,
        lore_items_read=lore_read,
        lore_items_found=lore_found,
        dialogue_lines_shown=dialogue_shown,
        dialogue_lines_skipped=dialogue_skipped,
        idle_seconds=idle_seconds,
        session_elapsed=session_elapsed,
        abilities_used=abilities_used,
        abilities_hit=abilities_hit,
    )


def test_feature_extractor_returns_expected_keys():
    extractor = FeatureExtractor()
    features = extractor.extract([_batch()])
    expected = {
        "kd_ratio", "objective_rate", "explore_rate",
        "dialogue_engage_rate", "ability_accuracy",
        "damage_taken_norm", "idle_ratio", "lore_engage_rate",
        "skill_score", "challenge_score", "challenge_skill_ratio",
    }
    assert expected.issubset(features.keys())


def test_all_features_in_zero_one_range():
    extractor = FeatureExtractor()
    features = extractor.extract([_batch()])
    for key, val in features.items():
        if key != "challenge_skill_ratio":
            assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"


def test_challenge_skill_ratio_higher_on_hard_play():
    extractor = FeatureExtractor()
    easy = extractor.extract([_batch(kills=10, deaths=0, damage_taken=0.0, objectives_completed=5, objectives_attempted=5)])
    hard = extractor.extract([_batch(kills=0, deaths=8, damage_taken=400.0, objectives_completed=0, objectives_attempted=5)])
    assert hard["challenge_skill_ratio"] > easy["challenge_skill_ratio"]


def test_empty_batches_returns_defaults():
    extractor = FeatureExtractor()
    features = extractor.extract([])
    assert features["challenge_skill_ratio"] == 0.5


def test_flow_classifier_returns_valid_state_and_confidence():
    clf = FlowClassifier()
    extractor = FeatureExtractor()
    features = extractor.extract([_batch()])
    state, conf = clf.classify(features)
    assert state in list(FlowState)
    assert 0.0 <= conf <= 1.0


def test_flow_classifier_boredom_on_trivial_play():
    clf = FlowClassifier()
    extractor = FeatureExtractor()
    features = extractor.extract([
        _batch(kills=20, deaths=0, damage_taken=0.0,
               objectives_completed=5, objectives_attempted=5,
               abilities_hit=10, abilities_used=10)
    ])
    state, _ = clf.classify(features)
    assert state == FlowState.BOREDOM


def test_flow_classifier_anxiety_on_impossible_play():
    clf = FlowClassifier()
    extractor = FeatureExtractor()
    features = extractor.extract([
        _batch(kills=0, deaths=10, damage_taken=600.0,
               objectives_completed=0, objectives_attempted=5,
               abilities_hit=0, abilities_used=10)
    ])
    state, _ = clf.classify(features)
    assert state == FlowState.ANXIETY


from backend.player_modeling.hexad_profiler import HexadProfiler
from backend.models.player_model import HexadProfile


def test_hexad_profiler_returns_hexad_profile():
    profiler = HexadProfiler()
    profile = profiler.compute([_batch()])
    assert isinstance(profile, HexadProfile)


def test_hexad_explorer_high_on_exploration():
    profiler = HexadProfiler()
    explorer_batch = TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=0.0, window_end=5.0,
        tiles_explored=85, total_tiles=100,
        lore_items_read=5, lore_items_found=5,
        npc_interactions_voluntary=3,
        session_elapsed=300.0,
    )
    profile = profiler.compute([explorer_batch])
    assert profile.explorer > 0.6


def test_hexad_disruptor_high_on_combat():
    profiler = HexadProfiler()
    combat_batch = TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=0.0, window_end=5.0,
        kills=15, deaths=2, damage_dealt=800.0,
        session_elapsed=300.0,
    )
    profile = profiler.compute([combat_batch])
    assert profile.disruptor > 0.6


def test_hexad_all_dimensions_in_range():
    profiler = HexadProfiler()
    profile = profiler.compute([_batch()])
    for field in ["achiever", "explorer", "socializer", "free_spirit", "disruptor", "philanthropist"]:
        val = getattr(profile, field)
        assert 0.0 <= val <= 1.0, f"hexad.{field}={val} out of [0,1]"


def test_hexad_empty_returns_defaults():
    profiler = HexadProfiler()
    profile = profiler.compute([])
    assert profile.achiever == 0.5
