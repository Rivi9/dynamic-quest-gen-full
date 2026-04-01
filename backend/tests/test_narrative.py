import pytest
from backend.narrative.rag_retriever import LoreRetriever


def test_retriever_returns_relevant_lore():
    retriever = LoreRetriever(persist_dir=":memory:")
    retriever.add_document(
        "The Vault is an ancient dungeon beneath the Contested Vale.", metadata={"source": "world"}
    )
    retriever.add_document(
        "Commander Varis leads the Azure Veil's forward post.", metadata={"source": "characters"}
    )
    results = retriever.retrieve("tell me about the dungeon", top_k=1)
    assert len(results) == 1
    assert "dungeon" in results[0]["text"].lower() or "vault" in results[0]["text"].lower()


def test_retriever_returns_list_on_empty_collection():
    retriever = LoreRetriever(persist_dir=":memory:")
    results = retriever.retrieve("spaceship laser cannon", top_k=3)
    assert isinstance(results, list)
    assert len(results) == 0


def test_retriever_top_k_limits_results():
    retriever = LoreRetriever(persist_dir=":memory:")
    for i in range(5):
        retriever.add_document(f"Lore chunk {i} about the kingdom.", metadata={"source": "world"})
    results = retriever.retrieve("kingdom lore", top_k=2)
    assert len(results) == 2


def test_retriever_result_has_expected_keys():
    retriever = LoreRetriever(persist_dir=":memory:")
    retriever.add_document("The seal was broken in the war.", metadata={"source": "world"})
    results = retriever.retrieve("seal broken", top_k=1)
    assert "text" in results[0]
    assert "source" in results[0]
    assert "distance" in results[0]


# --- Task 8: Episodic Session Memory ---
from backend.narrative.memory import EpisodicMemory


def test_memory_stores_events():
    mem = EpisodicMemory(max_events=5)
    mem.add_event("Player helped the merchant.", importance=0.9)
    mem.add_event("Player ignored the Chronicler's warning.", importance=0.7)
    assert len(mem.events) == 2


def test_memory_evicts_lowest_importance_when_full():
    mem = EpisodicMemory(max_events=3)
    mem.add_event("Low importance event.", importance=0.1)
    mem.add_event("Medium event.", importance=0.5)
    mem.add_event("High event.", importance=0.9)
    mem.add_event("Another high event.", importance=0.8)
    assert len(mem.events) == 3
    texts = [e.text for e in mem.events]
    assert "Low importance event." not in texts


def test_memory_get_context_summary_contains_events():
    mem = EpisodicMemory()
    mem.add_event("Player found the hidden cache.", importance=0.8)
    summary = mem.get_context_summary()
    assert "Player found the hidden cache." in summary
    assert "KEY NARRATIVE EVENTS" in summary


def test_memory_empty_returns_empty_string():
    mem = EpisodicMemory()
    assert mem.get_context_summary() == ""


def test_memory_clear_empties_all_events():
    mem = EpisodicMemory()
    mem.add_event("Test event.", importance=0.5)
    mem.clear()
    assert len(mem.events) == 0
    assert mem.get_context_summary() == ""


# --- Task 9: Prompt Builder ---
import time
from backend.narrative.prompt_builder import PromptBuilder
from backend.models.player_model import PlayerModel, FlowState, CurrentState, HexadProfile
from backend.models.narrative import NarrativeAction


def _make_model(flow: FlowState = FlowState.ANXIETY) -> PlayerModel:
    return PlayerModel(
        player_id="p1", session_id="s1",
        timestamp=time.time(),
        current_state=CurrentState.IN_DIALOGUE,
        flow_state=flow,
        flow_score=0.8,
        challenge_skill_ratio=1.6,
        hexad_profile=HexadProfile(socializer=0.9, explorer=0.7),
        session_elapsed=600.0,
    )


def test_prompt_builder_system_contains_json_rule():
    builder = PromptBuilder()
    system, _ = builder.build(_make_model(), NarrativeAction.ADD_MYSTERY, location="The Vault")
    assert "JSON" in system
    assert "fallback" in system


def test_prompt_builder_user_contains_flow_state():
    builder = PromptBuilder()
    _, user = builder.build(_make_model(FlowState.ANXIETY), NarrativeAction.PROVIDE_GUIDANCE)
    assert "ANXIETY" in user
    assert "PROVIDE_GUIDANCE" in user


def test_prompt_builder_user_contains_lore():
    builder = PromptBuilder()
    _, user = builder.build(
        _make_model(), NarrativeAction.LORE_REWARD,
        lore_context=["The dungeon holds ancient power."]
    )
    assert "dungeon" in user.lower()


def test_prompt_builder_user_contains_memory_context():
    builder = PromptBuilder()
    _, user = builder.build(
        _make_model(), NarrativeAction.ADD_MYSTERY,
        memory_context="- Player died to the first enemy."
    )
    assert "Player died" in user


def test_prompt_builder_returns_tuple_of_two_strings():
    builder = PromptBuilder()
    result = builder.build(_make_model(), NarrativeAction.NO_CHANGE)
    assert len(result) == 2
    assert all(isinstance(s, str) for s in result)


# --- Task 12: Narrative REST Endpoint ---
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType


def test_narrative_endpoint_with_mocked_ollama():
    mock_content = NarrativeContent(
        action_taken=NarrativeAction.ADD_MYSTERY,
        content_type=NarrativeContentType.DESCRIPTION,
        content="A strange symbol glows on the dungeon wall.",
        speaker=None,
        emotional_tone="mysterious",
    )
    with patch(
        "backend.routers.narrative._ollama.generate",
        new=AsyncMock(return_value=mock_content)
    ):
        client = TestClient(app)
        resp = client.post("/api/narrative/generate", json={
            "session_id": "narrative-test-session",
            "player_id": "p1",
            "location": "The Vault",
            "quest_stage": "Descend to the Vault",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "action_taken" in data
    assert data["content"] == "A strange symbol glows on the dungeon wall."


def test_narrative_endpoint_returns_fallback_gracefully():
    with patch(
        "backend.routers.narrative._ollama.generate",
        new=AsyncMock(side_effect=Exception("LLM unavailable"))
    ):
        client = TestClient(app)
        resp = client.post("/api/narrative/generate", json={
            "session_id": "fallback-test",
            "player_id": "p1",
            "location": "The Contested Vale",
            "quest_stage": "None",
        })
    # Should still return 200 — the agent.select_action picks NO_CHANGE for FLOW cold-start
    # and OllamaClient catches errors and returns fallback
    assert resp.status_code == 200
