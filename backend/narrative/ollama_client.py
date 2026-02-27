import json
import httpx
from backend.config import settings
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType

_FALLBACK_MAP: dict[NarrativeAction, str] = {
    NarrativeAction.PROVIDE_GUIDANCE: "The path ahead is treacherous. Tread carefully.",
    NarrativeAction.RAISE_STAKES:     "Something stirs in the darkness. You feel watched.",
    NarrativeAction.ADD_MYSTERY:      "A symbol on the wall catches your eye. You have seen it before.",
    NarrativeAction.LOWER_STAKES:     "The air grows lighter here. A moment of respite.",
    NarrativeAction.INCREASE_URGENCY: "A distant sound echoes. Something is coming.",
    NarrativeAction.ADD_HUMOR:        "You trip slightly. A rat watches you, unimpressed.",
    NarrativeAction.LORE_REWARD:      "Worn carvings on the wall tell an old story.",
    NarrativeAction.NO_CHANGE:        "",
}


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        action: NarrativeAction,
    ) -> NarrativeContent:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.75,
                "top_p": 0.9,
                "num_predict": 200,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                raw = resp.json()["message"]["content"]
                data = json.loads(raw)

                if data.get("fallback"):
                    return self._fallback(action)

                return NarrativeContent(
                    action_taken=action,
                    content_type=NarrativeContentType(data.get("type", "description")),
                    content=data.get("content", ""),
                    speaker=data.get("speaker"),
                    emotional_tone=data.get("emotional_tone", "neutral"),
                )
        except Exception:
            return self._fallback(action)

    def _fallback(self, action: NarrativeAction) -> NarrativeContent:
        return NarrativeContent(
            action_taken=action,
            content_type=NarrativeContentType.DESCRIPTION,
            content=_FALLBACK_MAP.get(action, ""),
            fallback=True,
        )
