#!/usr/bin/env python3
"""
Calculate typing and response timing based on emotional state.

Usage:
    calculate_timing.py --warmth=2 --tension=4 --event=normal
    calculate_timing.py --warmth=-1 --tension=8 --event=retraction

Output (JSON):
    {
        "typing_delay_ms": 5000,
        "read_delay_ms": 30000,
        "pace": "slow",
        "pace_ms_per_char": 120,
        "may_abort": false,
        "temperature_display": "cloudy"
    }
"""

import argparse
import json
import random
import sys


def calculate_timing(warmth: int, tension: int, event: str) -> dict:
    """Calculate response timing based on emotional state.

    Args:
        warmth: -5 to +5, emotional temperature
        tension: 0-10, relationship tension
        event: normal, retraction, confession, question, silence

    Returns:
        Dictionary with timing parameters
    """
    result = {
        "typing_delay_ms": 0,
        "read_delay_ms": 0,
        "pace": "normal",
        "pace_ms_per_char": 80,
        "may_abort": False,
        "temperature_display": "neutral",
        "should_reply": True,
        "reply_length": "normal",
    }

    # Base typing delay based on warmth
    if warmth <= -3:
        base_delay = random.randint(8000, 15000)
        result["pace"] = "fast"  # Quick dismissal
        result["pace_ms_per_char"] = random.randint(30, 50)
        result["reply_length"] = "very_short"
    elif warmth <= -1:
        base_delay = random.randint(5000, 10000)
        result["pace"] = "normal"
        result["pace_ms_per_char"] = random.randint(60, 80)
        result["reply_length"] = "short"
    elif warmth <= 1:
        base_delay = random.randint(4000, 8000)
        result["pace"] = "normal"
        result["pace_ms_per_char"] = random.randint(70, 90)
        result["reply_length"] = "normal"
    elif warmth <= 3:
        base_delay = random.randint(2000, 4000)
        result["pace"] = "normal"
        result["pace_ms_per_char"] = random.randint(60, 80)
        result["reply_length"] = "normal"
    else:  # warmth > 3
        base_delay = random.randint(1000, 2000)
        result["pace"] = "eager"
        result["pace_ms_per_char"] = random.randint(50, 70)
        result["reply_length"] = "longer"

    # Event modifiers
    if event == "retraction":
        base_delay += random.randint(10000, 20000)
        result["pace"] = "slow"
        result["pace_ms_per_char"] = random.randint(120, 180)
        if tension > 5:
            result["may_abort"] = random.random() < 0.3

    elif event == "confession":
        base_delay += random.randint(15000, 30000)
        result["pace"] = "slow"
        result["pace_ms_per_char"] = random.randint(150, 200)
        if warmth < 2:
            result["may_abort"] = random.random() < 0.5
            result["should_reply"] = random.random() < 0.7

    elif event == "ambiguous":  # Flirty or unclear intent
        base_delay += random.randint(5000, 10000)
        result["pace"] = "hesitant"
        result["pace_ms_per_char"] = random.randint(100, 150)

    elif event == "question":  # Direct question like "在干嘛"
        base_delay += random.randint(2000, 3000)

    elif event == "silence":  # They haven't said anything
        base_delay = 0  # No need to type
        result["should_reply"] = False

    # Tension modifiers
    if tension > 7:
        # High tension = unpredictable
        base_delay = random.randint(2000, 30000)
        result["pace_ms_per_char"] = random.randint(50, 200)
        result["may_abort"] = random.random() < 0.2
    elif tension > 5:
        base_delay += random.randint(3000, 8000)

    result["typing_delay_ms"] = base_delay

    # Read delay based on warmth
    if warmth > 3:
        result["read_delay_ms"] = random.randint(5000, 30000)
    elif warmth > 0:
        result["read_delay_ms"] = random.randint(60000, 300000)  # 1-5 min
    else:
        result["read_delay_ms"] = random.randint(600000, 1800000)  # 10-30 min

    # Temperature display (with lag simulation - actual display would lag)
    if warmth <= -3:
        result["temperature_display"] = "freezing"  # ❄
    elif warmth <= -1:
        result["temperature_display"] = "cloudy"  # ☁
    elif warmth <= 1:
        result["temperature_display"] = "neutral"  # 🌤
    elif warmth <= 3:
        result["temperature_display"] = "sunny"  # ☀
    else:
        result["temperature_display"] = "hidden"  # 不显示

    # Special states
    if tension > 7:
        result["special_state"] = "hesitant"  # 💭 迟疑

    return result


def main():
    parser = argparse.ArgumentParser(description="Calculate typing dynamics")
    parser.add_argument("--warmth", type=int, default=0, help="Warmth level (-5 to +5)")
    parser.add_argument("--tension", type=int, default=0, help="Tension level (0-10)")
    parser.add_argument("--event", type=str, default="normal",
                       choices=["normal", "retraction", "confession", "ambiguous", "question", "silence"],
                       help="Event type")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Clamp values
    warmth = max(-5, min(5, args.warmth))
    tension = max(0, min(10, args.tension))

    result = calculate_timing(warmth, tension, args.event)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Typing Delay: {result['typing_delay_ms']}ms ({result['typing_delay_ms']/1000:.1f}s)")
        print(f"Read Delay: {result['read_delay_ms']}ms ({result['read_delay_ms']/1000:.1f}s)")
        print(f"Pace: {result['pace']} ({result['pace_ms_per_char']}ms/char)")
        print(f"Temperature: {result['temperature_display']}")
        print(f"Reply Length: {result['reply_length']}")
        if result.get("may_abort"):
            print("⚠ May abort typing (fake typing then nothing)")
        if not result.get("should_reply", True):
            print("⚠ May not reply at all")


if __name__ == "__main__":
    main()
