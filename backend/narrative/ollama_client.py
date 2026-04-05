import json
import logging
import re
import httpx
from backend.config import settings
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType

logger = logging.getLogger(__name__)

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
        self._fallback_counts: dict[NarrativeAction, int] = {}

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
        raw = ""
        try:
            # Local student machines can need well over 30 seconds for JSON-mode generation.
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat", json=payload
                )
                resp.raise_for_status()
                raw = resp.json()["message"]["content"]
                data = self._parse_response(raw)

                if data.get("fallback"):
                    return self._soft_fallback(action)

                content = self._extract_content_text(data)
                if not content:
                    return self._soft_fallback(action)

                content_type = self._extract_content_type(data)

                return NarrativeContent(
                    action_taken=action,
                    content_type=content_type,
                    content=content,
                    speaker=self._extract_speaker(data),
                    emotional_tone=data.get("emotional_tone", "neutral"),
                )
        except Exception as exc:
            salvaged = self._salvage_text(raw)
            if salvaged:
                logger.warning("Ollama generation parse failed; salvaging raw text instead of fallback.", exc_info=True)
                return NarrativeContent(
                    action_taken=action,
                    content_type=NarrativeContentType.DESCRIPTION,
                    content=salvaged,
                    emotional_tone="neutral",
                    fallback=False,
                )

            logger.warning("Ollama generation failed, using fallback: %r", exc, exc_info=True)
            return self._soft_fallback(action)

    def _fallback(self, action: NarrativeAction) -> NarrativeContent:
        return NarrativeContent(
            action_taken=action,
            content_type=NarrativeContentType.DESCRIPTION,
            content=_FALLBACK_MAP.get(action, ""),
            fallback=True,
        )

    def _soft_fallback(self, action: NarrativeAction) -> NarrativeContent:
        return NarrativeContent(
            action_taken=action,
            content_type=NarrativeContentType.DESCRIPTION,
            content=self._variant_fallback(action),
            fallback=True,
        )

    def _parse_response(self, raw: str) -> dict:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            candidate = match.group(0)
            for variant in (candidate, self._clean_json(candidate)):
                try:
                    data = json.loads(variant)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError:
                    continue

        text = raw.strip()
        if text:
            return {"type": "description", "content": text}

        raise ValueError("Empty Ollama response")

    def _clean_json(self, raw: str) -> str:
        # Local models commonly emit trailing commas before a closing brace/bracket.
        return re.sub(r",\s*([}\]])", r"\1", raw)

    def _extract_content_type(self, data: dict) -> NarrativeContentType:
        raw_type = str(data.get("type", "description")).lower()
        try:
            return NarrativeContentType(raw_type)
        except ValueError:
            return NarrativeContentType.DESCRIPTION

    def _extract_content_text(self, data: dict) -> str:
        content = data.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, dict):
            for key in ("text", "content", "dialogue", "description"):
                value = content.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        for key in ("text", "dialogue", "description"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        # Some local model outputs ignore the requested schema completely.
        # Build a usable line from common alternate keys instead of failing hard.
        character = data.get("character")
        setting = data.get("setting")
        time_of_day = data.get("time_of_day")
        parts = [part.strip() for part in (character, setting, time_of_day) if isinstance(part, str) and part.strip()]
        return ". ".join(parts)

    def _extract_speaker(self, data: dict) -> str | None:
        speaker = data.get("speaker")
        if isinstance(speaker, str):
            return speaker.strip() or None
        return None

    def _salvage_text(self, raw: str) -> str:
        text = (raw or "").strip()
        if not text:
            return ""

        # Remove common JSON scaffolding and keep only the useful narrative text.
        text = self._clean_json(text)

        content_match = re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if content_match:
            try:
                return json.loads(f'"{content_match.group(1)}"').strip()
            except json.JSONDecodeError:
                return content_match.group(1).strip()

        text = re.sub(r'^\s*\{', "", text)
        text = re.sub(r'\}\s*$', "", text)
        text = re.sub(r'"\w+"\s*:\s*', "", text)
        text = text.replace("\\n", " ").replace("\n", " ").strip(" ,")
        return text.strip()

    def _variant_fallback(self, action: NarrativeAction) -> str:
        variants: dict[NarrativeAction, list[str]] = {
            NarrativeAction.PROVIDE_GUIDANCE: [
                "Varis keeps his voice low. 'Hold the safer line and do not give them the centre for free.'",
                "The Chronicler does not look up. 'You are drawing too much pressure at once. Narrow the fight.'",
                "Varis points toward cover. 'Break their angle first, then push.'",
            ],
            NarrativeAction.RAISE_STAKES: [
                "A horn call rolls across the Vale. The fighting is widening, not ending.",
                "More movement stirs along the ridge, enough to turn a skirmish into something larger.",
                "The air near the Vault feels wrong, as though the battle has started leaning toward disaster.",
            ],
            NarrativeAction.INCREASE_URGENCY: [
                "Bootsteps and shouted orders carry from the northern path. Something is closing in fast.",
                "Steel rings out from beyond the ruins. Whatever is coming will not wait for you to be ready.",
                "A fresh cry rises from the ridge. The moment to act is slipping.",
            ],
            NarrativeAction.ADD_MYSTERY: [
                "The Chronicler pauses mid-note, listening to something you cannot hear.",
                "For a moment the wind around the Vault carries a whisper with no clear source.",
                "A half-buried carving catches the light, then vanishes again beneath the dust.",
            ],
            NarrativeAction.LORE_REWARD: [
                "The Chronicler murmurs, 'The Vale was not always contested. Once, both roads answered to the same keep.'",
                "An old field marker bears the Azure seal beneath older, scorched markings from the Host.",
                "Varis glances toward the Vault. 'Men call it sealed. Men have been wrong before.'",
            ],
            NarrativeAction.LOWER_STAKES: [
                "For a brief stretch, the noise of battle thins and the Vale remembers how to be quiet.",
                "Even here, there is a small pocket of stillness between one danger and the next.",
                "Sera exhales softly. 'Good. A breath. Take it while the Vale allows one.'",
            ],
            NarrativeAction.ADD_HUMOR: [
                "Sera folds her arms. 'If you plan to bleed on my stock, at least buy something first.'",
                "Varis looks at the wreckage, unimpressed. 'Messy. Effective enough, but messy.'",
                "The Chronicler sighs. 'You do make archival clarity more difficult than necessary.'",
            ],
            NarrativeAction.NO_CHANGE: [""],
        }
        options = variants.get(action) or [_FALLBACK_MAP.get(action, "")]
        index = self._fallback_counts.get(action, 0) % len(options)
        self._fallback_counts[action] = index + 1
        return options[index]
