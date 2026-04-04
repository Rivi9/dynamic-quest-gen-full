from fastapi import APIRouter
from pathlib import Path
from pydantic import BaseModel
from backend.models.narrative import NarrativeContent
from backend.models.player_model import PlayerModel
from backend.narrative.rag_retriever import LoreRetriever
from backend.narrative.memory import EpisodicMemory
from backend.narrative.prompt_builder import PromptBuilder
from backend.narrative.ollama_client import OllamaClient
from backend.player_modeling.modeling_service import PlayerModelingService
from backend.adaptation.agent import NarrativeAgent
from backend.routers.telemetry import get_store

router = APIRouter()

_retriever = LoreRetriever()

# Load lore files into the retriever at startup
_LORE_DIR = Path(__file__).resolve().parents[2] / "lore"
for _lore_file in _LORE_DIR.glob("*.md"):
    _retriever.add_documents_from_file(str(_lore_file), source=_lore_file.name)
_memory: dict[str, EpisodicMemory] = {}
_prompt_builder = PromptBuilder()
_ollama = OllamaClient()
_agent = NarrativeAgent(auto_train=False)
_service = PlayerModelingService(get_store())


class NarrativeRequest(BaseModel):
    session_id: str
    player_id: str = "unknown"
    location: str = "Unknown"
    quest_stage: str = "None"


@router.post("/narrative/generate", response_model=NarrativeContent)
async def generate_narrative(request: NarrativeRequest) -> NarrativeContent:
    player_model = _service.get_model(request.session_id, request.player_id)
    action = _agent.select_action(player_model)

    session_memory = _memory.setdefault(request.session_id, EpisodicMemory())
    memory_ctx = session_memory.get_context_summary()

    query = f"{request.location} {request.quest_stage} {action.value}"
    lore_results = _retriever.retrieve(query, top_k=3)
    lore_context = [r["text"] for r in lore_results]

    system, user = _prompt_builder.build(
        player_model=player_model,
        action=action,
        location=request.location,
        quest_stage=request.quest_stage,
        lore_context=lore_context,
        memory_context=memory_ctx,
    )

    try:
        content = await _ollama.generate(system, user, action)
    except Exception:
        content = _ollama._fallback(action)

    if not content.fallback and content.content:
        session_memory.add_event(
            f"{request.location}: {content.content[:80]}",
            importance=0.7,
        )

    content.lore_refs = [r["source"] for r in lore_results]
    return content
