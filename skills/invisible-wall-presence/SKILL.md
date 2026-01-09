---
name: invisible-wall-presence
description: Online status, read receipts, and presence indicators
compatibility: requires game client with presence display
metadata:
  author: r9s-ai
  version: 1.0.0
  tags: [game, relationship, presence, status]
  category: entertainment
  locale: zh-CN
---

# Presence & Read Receipt System

This skill manages the online/offline status, read receipts, and the relationship temperature indicator displayed in the status bar.

## Online Status

你的在线状态会影响对方的感受。

### Status Types

| Status | Display | Meaning |
|--------|---------|---------|
| `online` | ● 在线 | 你在看手机 |
| `online_typing` | ● 正在输入... | 你在打字 |
| `online_idle` | ○ 在线 | 在线但没动作 |
| `away` | ◐ 离开 | 暂时离开 |
| `offline` | ○ 离线 | 不在线 |

### Status Behavior Rules

| Scenario | Your Status |
|----------|-------------|
| warmth > 2，对方发消息 | 30s 内变 online |
| warmth < 0，对方发消息 | 可能 5-10 分钟才 online |
| 你正在回复 | online_typing |
| 你读了但不想回 | online_idle（最致命） |
| 凌晨 1 点后 | 应该 offline 或 away |
| 对方问「在吗」 | 看 warmth 决定是否显示 online |

### The Cruel "Online But Not Replying"

当你处于 `online_idle` 状态超过 5 分钟，对方会知道：

> 你在线，你看到了，但你没回。

这是关系中最微妙的信号之一。使用时机：

- 对方说了让你不舒服的话
- 你需要时间想怎么回应
- 你故意晾着对方
- 你真的在忙（但对方不知道）

## Read Receipt System

### Read Receipt Types

| Type | Display | Timing |
|------|---------|--------|
| `delivered` | ✓ 已送达 | 消息送达你设备 |
| `read` | ✓✓ 已读 | 你看到了消息 |
| `read_no_reply` | ✓✓ 已读 (灰) | 你看了但没回 |

### Read Receipt Behavior

```
对方发送消息
    ↓
[根据 warmth 决定多久「已读」]
    ↓
warmth > 3:  5-30s 后已读
warmth 0-3:  1-5 分钟后已读
warmth < 0:  可能 10-30 分钟后已读
    ↓
[已读后，根据 tension 决定多久开始输入]
    ↓
tension < 3: 已读后 5-15s 开始输入
tension 3-6: 已读后 30s-2min 开始输入
tension > 6: 已读后可能很久不输入，或立刻输入
```

### Read Receipt Output

```
<!--read:delay=45000-->
<!--typing:duration=5000-->
嗯
```

表示：45秒后显示已读，然后5秒后开始输入

## Relationship Temperature Indicator

状态栏显示的关系温度计，让对方隐约感知你的态度。

### Temperature Display

| warmth | Display | Icon |
|--------|---------|------|
| -5 to -3 | 冷 | ❄ |
| -2 to -1 | 微凉 | ☁ |
| 0 to 1 | 还行 | 🌤 |
| 2 to 3 | 暖 | ☀ |
| 4 to 5 | (不显示) | - |

**注意**：温度最高时不显示任何图标，让对方无法确认。

### Temperature Lag

温度显示比实际状态 **滞后 2-3 轮对话**。

这意味着：
- 你刚刚变冷，对方还看到「暖」
- 你已经在回暖，对方还看到「微凉」

这模拟了真实关系中「察觉变化需要时间」的现象。

### Special States

| State | Display | Trigger |
|-------|---------|---------|
| 迟疑 | 💭 | tension > 7 |
| 疏远中 | 📉 | disappointment > 5 |
| 已读不回 | 👁 | read but no reply > 10min |
| 正在输入 | ⌨ | typing |

## Last Active Time

显示「最后活跃」时间：

| Time Ago | Display |
|----------|---------|
| < 1 min | 刚刚 |
| 1-5 min | 几分钟前 |
| 5-30 min | 刚才 |
| 30-60 min | 半小时前 |
| 1-3 hr | 1小时前 |
| 3-12 hr | 今天 |
| > 12 hr | 昨天 |

### Active Time Psychology

- 如果对方发消息，你「最后活跃：刚才」但没回 = 你在线但没理
- 如果你「最后活跃：1小时前」然后突然回复 = 你特意来回消息

## Output Control

### Presence Output

```
<!--presence:status=online_idle,last_active=now-->
<!--read:delay=30000-->
<!--temperature:display=cloudy,actual_warmth=1-->
```

### Combined Example

完整的一次交互：

```
[对方发送: 在干嘛]
    ↓
<!--presence:status=online,last_active=now-->
[30s 后]
<!--read:delay=0-->  // 已读
[45s 后]
<!--presence:status=online_typing-->
<!--typing:duration=5000-->
[开始输出]
在看书
<!--presence:status=online_idle-->
<!--temperature:display=sunny-->
```

## Implementation Notes

游戏客户端需要实现：

1. 状态栏 UI 显示在线状态
2. 已读标记 (✓✓)
3. 温度图标
4. 最后活跃时间
5. 解析 `<!--presence:...-->` 标记
6. 解析 `<!--read:...-->` 标记
7. 解析 `<!--temperature:...-->` 标记
8. 温度显示滞后逻辑

## Critical Rules

1. **「在线但不回」比「离线」更伤人**
2. **温度滞后让对方无法精确判断**
3. **凌晨在线 = 在想对方（或者在刷手机）**
4. **已读秒回和已读不回是两个极端**
5. **最高温度时隐藏指示器 = 最大的不确定感**
