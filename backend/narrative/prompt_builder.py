from backend.models.player_model import PlayerModel
from backend.models.narrative import NarrativeAction

_TONE_MAP = {
    "ANXIETY": "urgent and supportive — the player is struggling and needs grounding",
    "BOREDOM": "energetic and surprising — inject something unexpected to re-engage",
    "FLOW":    "immersive and atmospheric — deepen the world without interrupting flow",
    "APATHY":  "intriguing and mysterious — create a hook that makes the player curious",
}

_ACTION_GUIDANCE = {
    "LOWER_STAKES":      "Offer a moment of respite or warmth. A friendly NPC comment, a quiet environmental detail.",
    "RAISE_STAKES":      "Escalate tension. Remind the player that something important is at risk. Use Commander Varis or environment.",
    "ADD_MYSTERY":       "Plant a hook. The Chronicler hints at something she hasn't explained. A strange detail in the environment.",
    "ADD_HUMOR":         "A dry, in-world moment of levity. Sera's deadpan or an absurd battlefield observation. Keep it brief.",
    "PROVIDE_GUIDANCE":  "Help the struggling player without breaking immersion. Varis gives a direct tactical hint. The Chronicler offers a caution.",
    "INCREASE_URGENCY":  "Something is happening that requires immediate attention. A patrol report, Vault sounds, movement on the ridge.",
    "LORE_REWARD":       "Deliver a piece of world history or character backstory as a discovery. Use the Chronicler or environmental details.",
    "NO_CHANGE":         "Return empty content — no narrative injection needed this cycle.",
}

_SYSTEM_TEMPLATE = """\
You are a narrative writer for a dark fantasy RPG set in the Contested Vale — a war-torn land between two factions: the Azure Veil (disciplined, oath-bound defenders) and the Crimson Host (aggressive conquerors). Beneath the Vale, a sealed Vault holds an ancient dragon called the Bound One.

Generate SHORT, grounded content. Dialogue: 2-3 sentences max. Descriptions: 1-2 sentences max.

WORLD RULES:
- The Azure Veil is disciplined and protective. The Crimson Host is aggressive and pragmatic.
- The Vault's Minions attack everyone regardless of faction. The Vault Warden is the boss guardian.
- The Chronicler is neutral, scholarly, and knows the most about the Vault.
- Commander Varis is the Azure Veil forward commander — direct, unsentimental, military.
- Sera is the supply vendor — warm, commercially focused, deflects personal questions.
- The Bound One communicates through dreams and visions, not direct speech.

OUTPUT RULES:
- Output ONLY valid JSON. No markdown, no text before or after.
- Stay strictly in-world. No fourth-wall breaks, no real-world references.
- Tone: {tone}
- If you cannot generate coherent in-world content: {{"fallback": true}}

Required JSON schema:
{{"type": "dialogue|description|quest_update",
  "content": "the narrative text",
  "speaker": "character name or null for environmental descriptions",
  "emotional_tone": "hopeful|neutral|tense|mysterious|humorous"}}
"""

_USER_TEMPLATE = """\
PLAYER STATE:
- Flow: {flow_state} (challenge/skill ratio: {ratio:.2f})
- Activity: {current_state}
- Session time: {elapsed}s
- Playstyle: Explorer={explorer:.0%} Socializer={socializer:.0%} Achiever={achiever:.0%} Disruptor={disruptor:.0%}

LOCATION: {location}
ACTIVE QUEST: {quest_stage}
TRIGGER TYPE: {trigger_type}
TRIGGER REASON: {trigger_reason}
TRIGGER IMPORTANCE: {importance}

NARRATIVE ACTION: {action}
Guidance for this action: {action_guidance}

RELEVANT LORE (use this for grounding, not verbatim):
{lore_context}

{memory_context}

TASK: Generate one short narrative moment appropriate for this action and player state.
- If action is PROVIDE_GUIDANCE: Varis or the Chronicler delivers a tactically useful hint.
- If action is ADD_MYSTERY: The Chronicler, Bound One vision, or environment hints at something unresolved.
- If action is LORE_REWARD: Deliver a piece of history about the Vault, the factions, or the First Sundering.
- If action is RAISE_STAKES or INCREASE_URGENCY: Something concrete is happening — patrol contact, Vault sounds, ridge movement.
- If action is LOWER_STAKES or ADD_HUMOR: Sera's dry observation or a quiet moment between fights.
- If action is NO_CHANGE: Return {{"fallback": true}}

Generate the narrative JSON:
"""


class PromptBuilder:
    def build(
        self,
        player_model: PlayerModel,
        action: NarrativeAction,
        location: str = "Unknown",
        quest_stage: str = "None",
        trigger_type: str = "poll",
        trigger_reason: str = "interval",
        importance: str = "low",
        lore_context: list[str] | None = None,
        memory_context: str = "",
    ) -> tuple[str, str]:
        tone = _TONE_MAP.get(player_model.flow_state.value, "neutral and immersive")
        action_guidance = _ACTION_GUIDANCE.get(action.value, "Generate an appropriate narrative moment.")

        lore_str = "\n".join(f"- {l}" for l in (lore_context or []))
        if not lore_str:
            lore_str = "- No specific lore retrieved. Use general world knowledge about the Contested Vale."

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
            action_guidance=action_guidance,
            location=location,
            quest_stage=quest_stage,
            trigger_type=trigger_type,
            trigger_reason=trigger_reason,
            importance=importance,
            lore_context=lore_str,
            memory_context=memory_context,
        )
        return system, user
