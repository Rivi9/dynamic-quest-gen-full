from pydantic import BaseModel
from enum import Enum

class NarrativeAction(str, Enum):
    LOWER_STAKES = "LOWER_STAKES"
    RAISE_STAKES = "RAISE_STAKES"
    ADD_MYSTERY = "ADD_MYSTERY"
    ADD_HUMOR = "ADD_HUMOR"
    PROVIDE_GUIDANCE = "PROVIDE_GUIDANCE"
    INCREASE_URGENCY = "INCREASE_URGENCY"
    LORE_REWARD = "LORE_REWARD"
    NO_CHANGE = "NO_CHANGE"

class NarrativeContentType(str, Enum):
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    QUEST_UPDATE = "quest_update"

class NarrativeContent(BaseModel):
    action_taken: NarrativeAction
    content_type: NarrativeContentType
    content: str
    speaker: str | None = None
    emotional_tone: str = "neutral"
    lore_refs: list[str] = []
    fallback: bool = False
