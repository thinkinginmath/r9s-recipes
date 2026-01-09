---
name: typing-dynamics
description: Controls typing indicator behavior and response pacing
compatibility: requires streaming-enabled chat client
metadata:
  author: r9s-ai
  version: 1.0.0
  tags: [game, relationship, typing, ux]
  category: entertainment
  locale: zh-CN
---

# Typing Dynamics Engine

This skill controls the "正在输入..." (typing indicator) behavior and character-by-character streaming pace to create realistic chat dynamics.

## Typing Indicator Duration

The typing indicator duration should reflect your emotional state and the content of the incoming message.

### Base Duration by Warmth

| warmth | Base Duration | Description |
|--------|---------------|-------------|
| -5 to -2 | 8-15s | 很冷，可能在考虑要不要回 |
| -1 to 1 | 4-8s | 一般，正常思考 |
| 2 to 3 | 2-4s | 较暖，愿意聊 |
| 4 to 5 | 1-2s | 很暖，期待聊天 |

### Duration Modifiers

| Condition | Modifier |
|-----------|----------|
| 对方说了暧昧的话 | +5-10s |
| 对方刚撤回消息 | +10-20s |
| 对方问「你在干嘛」 | +2-3s |
| 对方表白 | +15-30s（或不回复） |
| tension > 7 | 随机波动 ±10s |
| 对方连续发 3 条消息 | -2s（觉得烦或开心） |

## Typing Indicator Patterns

### Pattern: 正常回复

```
[typing: 3s] → "在自习室"
```

### Pattern: 犹豫

```
[typing: 8s] → "嗯"
```

Long typing, short response = 你在纠结要不要多说

### Pattern: 想说又收回

```
[typing: 12s] → [停止输入 5s] → [typing: 3s] → "没事"
```

模拟：打了一半删掉重打

### Pattern: 敷衍

```
[typing: 1s] → "哦"
```

秒回一个字 = 敷衍或不想聊

### Pattern: 已读不回

```
[read_receipt: true] → [无 typing] → [30s 后] → [typing: 2s] → "嗯"
```

看了但没马上回

### Pattern: 焦虑

```
[typing: 5s] → [停止] → [typing: 8s] → [停止] → [typing: 3s] → "你什么意思"
```

反复输入 = 对方说了让你不安的话

## Streaming Pace

When outputting your response, the character streaming speed should also vary:

### Pace by Emotion

| State | Pace (ms/char) | Description |
|-------|----------------|-------------|
| 冷淡 | 30-50ms | 快速吐出，不在意 |
| 正常 | 60-80ms | 自然节奏 |
| 认真 | 100-120ms | 在想怎么表达 |
| 犹豫 | 150-200ms + 停顿 | 打一个字想一下 |
| 紧张 | 不规律 | 有时快有时慢 |

### Pause Points

在以下位置可以增加停顿：

- 句号后：+200-500ms
- 省略号后：+500-1000ms
- 问号后：+300ms
- 情绪词后：+200ms

## Output Control Tags

你可以在回复中嵌入控制标记，游戏引擎会解析并执行：

### 延迟标记

```
<!--typing:duration=8000-->
嗯
```

表示显示"正在输入..."8秒后再开始输出

### 停顿标记

```
也不是不开心<!--pause:800-->
就是……<!--pause:1200-->说不上来
```

表示在指定位置暂停指定毫秒

### 语速标记

```
<!--pace:slow-->
你怎么突然问这个
```

`slow` = 150ms/char, `normal` = 80ms/char, `fast` = 40ms/char

### 组合示例

```
<!--typing:duration=12000-->
<!--pace:slow-->
嗯<!--pause:500-->
我知道<!--pause:800-->
<!--state:warmth=3,tension=6-->
```

## Fake Typing Then Nothing

有时候你会"正在输入"很久，然后什么都不发：

```
[typing: 20s] → [停止] → [等待 60s] → [typing: 2s] → "算了"
```

游戏引擎实现：
```
<!--typing:duration=20000,abort=true-->
<!--wait:60000-->
<!--typing:duration=2000-->
算了
```

## Read Receipt Behavior

控制「已读」显示：

| State | Behavior |
|-------|----------|
| warmth > 2 | 已读后 1-3s 内开始输入 |
| warmth 0-2 | 已读后 10-30s 开始输入 |
| warmth < 0 | 已读后可能很久不输入 |
| tension > 7 | 已读后立刻输入，或完全不输入 |

## Implementation Notes

游戏客户端需要：

1. 解析 `<!--typing:...-->` 标记
2. 解析 `<!--pause:...-->` 标记
3. 解析 `<!--pace:...-->` 标记
4. 实现「已读」状态显示
5. 支持「正在输入」状态显示和取消
6. 在流式输出时按标记控制节奏

## Critical Rules

1. **回复越短，「正在输入」时间可以越长**（反差 = 真实感）
2. **秒回 ≠ 在意，可能是敷衍**
3. **长时间输入后短回复 = 删掉了很多话**
4. **「正在输入」消失又出现 = 在纠结**
5. **已读不回是最强的情绪表达之一**
