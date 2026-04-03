import json
import httpx
from backend.config import settings
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType

_FALLBACK_MAP: dict[NarrativeAction, str] = {
    NarrativeAction.PROVIDE_GUIDANCE: "Varis's voice, clipped and flat: 'Stay to the northern approach. The centre is exposed.'",
    NarrativeAction.RAISE_STAKES:     "Movement on the south ridge. The Crimson Host archers have shifted position.",
    NarrativeAction.ADD_MYSTERY:      "The Chronicler looks up from her journal, watching you pass. She does not write anything down.",
    NarrativeAction.LOWER_STAKES:     "The fighting is elsewhere, for now. The Vale is briefly, almost quietly, itself.",
    NarrativeAction.INCREASE_URGENCY: "From the direction of the Vault entrance, a sound that is not wind and not an animal.",
    NarrativeAction.ADD_HUMOR:        "Sera calls after you: 'Try not to die. I just restocked and I hate doing inventory.'",
    NarrativeAction.LORE_REWARD:      "The Chronicler's voice, without looking up: 'The seal has nine panels. Three are cracked. She has been counting.'",
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
