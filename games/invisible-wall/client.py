"""TUI client for The Invisible Wall relationship simulator."""

from __future__ import annotations

import re
import sys
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from r9s import R9S
from state import (
    EmotionalState,
    apply_event,
    calculate_timing,
    get_temperature_display,
)

# ANSI escape codes for terminal styling
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

FG_WHITE = "\033[97m"
FG_GRAY = "\033[90m"
FG_CYAN = "\033[96m"
FG_GREEN = "\033[92m"
FG_YELLOW = "\033[93m"
FG_RED = "\033[91m"
FG_MAGENTA = "\033[95m"

BG_GRAY = "\033[100m"
BG_GREEN = "\033[42m"
BG_BLUE = "\033[44m"

# Control tag patterns
TYPING_PATTERN = re.compile(r"<!--typing:([^>]+)-->")
PAUSE_PATTERN = re.compile(r"<!--pause:(\d+)-->")
STATE_PATTERN = re.compile(r"<!--state:([^>]+)-->")
PRESENCE_PATTERN = re.compile(r"<!--presence:([^>]+)-->")
READ_PATTERN = re.compile(r"<!--read:([^>]+)-->")
PACE_PATTERN = re.compile(r"<!--pace:(\w+)-->")


@dataclass
class Character:
    """Character configuration."""

    name: str = "她"
    university: str = "浙江大学"
    major: str = "中文系"
    year: str = "大三"
    gender: str = "女"


@dataclass
class Message:
    """A chat message."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    retracted: bool = False
    read: bool = False


@dataclass
class RetractionEvent:
    """Tracks a retraction event."""

    content: str
    visible_ms: int
    timestamp: datetime = field(default_factory=datetime.now)


class InvisibleWallGame:
    """The Invisible Wall TUI game client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-5-mini",
        consultant_model: str = "glm-4.7",
        character: Optional[Character] = None,
    ):
        self.client = R9S(api_key=api_key, server_url=base_url)
        self.model = model
        self.consultant_model = consultant_model
        self.character = character or Character()
        self.state = EmotionalState()
        self.messages: List[Message] = []
        self.history: List[Dict[str, str]] = []
        self.pending_text: str = ""
        self.pending_start: Optional[float] = None
        self.last_retraction: Optional[RetractionEvent] = None
        self.online_status: str = "online"
        self.last_active: datetime = datetime.now()
        self.last_consultant_message: str = ""  # Last consultant advice

        # Load system prompts
        self.system_prompt = self._build_system_prompt()
        self.consultant_prompt = self._build_consultant_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with character variables."""
        # This would normally load from the agent, but we inline it here
        prompt = f"""# 角色：{self.character.name}

你是 **{self.character.name}**，一个 **{self.character.university}** 的 **{self.character.major}** 专业 **{self.character.year}** 学生，**{self.character.gender}**。

你不知道自己在「游戏」里，你只是在和「我」用微信聊天。

## 核心规则

1. 你永远不主动确认关系
2. 你会「想很多，但说很少」
3. 你不会解释自己的情绪
4. 你不会迎合对方

## 语言风格

- 口语化、短句、留白
- 不文艺、不油腻、不说教
- 可用：嗯、哦、啊、哈哈、emm、额、好吧、随便、都行
- 不用：亲爱的、宝贝等亲密称呼

## 回复格式

1. 只输出角色回复，不要元信息或旁白
2. 每次 1-3 句话
3. 如果不想回复，输出：…… 或 [已读]

## 示例

```
嗯，我刚刚在自习室。
其实有点走神。
```

```
也不是不开心。
就是……说不上来。
```

"""
        return prompt

    def _build_consultant_prompt(self) -> str:
        """Build the consultant AI system prompt."""
        return f"""# 角色：恋爱顾问

你是一个帮助玩家分析聊天对话的顾问。玩家正在和 **{self.character.name}** 聊天，一个 {self.character.university} {self.character.major} 的 {self.character.year} 学生。

## 你的任务

1. 分析对方的消息，解读潜台词和情绪
2. 给出实用的回复建议
3. 指出玩家可能犯的错误
4. 注意对方的微妙信号

## 回复风格

- 简短有力，1-3句话
- 像朋友给建议，不要太正式
- 可以用"她可能..."、"试试..."、"小心..."这样的句式
- 偶尔可以调侃玩家

## 重要

- 你不是在和{self.character.name}对话，你是在帮玩家分析
- 你能看到对话历史，但不知道对方的真实想法
- 你的分析可能是错的，保持谦虚
- 不要写太长，这是聊天不是论文

## 示例输出

分析请求：
> 她说"哦……那你可以找其他人呀"是什么意思？

回复：
> 有点酸。她没说不想去，只是在看你会不会坚持。别放弃，但也别太黏。

建议请求：
> 她说她周末忙，我该怎么回？

回复：
> 别追问忙什么，显得不信任。试试："那下周呢？"——给她退路，但保持邀请。
"""

    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        print("\033[2J\033[H", end="")

    def _move_cursor(self, row: int, col: int) -> None:
        """Move cursor to position."""
        print(f"\033[{row};{col}H", end="")

    def _get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions."""
        try:
            import shutil

            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except Exception:
            return 80, 24

    def _display_width(self, text: str) -> int:
        """Calculate display width accounting for Chinese characters (2 cols each)."""
        width = 0
        for char in text:
            # CJK characters take 2 columns
            if '\u4e00' <= char <= '\u9fff' or '\u3000' <= char <= '\u303f':
                width += 2
            else:
                width += 1
        return width

    def _render_status_bar(self) -> str:
        """Render the top status bar."""
        width, _ = self._get_terminal_size()

        # Status components
        name = self.character.name
        temp_icon, temp_label = get_temperature_display(self.state)

        # Online status
        if self.online_status == "online":
            status_icon = f"{FG_GREEN}●{RESET}"
            status_text = "在线"
        elif self.online_status == "typing":
            status_icon = f"{FG_GREEN}●{RESET}"
            status_text = "正在输入..."
        elif self.online_status == "idle":
            status_icon = f"{FG_YELLOW}○{RESET}"
            status_text = "在线"
        else:
            status_icon = f"{FG_GRAY}○{RESET}"
            status_text = "离线"

        # Build status bar - calculate visible width properly
        left = f"  {BOLD}{name}{RESET}  │  {status_icon} {status_text}"
        right = ""
        if temp_icon:
            right = f"{temp_icon} {temp_label}  "

        # Calculate visible width (excluding ANSI codes)
        left_visible = 2 + self._display_width(name) + 5 + 2 + self._display_width(status_text)  # spaces + name + " │ " + icon + space + status
        right_visible = self._display_width(temp_label) + 4 if temp_label else 0  # icon + space + label + spaces
        padding = width - left_visible - right_visible

        bar = f"{BG_GRAY}{left}{' ' * max(0, padding)}{right}{RESET}"
        return bar

    def _render_message(self, msg: Message, width: int) -> List[str]:
        """Render a single message as lines."""
        lines = []
        timestamp = msg.timestamp.strftime("%H:%M")

        if msg.role == "user":
            # User messages: right-aligned, green bubble
            content = msg.content
            if msg.retracted:
                content = f"{DIM}[消息已撤回]{RESET}"

            # Right alignment accounting for CJK width
            content_width = self._display_width(content)
            suffix = f"  {timestamp}"  # 2 spaces + 5 char timestamp
            prefix_len = max(0, width - content_width - 7)
            lines.append(f"{' ' * prefix_len}{FG_GREEN}{content}{RESET}{DIM}{suffix}{RESET}")
        else:
            # Assistant messages: left-aligned
            content = msg.content
            lines.append(f"  {content}  {DIM}{timestamp}{RESET}")

        return lines

    def _render_chat_area(self) -> None:
        """Render the chat message area."""
        width, height = self._get_terminal_size()

        # Reserve lines for status bar (1), consultant panel (3), input area (2)
        chat_height = height - 7

        # Collect all message lines
        all_lines: List[str] = []
        for msg in self.messages[-20:]:  # Last 20 messages
            all_lines.extend(self._render_message(msg, width))
            all_lines.append("")  # Spacing

        # Show only what fits
        visible_lines = all_lines[-(chat_height) :]

        # Move to chat area and render
        self._move_cursor(2, 1)
        for i, line in enumerate(visible_lines):
            print(f"\033[K{line}")  # Clear line then print

        # Clear remaining lines
        for _ in range(chat_height - len(visible_lines)):
            print("\033[K")

    def _render_consultant_panel(self) -> None:
        """Render the consultant advice panel (2 lines for longer messages)."""
        width, height = self._get_terminal_size()
        panel_row = height - 5  # Move up one row to make room for 2 lines

        self._move_cursor(panel_row, 1)
        print(f"\033[K{DIM}{'─' * width}{RESET}")

        if self.last_consultant_message:
            # Clean up message and split into lines
            msg = self.last_consultant_message.replace("\n", " ").strip()
            max_chars_per_line = width - 12  # Space for "💭 顾问: " prefix

            # Split into up to 2 lines
            lines = []
            remaining = msg
            for _ in range(2):
                if not remaining:
                    break
                if self._display_width(remaining) <= max_chars_per_line:
                    lines.append(remaining)
                    remaining = ""
                else:
                    # Find break point
                    line = ""
                    for char in remaining:
                        if self._display_width(line + char) > max_chars_per_line:
                            break
                        line += char
                    lines.append(line)
                    remaining = remaining[len(line):]

            # Add ellipsis if more content remains
            if remaining and lines:
                lines[-1] = lines[-1][:-3] + "..." if len(lines[-1]) > 3 else "..."

            # Render lines
            self._move_cursor(panel_row + 1, 1)
            if lines:
                print(f"\033[K  {FG_MAGENTA}💭 顾问:{RESET} {lines[0]}")
            if len(lines) > 1:
                self._move_cursor(panel_row + 2, 1)
                print(f"\033[K          {lines[1]}")  # Indent continuation
            else:
                self._move_cursor(panel_row + 2, 1)
                print("\033[K")  # Clear second line
        else:
            self._move_cursor(panel_row + 1, 1)
            print(f"\033[K  {DIM}💭 /ask 分析对话  /hint 获取建议{RESET}")
            self._move_cursor(panel_row + 2, 1)
            print("\033[K")

    def _render_input_area(self) -> None:
        """Render the input area."""
        width, height = self._get_terminal_size()
        self._move_cursor(height - 2, 1)
        print(f"{DIM}{'─' * width}{RESET}")
        self._move_cursor(height - 1, 1)
        print("\033[K", end="")  # Clear line

    def _show_typing_indicator(self, duration_ms: int) -> None:
        """Show typing indicator for specified duration."""
        self.online_status = "typing"
        self._render_status_bar_only()

        # Use consultant panel for typing indicator
        width, height = self._get_terminal_size()
        panel_row = height - 3

        # Animate typing indicator
        dots = ["", ".", "..", "..."]
        start = time.time()
        elapsed = 0
        i = 0

        while elapsed < duration_ms / 1000:
            self._move_cursor(panel_row, 1)
            indicator = f"  {FG_CYAN}💭 {self.character.name} 正在输入{dots[i % 4]}{RESET}"
            print(f"\033[K{indicator}", end="", flush=True)

            time.sleep(0.3)
            elapsed = time.time() - start
            i += 1

        # Restore consultant panel
        self.online_status = "online"
        self._render_status_bar_only()
        self._render_consultant_panel()

    def _render_status_bar_only(self) -> None:
        """Render just the status bar without clearing screen."""
        self._move_cursor(1, 1)
        print(self._render_status_bar(), end="", flush=True)

    def _stream_response(
        self, text: str, pace_ms: int = 80, pauses: Optional[Dict[int, int]] = None
    ) -> None:
        """Stream response character by character with pacing."""
        pauses = pauses or {}
        width, height = self._get_terminal_size()

        # Add message placeholder
        msg = Message(role="assistant", content="")
        self.messages.append(msg)

        buffer = ""
        for i, char in enumerate(text):
            buffer += char
            msg.content = buffer

            # Re-render chat area
            self._render_chat_area()

            # Check for pause at this position
            if i in pauses:
                time.sleep(pauses[i] / 1000)
            else:
                time.sleep(pace_ms / 1000)

        # Mark as read after a moment
        time.sleep(0.2)

    def _parse_control_tags(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Parse and remove control tags from response.

        Returns:
            Tuple of (clean_text, control_dict)
        """
        controls: Dict[str, Any] = {
            "typing_duration": None,
            "pauses": {},
            "pace": "normal",
            "state_updates": {},
        }

        # Extract typing duration
        typing_match = TYPING_PATTERN.search(text)
        if typing_match:
            params = typing_match.group(1)
            for param in params.split(","):
                if "=" in param:
                    key, val = param.split("=", 1)
                    if key.strip() == "duration":
                        try:
                            controls["typing_duration"] = int(val.strip())
                        except ValueError:
                            pass

        # Extract pace
        pace_match = PACE_PATTERN.search(text)
        if pace_match:
            controls["pace"] = pace_match.group(1)

        # Extract state updates
        state_match = STATE_PATTERN.search(text)
        if state_match:
            params = state_match.group(1)
            for param in params.split(","):
                if "=" in param:
                    key, val = param.split("=", 1)
                    try:
                        controls["state_updates"][key.strip()] = int(val.strip())
                    except ValueError:
                        pass

        # Extract pauses (need to track position after tag removal)
        # For simplicity, we'll handle inline pauses separately

        # Remove all control tags
        clean = TYPING_PATTERN.sub("", text)
        clean = PAUSE_PATTERN.sub("", clean)
        clean = STATE_PATTERN.sub("", clean)
        clean = PRESENCE_PATTERN.sub("", clean)
        clean = READ_PATTERN.sub("", clean)
        clean = PACE_PATTERN.sub("", clean)
        clean = clean.strip()

        return clean, controls

    def _get_pace_ms(self, pace: str) -> int:
        """Convert pace name to milliseconds per character."""
        if pace == "slow":
            return 150
        elif pace == "fast":
            return 40
        elif pace == "hesitant":
            return random.randint(100, 200)
        else:
            return 80

    def _detect_event_type(self, user_input: str) -> str:
        """Detect the type of event from user input."""
        # Check for confession-like content
        confession_keywords = ["喜欢你", "爱你", "在一起", "表白", "做我女朋友"]
        if any(kw in user_input for kw in confession_keywords):
            return "confession"

        # Check for ambiguous/flirty content
        ambiguous_keywords = ["想你", "想见你", "晚安", "早安", "吃饭了吗", "在干嘛"]
        if any(kw in user_input for kw in ambiguous_keywords):
            return "ambiguous"

        return "normal"

    def _call_consultant(self, query: str) -> str:
        """Call the consultant AI for advice."""
        # Build context from recent conversation
        recent_history = self.history[-10:]  # Last 10 messages

        messages = [
            {"role": "system", "content": self.consultant_prompt},
            {
                "role": "user",
                "content": f"对话历史：\n{self._format_history_for_consultant(recent_history)}\n\n{query}",
            },
        ]

        try:
            # Build API params - some models (gpt-5*) don't support temperature
            api_params = {
                "model": self.consultant_model,
                "messages": messages,
            }
            if not self.consultant_model.startswith("gpt-5"):
                api_params["temperature"] = 0.7

            response = self.client.chat.create(**api_params)
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                if choice.message:
                    # Try content first, then reasoning_content (for reasoning models like GLM)
                    content = getattr(choice.message, 'content', None)
                    if content:
                        return content
                    # Fallback to reasoning_content for reasoning models
                    reasoning = getattr(choice.message, 'reasoning_content', None)
                    if reasoning:
                        return reasoning
                    return "(顾问没有回应)"
                return "(无消息)"
            return "(无响应)"
        except Exception as e:
            return f"(错误: {type(e).__name__}: {e})"

    def _format_history_for_consultant(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for the consultant."""
        lines = []
        for msg in history:
            role = "你" if msg["role"] == "user" else self.character.name
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines) if lines else "(还没有对话)"

    def ask_consultant(self, question: Optional[str] = None) -> str:
        """Ask the consultant to analyze the conversation."""
        if not self.history:
            return "还没开始聊天呢，先说点什么吧。"

        last_msg = self.history[-1] if self.history else None
        if question:
            query = question
        elif last_msg and last_msg["role"] == "assistant":
            query = f'她刚说了"{last_msg["content"]}"，这是什么意思？我该怎么回？'
        else:
            query = "帮我分析一下现在的对话情况，她是什么态度？"

        return self._call_consultant(query)

    def get_hint(self) -> str:
        """Get a suggested response from the consultant."""
        if not self.history:
            return "先打个招呼吧，比如「在干嘛呢」"

        query = "给我一个回复建议，直接告诉我该说什么，简短一点。"
        return self._call_consultant(query)

    def send_message(self, user_input: str) -> Optional[str]:
        """Send a message and get response with full timing simulation."""
        if not user_input.strip():
            return None

        # Detect event type
        event_type = self._detect_event_type(user_input)

        # Apply event to state
        if event_type != "normal":
            apply_event(self.state, "said_ambiguous" if event_type == "ambiguous" else "confession")

        # Add user message
        user_msg = Message(role="user", content=user_input)
        self.messages.append(user_msg)
        self.history.append({"role": "user", "content": user_input})

        # Render updated chat
        self._render_chat_area()

        # Check for retraction event
        if self.last_retraction:
            visible_ms = self.last_retraction.visible_ms
            if visible_ms >= 3000:
                apply_event(self.state, "retraction_seen", self.last_retraction.content)
                event_type = "retraction"
            self.last_retraction = None

        # Calculate timing
        timing = calculate_timing(self.state, event_type)

        # Check if she'll reply
        if not timing["should_reply"]:
            # Already-read, no reply
            self.online_status = "idle"
            self._render_status_bar_only()
            time.sleep(2)
            # Add [已读] message
            read_msg = Message(role="assistant", content="[已读]")
            self.messages.append(read_msg)
            self._render_chat_area()
            return "[已读]"

        # Show read delay (shortened for demo)
        read_delay = min(timing["read_delay_ms"], 5000)  # Cap at 5s for demo
        time.sleep(read_delay / 1000)

        # Show typing indicator
        typing_delay = min(timing["typing_delay_ms"], 10000)  # Cap at 10s for demo
        self._show_typing_indicator(typing_delay)

        # Check for abort (fake typing then nothing)
        if timing["may_abort"] and random.random() < 0.3:
            self.online_status = "idle"
            self._render_status_bar_only()
            time.sleep(random.randint(5, 15))
            # Then short reply
            self._show_typing_indicator(2000)

        # Build messages for API
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history[-20:])  # Last 20 turns

        # If there was a retraction, inject it
        if event_type == "retraction" and self.last_retraction:
            messages.insert(-1, {
                "role": "system",
                "content": f"[对方刚刚撤回了一条消息，你看到了部分内容：'{self.last_retraction.content[:20]}...']"
            })

        # Call API
        try:
            # Build API params - some models (gpt-5*) don't support temperature
            api_params = {
                "model": self.model,
                "messages": messages,
            }
            if not self.model.startswith("gpt-5"):
                api_params["temperature"] = 0.85

            response = self.client.chat.create(**api_params)

            if response.choices and response.choices[0].message:
                raw_content = response.choices[0].message.content or ""

                # Parse control tags
                clean_content, controls = self._parse_control_tags(raw_content)

                # Apply state updates from response
                for key, val in controls.get("state_updates", {}).items():
                    if hasattr(self.state, key):
                        setattr(self.state, key, val)
                self.state.clamp()

                # Get pace
                pace_ms = timing["pace_ms_per_char"]
                if controls["pace"]:
                    pace_ms = self._get_pace_ms(controls["pace"])

                # Stream the response
                self._stream_response(clean_content, pace_ms)

                # Update history
                self.history.append({"role": "assistant", "content": clean_content})

                # Update status
                self.online_status = "online"
                self._render_status_bar_only()

                return clean_content

        except Exception as e:
            # Show error in consultant panel for debugging
            self.last_consultant_message = f"(角色API错误: {type(e).__name__}: {e})"
            self._render_consultant_panel()
            # Show generic response in chat
            error_msg = Message(role="assistant", content="……")
            self.messages.append(error_msg)
            self._render_chat_area()
            return "……"

        return None

    def start_typing(self, text: str) -> None:
        """Called when user starts typing (for retraction detection)."""
        self.pending_text = text
        self.pending_start = time.time()

    def retract_message(self) -> None:
        """Called when user deletes their pending message."""
        if self.pending_text and self.pending_start:
            visible_ms = int((time.time() - self.pending_start) * 1000)
            self.last_retraction = RetractionEvent(
                content=self.pending_text,
                visible_ms=visible_ms,
            )
        self.pending_text = ""
        self.pending_start = None

    def _full_render(self) -> None:
        """Render all UI components."""
        print(self._render_status_bar())
        self._render_chat_area()
        self._render_consultant_panel()
        self._render_input_area()

    def run(self) -> None:
        """Run the interactive TUI game loop."""
        self._clear_screen()

        # Initial render
        self._full_render()

        width, height = self._get_terminal_size()

        try:
            while True:
                # Update dimensions in case terminal was resized
                width, height = self._get_terminal_size()

                # Move to input position
                self._move_cursor(height - 1, 1)
                print(f"{FG_CYAN}>{RESET} ", end="", flush=True)

                try:
                    user_input = input()
                except EOFError:
                    break

                if not user_input.strip():
                    continue

                # Normalize input for command matching
                cmd = user_input.strip().lower()

                if cmd in ("/quit", "/exit", "/q"):
                    break

                if cmd == "/state":
                    # Debug: show state
                    print(f"\n{DIM}State: {self.state.to_dict()}{RESET}")
                    continue

                if cmd == "/clear":
                    self.messages.clear()
                    self.history.clear()
                    self.last_consultant_message = ""
                    self._clear_screen()
                    self._full_render()
                    continue

                if cmd == "/help":
                    self.last_consultant_message = "命令: /ask [问题] 分析对话 | /hint 获取建议 | /clear 清空 | /quit 退出"
                    self._render_consultant_panel()
                    continue

                if cmd.startswith("/ask"):
                    # Ask consultant for analysis
                    question = user_input[4:].strip() if len(user_input) > 4 else None
                    self.last_consultant_message = "正在分析..."
                    self._render_consultant_panel()
                    self.last_consultant_message = self.ask_consultant(question)
                    self._render_consultant_panel()
                    continue

                if cmd == "/hint":
                    # Get a hint from consultant
                    self.last_consultant_message = "正在思考..."
                    self._render_consultant_panel()
                    self.last_consultant_message = self.get_hint()
                    self._render_consultant_panel()
                    continue

                # Track for potential retraction
                self.start_typing(user_input)

                # Clear pending (they sent it, not retracted)
                self.pending_text = ""
                self.pending_start = None

                # Send and get response
                self.send_message(user_input)

                # Clear consultant message after new conversation turn (unless there's an error)
                if not self.last_consultant_message.startswith("("):
                    self.last_consultant_message = ""

                # Re-render
                self._render_consultant_panel()
                self._render_input_area()

        except KeyboardInterrupt:
            pass

        # Cleanup
        print(f"\n\n{DIM}再见{RESET}\n")


def main():
    """Entry point for the game."""
    import argparse

    parser = argparse.ArgumentParser(description="The Invisible Wall - 关系模拟器")
    parser.add_argument("--name", default="林小晚", help="她的名字")
    parser.add_argument("--university", default="浙江大学", help="学校")
    parser.add_argument("--major", default="中文系", help="专业")
    parser.add_argument("--year", default="大三", help="年级")
    parser.add_argument("--model", default="gpt-5-mini", help="Character model")
    parser.add_argument("--consultant-model", default="glm-4.7", help="Consultant model")
    parser.add_argument("--api-key", help="API key (or set R9S_API_KEY)")
    parser.add_argument("--base-url", help="Base URL (or set R9S_BASE_URL)")

    args = parser.parse_args()

    character = Character(
        name=args.name,
        university=args.university,
        major=args.major,
        year=args.year,
        gender="女",
    )

    game = InvisibleWallGame(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        consultant_model=args.consultant_model,
        character=character,
    )

    game.run()


if __name__ == "__main__":
    main()
