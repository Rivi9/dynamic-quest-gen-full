from dataclasses import dataclass, field


@dataclass
class MemoryEvent:
    text: str
    importance: float
    timestamp: float = 0.0

    def __lt__(self, other: "MemoryEvent") -> bool:
        return self.importance < other.importance


class EpisodicMemory:
    def __init__(self, max_events: int = 10):
        self.max_events = max_events
        self.events: list[MemoryEvent] = []

    def add_event(
        self, text: str, importance: float = 0.5, timestamp: float = 0.0
    ) -> None:
        self.events.append(MemoryEvent(text=text, importance=importance, timestamp=timestamp))
        if len(self.events) > self.max_events:
            self.events.sort(key=lambda e: e.importance, reverse=True)
            self.events = self.events[: self.max_events]

    def get_context_summary(self) -> str:
        if not self.events:
            return ""
        top = sorted(self.events, key=lambda e: e.importance, reverse=True)[:5]
        lines = [f"- {e.text}" for e in top]
        return "KEY NARRATIVE EVENTS THIS SESSION:\n" + "\n".join(lines)

    def clear(self) -> None:
        self.events.clear()
