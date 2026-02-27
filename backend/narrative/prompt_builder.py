from backend.models.player_model import PlayerModel
from backend.models.narrative import NarrativeAction

_TONE_MAP = {
    "ANXIETY": "urgent and supportive — the player is struggling",
    "BOREDOM": "exciting and surprising — inject energy",
    "FLOW":    "immersive and atmospheric — maintain the experience",
    "APATHY":  "intriguing and mysterious — re-engage the player",
}

_SYSTEM_TEMPLATE = """\
You are a narrative writer for a dark fantasy RPG called Eryndal.
Generate SHORT content: dialogue (2-4 sentences) or descriptions (1-2 sentences).

STRICT RULES:
- Stay in the game world. No real-world references. No fourth-wall breaks.
- Tone: {tone}
- Output ONLY valid JSON. No markdown, no explanation before or after.
- If you cannot generate coherent in-world content, output exactly: {{"fallback": true}}

Required output schema:
{{"type": "dialogue|description|quest_update",
  "content": "...",
  "speaker": "NPC name or null",
  "emotional_tone": "hopeful|neutral|tense|mysterious|humorous"}}
"""

_USER_TEMPLATE = """\
PLAYER STATE:
- Flow State: {flow_state} (challenge/skill ratio: {ratio:.2f})
- Activity: {current_state}
- Session elapsed: {elapsed}s
- Playstyle: Explorer={explorer:.0%}, Socializer={socializer:.0%}, Achiever={achiever:.0%}, Disruptor={disruptor:.0%}

NARRATIVE ACTION: {action}
Actions reference:
  LOWER_STAKES=ease tension, RAISE_STAKES=increase urgency,
  ADD_MYSTERY=curiosity hook, ADD_HUMOR=comic relief,
  PROVIDE_GUIDANCE=help struggling player, INCREASE_URGENCY=re-engage bored player,
  LORE_REWARD=discovery payoff, NO_CHANGE=no new content needed

LOCATION: {location}
ACTIVE QUEST: {quest_stage}

RELEVANT LORE:
{lore_context}

{memory_context}

CONSTRAINTS:
- Forbidden: real-world references, anachronisms, fourth-wall breaks
- Character voices: Aldric=formal/melancholic, Mira=dry/witty, Stranger=cryptic/short sentences

Generate the narrative JSON:
"""


class PromptBuilder:
    def build(
        self,
        player_model: PlayerModel,
        action: NarrativeAction,
        location: str = "Unknown",
        quest_stage: str = "None",
        lore_context: list[str] | None = None,
        memory_context: str = "",
    ) -> tuple[str, str]:
        tone = _TONE_MAP.get(player_model.flow_state.value, "neutral")
        lore_str = "\n".join(f"- {l}" for l in (lore_context or []))
        if not lore_str:
            lore_str = "- No specific lore retrieved."

        system = _SYSTEM_TEMPLATE.format(tone=tone)
        user = _USER_TEMPLATE.format(
            flow_state=player_model.flow_state.value,
            ratio=player_model.challenge_skill_ratio,
            current_state=player_model.current_state.value,
            elapsed=int(player_model.session_elapsed),
            explorer=player_model.hexad_profile.explorer,
            socializer=player_model.hexad_profile.socializer,
            achiever=player_model.hexad_profile.achiever,
            disruptor=player_model.hexad_profile.disruptor,
            action=action.value,
            location=location,
            quest_stage=quest_stage,
            lore_context=lore_str,
            memory_context=memory_context,
        )
        return system, user
