#!/usr/bin/env python3
"""
Emotional state engine for Invisible Wall relationship simulator.

Maintains hidden state and applies transition rules based on events.

Usage:
    # Initialize new state
    state_engine.py init --output state.json

    # Apply an event
    state_engine.py apply --state state.json --event eager_push
    state_engine.py apply --state state.json --event retraction --content "我喜欢..."

    # Query state
    state_engine.py query --state state.json

    # Get response style hints
    state_engine.py style --state state.json
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class EmotionalState:
    """Hidden emotional state dimensions."""
    warmth: int = 0           # -5 to +5: 冷淡 ↔ 温暖
    tension: int = 0          # 0-10: 暧昧张力
    trust: int = 5            # 0-10: 信任程度
    disappointment: int = 0   # 0-10: 失望累积
    need: int = 3             # 0-10: 被需要感
    rhythm: int = 5           # 0-10: 节奏匹配度

    # Memory
    consecutive_days: int = 0        # 连续聊天天数
    last_interaction: str = ""       # ISO timestamp
    retraction_memory: list = None   # 记住的撤回内容
    disappointment_events: list = None  # 失望事件记录

    def __post_init__(self):
        if self.retraction_memory is None:
            self.retraction_memory = []
        if self.disappointment_events is None:
            self.disappointment_events = []

    def clamp(self):
        """Ensure all values are within valid ranges."""
        self.warmth = max(-5, min(5, self.warmth))
        self.tension = max(0, min(10, self.tension))
        self.trust = max(0, min(10, self.trust))
        self.disappointment = max(0, min(10, self.disappointment))
        self.need = max(0, min(10, self.need))
        self.rhythm = max(0, min(10, self.rhythm))


# Event transition rules
TRANSITIONS = {
    # Positive events
    "consistent_daily": {"warmth": +1, "trust": +1, "rhythm": +1},
    "remembered_detail": {"warmth": +2, "trust": +1, "need": +1},
    "patient_waiting": {"warmth": +1, "rhythm": +1},
    "shared_personal": {"trust": +1, "warmth": +1},
    "natural_rhythm": {"trust": +1, "rhythm": +1},
    "showed_care": {"warmth": +1, "need": +1},

    # Negative events
    "eager_push": {"warmth": -1, "tension": +2, "rhythm": -1},
    "disappeared_24h": {"warmth": -1, "disappointment": +1},
    "obvious_dismissal": {"warmth": -2, "trust": -1},
    "inconsistent_story": {"trust": -2},
    "forgot_detail": {"disappointment": +2, "need": -1},
    "missed_emotion": {"disappointment": +1},
    "self_centered": {"disappointment": +1, "warmth": -1},
    "instant_reply_always": {"trust": +0, "rhythm": -1},  # 太刻意

    # High tension events
    "said_ambiguous": {"tension": +2},
    "retraction_seen": {"tension": +2},
    "asked_feelings": {"tension": +1},
    "confession": {"tension": +5},

    # Neutral/reset events
    "long_silence": {"tension": -1},
    "normal_chat": {"tension": -0.5, "rhythm": +0.5},
    "time_passed_day": {"disappointment": -0.5},  # 时间会淡化失望
}


def apply_event(state: EmotionalState, event: str, content: str = None) -> dict:
    """Apply an event and return the state changes.

    Args:
        state: Current emotional state
        event: Event name (must be in TRANSITIONS)
        content: Optional content for context (e.g., retraction content)

    Returns:
        Dictionary with old values, new values, and changes
    """
    if event not in TRANSITIONS:
        return {"error": f"Unknown event: {event}"}

    old_state = asdict(state)
    changes = TRANSITIONS[event].copy()

    # Special handling for retraction
    if event == "retraction_seen" and content:
        # Check for emotional keywords
        emotional_keywords = ["喜欢", "想你", "想见", "在一起", "讨厌", "烦", "对不起"]
        if any(kw in content for kw in emotional_keywords):
            changes["tension"] = changes.get("tension", 0) + 2

        # Remember the retraction
        state.retraction_memory.append({
            "content": content[:50],  # Truncate
            "timestamp": datetime.now().isoformat(),
            "tension_at_time": state.tension
        })
        # Keep only last 5
        state.retraction_memory = state.retraction_memory[-5:]

    # Apply changes
    for attr, delta in changes.items():
        if hasattr(state, attr):
            current = getattr(state, attr)
            if isinstance(current, (int, float)):
                setattr(state, attr, current + delta)

    # Update last interaction
    state.last_interaction = datetime.now().isoformat()

    # Clamp values
    state.clamp()

    # Check for special state transitions
    special_states = []
    if state.disappointment >= 7:
        special_states.append("distancing_mode")  # 疏远模式
    if state.tension >= 8:
        special_states.append("high_alert")
    if state.warmth <= -3:
        special_states.append("cold_mode")

    new_state = asdict(state)

    return {
        "old": old_state,
        "new": new_state,
        "changes": changes,
        "special_states": special_states
    }


def get_response_style(state: EmotionalState) -> dict:
    """Get response style hints based on current state."""
    style = {
        "reply_length": "normal",
        "reply_delay": "medium",
        "tone": "neutral",
        "punctuation": "normal",
        "emoji_usage": "rare",
        "question_asking": "sometimes",
        "sharing": "minimal",
    }

    # Warmth affects most things
    if state.warmth <= -3:
        style.update({
            "reply_length": "very_short",  # 1-5 chars
            "reply_delay": "long",
            "tone": "cold",
            "punctuation": "minimal",  # 不加标点
            "question_asking": "never",
            "sharing": "none",
        })
    elif state.warmth <= -1:
        style.update({
            "reply_length": "short",
            "reply_delay": "medium_long",
            "tone": "polite_distant",
            "question_asking": "rarely",
        })
    elif state.warmth <= 1:
        style.update({
            "reply_length": "normal",
            "reply_delay": "medium",
            "tone": "neutral",
        })
    elif state.warmth <= 3:
        style.update({
            "reply_length": "normal_plus",
            "reply_delay": "short",
            "tone": "warm",
            "question_asking": "often",
            "sharing": "some",
        })
    else:  # warmth > 3
        style.update({
            "reply_length": "longer",
            "reply_delay": "quick",
            "tone": "caring",
            "question_asking": "often",
            "sharing": "willing",
        })

    # Tension modifies behavior
    if state.tension >= 7:
        style.update({
            "reply_delay": "unpredictable",
            "tone": "cautious",
            "punctuation": "ellipsis_heavy",  # 多省略号
        })

    # Disappointment affects engagement
    if state.disappointment >= 5:
        style.update({
            "tone": "mechanical",
            "question_asking": "never",
            "sharing": "none",
            "reply_length": "short",
        })

    # Example phrases for each warmth level
    example_phrases = {
        "very_cold": ["嗯", "哦", "好", "随便", "都行"],
        "cold": ["还行吧", "也不是", "看情况", "再说"],
        "neutral": ["还好", "是啊", "对的", "嗯嗯"],
        "warm": ["哈哈", "真的吗", "然后呢", "我也是"],
        "caring": ["你呢", "怎么了", "早点休息", "吃饭了吗"],
    }

    if state.warmth <= -3:
        style["example_phrases"] = example_phrases["very_cold"]
    elif state.warmth <= -1:
        style["example_phrases"] = example_phrases["cold"]
    elif state.warmth <= 1:
        style["example_phrases"] = example_phrases["neutral"]
    elif state.warmth <= 3:
        style["example_phrases"] = example_phrases["warm"]
    else:
        style["example_phrases"] = example_phrases["caring"]

    return style


def load_state(path: Path) -> EmotionalState:
    """Load state from JSON file."""
    if not path.exists():
        return EmotionalState()

    data = json.loads(path.read_text())
    state = EmotionalState()
    for key, value in data.items():
        if hasattr(state, key):
            setattr(state, key, value)
    return state


def save_state(state: EmotionalState, path: Path):
    """Save state to JSON file."""
    path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Emotional state engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new state")
    init_parser.add_argument("--output", "-o", type=Path, required=True)
    init_parser.add_argument("--warmth", type=int, default=0)
    init_parser.add_argument("--tension", type=int, default=0)

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply an event")
    apply_parser.add_argument("--state", "-s", type=Path, required=True)
    apply_parser.add_argument("--event", "-e", type=str, required=True)
    apply_parser.add_argument("--content", "-c", type=str, default=None)

    # Query command
    query_parser = subparsers.add_parser("query", help="Query current state")
    query_parser.add_argument("--state", "-s", type=Path, required=True)

    # Style command
    style_parser = subparsers.add_parser("style", help="Get response style hints")
    style_parser.add_argument("--state", "-s", type=Path, required=True)

    # List events command
    subparsers.add_parser("events", help="List available events")

    args = parser.parse_args()

    if args.command == "init":
        state = EmotionalState(warmth=args.warmth, tension=args.tension)
        save_state(state, args.output)
        print(json.dumps(asdict(state), indent=2, ensure_ascii=False))

    elif args.command == "apply":
        state = load_state(args.state)
        result = apply_event(state, args.event, args.content)
        if "error" not in result:
            save_state(state, args.state)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "query":
        state = load_state(args.state)
        print(json.dumps(asdict(state), indent=2, ensure_ascii=False))

    elif args.command == "style":
        state = load_state(args.state)
        style = get_response_style(state)
        print(json.dumps(style, indent=2, ensure_ascii=False))

    elif args.command == "events":
        print("Available events:")
        for event, changes in TRANSITIONS.items():
            effects = ", ".join(f"{k}:{v:+d}" for k, v in changes.items() if isinstance(v, (int, float)))
            print(f"  {event}: {effects}")


if __name__ == "__main__":
    main()
