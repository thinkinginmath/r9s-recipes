# The Invisible Wall (隐形墙)

A relationship simulator game that demonstrates r9s SDK capabilities.

## What Is This?

This is not a dating game. It's a **relationship simulation / emotional experiment device**.

You chat with "her" - a realistic AI character who:
- Never confirms the relationship first
- Thinks a lot, says little
- Has hidden emotional states that affect responses
- May leave you on read
- May type for 30 seconds then just say "嗯"

## Quick Start

```bash
# Install r9s SDK
pip install r9s

# Set your API key
export R9S_API_KEY="your-key"

# Run the game
cd presets/games/invisible-wall
python client.py
```

## Customize Character

```bash
python client.py \
  --name "苏小暖" \
  --university "北京大学" \
  --major "心理学" \
  --year "大二" \
  --model "gpt-4o"
```

## Screenshot

```
┌──────────────────────────────────────────────────────────────┐
│  林小晚  │  ● 在线  │                              ☁ 微凉  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                                          在干嘛  14:32      │
│                                                              │
│  嗯，在自习室                                                │
│  有点困                                     14:33           │
│                                                              │
│                                    要不要出来走走  14:35     │
│                                                              │
│  [林小晚 正在输入...]                       (8.7s)          │
│                                                              │
│──────────────────────────────────────────────────────────────│
│> _                                                           │
└──────────────────────────────────────────────────────────────┘
```

## How It Works

### Hidden Emotional State

The game tracks hidden dimensions (never shown to you):

| Dimension | Range | Description |
|-----------|-------|-------------|
| warmth | -5 to +5 | 冷淡 ↔ 温暖 |
| tension | 0-10 | 暧昧张力 |
| trust | 0-10 | 信任程度 |
| disappointment | 0-10 | 失望累积 |

### Response Timing

Based on emotional state, her response timing changes:

| State | Typing Duration | Reply Length |
|-------|-----------------|--------------|
| Cold (warmth < 0) | 8-15 seconds | 1-5 chars |
| Neutral | 4-8 seconds | 10-20 chars |
| Warm (warmth > 2) | 1-3 seconds | 20-40 chars |
| High Tension | Random (2-30s) | Unpredictable |

### Temperature Indicator

The status bar shows a vague temperature indicator:

| Icon | Meaning |
|------|---------|
| ❄ 冷 | She's cold to you |
| ☁ 微凉 | Slightly cool |
| 🌤 还行 | Neutral |
| ☀ 暖 | Warm |
| (hidden) | Maximum warmth (no confirmation) |
| 💭 迟疑 | High tension - she's conflicted |

## SDK Features Demonstrated

This game showcases:

1. **Streaming API** - Character-by-character output with pacing
2. **Chat Completions** - Multi-turn conversation
3. **State Management** - Tracking context across turns
4. **Agent System** - Uses the `invisible-wall` agent preset
5. **Skills System** - Uses timing/state/retraction skills

## Related Files

- `../agents/invisible-wall/` - Agent definition
- `../skills/invisible-wall-state/` - Emotional state skill
- `../skills/typing-dynamics/` - Typing timing skill
- `../skills/retraction-handler/` - Message retraction skill

## Commands

| Command | Description |
|---------|-------------|
| `/quit` | Exit the game |
| `/clear` | Clear chat history |
| `/state` | Debug: show emotional state |

## License

MIT - Part of r9s SDK examples.
