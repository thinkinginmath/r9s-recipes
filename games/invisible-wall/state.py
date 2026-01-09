"""Emotional state engine for Invisible Wall."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class EmotionalState:
    """Hidden emotional state dimensions."""

    warmth: int = 0  # -5 to +5: 冷淡 ↔ 温暖
    tension: int = 0  # 0-10: 暧昧张力
    trust: int = 5  # 0-10: 信任程度
    disappointment: int = 0  # 0-10: 失望累积
    need: int = 3  # 0-10: 被需要感
    rhythm: int = 5  # 0-10: 节奏匹配度

    # Memory
    retraction_memory: List[Dict[str, Any]] = field(default_factory=list)
    last_interaction: Optional[str] = None

    def clamp(self) -> None:
        """Ensure all values are within valid ranges."""
        self.warmth = max(-5, min(5, self.warmth))
        self.tension = max(0, min(10, self.tension))
        self.trust = max(0, min(10, self.trust))
        self.disappointment = max(0, min(10, self.disappointment))
        self.need = max(0, min(10, self.need))
        self.rhythm = max(0, min(10, self.rhythm))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalState":
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "EmotionalState":
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text()))


# Event transition rules
TRANSITIONS: Dict[str, Dict[str, float]] = {
    # Positive events
    "consistent_daily": {"warmth": 1, "trust": 1, "rhythm": 1},
    "remembered_detail": {"warmth": 2, "trust": 1, "need": 1},
    "patient_waiting": {"warmth": 1, "rhythm": 1},
    "shared_personal": {"trust": 1, "warmth": 1},
    "natural_rhythm": {"trust": 1, "rhythm": 1},
    "showed_care": {"warmth": 1, "need": 1},
    # Negative events
    "eager_push": {"warmth": -1, "tension": 2, "rhythm": -1},
    "disappeared_24h": {"warmth": -1, "disappointment": 1},
    "obvious_dismissal": {"warmth": -2, "trust": -1},
    "inconsistent_story": {"trust": -2},
    "forgot_detail": {"disappointment": 2, "need": -1},
    "missed_emotion": {"disappointment": 1},
    "self_centered": {"disappointment": 1, "warmth": -1},
    # High tension events
    "said_ambiguous": {"tension": 2},
    "retraction_seen": {"tension": 2},
    "asked_feelings": {"tension": 1},
    "confession": {"tension": 5},
    # Neutral events
    "normal_chat": {"tension": -0.5, "rhythm": 0.5},
}


def apply_event(state: EmotionalState, event: str, content: str = "") -> Dict[str, Any]:
    """Apply an event and update state."""
    if event not in TRANSITIONS:
        return {"error": f"Unknown event: {event}"}

    changes = TRANSITIONS[event].copy()

    # Special handling for retraction
    if event == "retraction_seen" and content:
        emotional_keywords = ["喜欢", "想你", "想见", "在一起", "讨厌", "烦", "对不起"]
        if any(kw in content for kw in emotional_keywords):
            changes["tension"] = changes.get("tension", 0) + 2

        state.retraction_memory.append(
            {
                "content": content[:50],
                "timestamp": datetime.now().isoformat(),
            }
        )
        state.retraction_memory = state.retraction_memory[-5:]

    # Apply changes
    for attr, delta in changes.items():
        if hasattr(state, attr):
            current = getattr(state, attr)
            if isinstance(current, (int, float)):
                setattr(state, attr, int(current + delta))

    state.last_interaction = datetime.now().isoformat()
    state.clamp()

    return {"changes": changes}


def get_temperature_display(state: EmotionalState) -> tuple[str, str]:
    """Get temperature icon and label for status bar.

    Returns:
        Tuple of (icon, label)
    """
    if state.tension > 7:
        return "💭", "迟疑"
    if state.disappointment > 5:
        return "📉", "疏远中"

    if state.warmth <= -3:
        return "❄", "冷"
    elif state.warmth <= -1:
        return "☁", "微凉"
    elif state.warmth <= 1:
        return "🌤", "还行"
    elif state.warmth <= 3:
        return "☀", "暖"
    else:
        return "", ""  # Hidden at max warmth


def calculate_timing(state: EmotionalState, event: str = "normal") -> Dict[str, Any]:
    """Calculate response timing based on emotional state."""
    result = {
        "typing_delay_ms": 0,
        "read_delay_ms": 0,
        "pace_ms_per_char": 80,
        "may_abort": False,
        "should_reply": True,
    }

    warmth = state.warmth
    tension = state.tension

    # Base typing delay based on warmth
    if warmth <= -3:
        base_delay = random.randint(8000, 15000)
        result["pace_ms_per_char"] = random.randint(30, 50)
    elif warmth <= -1:
        base_delay = random.randint(5000, 10000)
        result["pace_ms_per_char"] = random.randint(60, 80)
    elif warmth <= 1:
        base_delay = random.randint(4000, 8000)
        result["pace_ms_per_char"] = random.randint(70, 90)
    elif warmth <= 3:
        base_delay = random.randint(2000, 4000)
        result["pace_ms_per_char"] = random.randint(60, 80)
    else:
        base_delay = random.randint(1000, 2000)
        result["pace_ms_per_char"] = random.randint(50, 70)

    # Event modifiers
    if event == "retraction":
        base_delay += random.randint(10000, 20000)
        result["pace_ms_per_char"] = random.randint(120, 180)
        if tension > 5:
            result["may_abort"] = random.random() < 0.3
    elif event == "confession":
        base_delay += random.randint(15000, 30000)
        result["pace_ms_per_char"] = random.randint(150, 200)
        if warmth < 2:
            result["may_abort"] = random.random() < 0.5
            result["should_reply"] = random.random() < 0.7
    elif event == "ambiguous":
        base_delay += random.randint(5000, 10000)
        result["pace_ms_per_char"] = random.randint(100, 150)

    # Tension modifiers
    if tension > 7:
        base_delay = random.randint(2000, 30000)
        result["pace_ms_per_char"] = random.randint(50, 200)
        result["may_abort"] = random.random() < 0.2

    result["typing_delay_ms"] = base_delay

    # Read delay
    if warmth > 3:
        result["read_delay_ms"] = random.randint(5000, 30000)
    elif warmth > 0:
        result["read_delay_ms"] = random.randint(30000, 120000)
    else:
        result["read_delay_ms"] = random.randint(120000, 300000)

    return result
