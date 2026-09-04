"""
NEXA Computer Tools — Keyboard control.
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class KeyboardTypeTool(Tool):
    @property
    def name(self) -> str:
        return "keyboard.type"

    @property
    def description(self) -> str:
        return "Type text using the keyboard. Simulates individual key presses."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="text", type="string",
                description="The text to type",
            ),
            ToolParameter(
                name="interval", type="number",
                description="Interval between keystrokes in seconds",
                required=False, default=0.02,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import time
            import pyautogui
            import pyperclip
            
            text = params.get("text", "")
            interval = params.get("interval", 0.02)
            
            if not text:
                return ToolResult.fail("No text provided")
            
            # Pause briefly to ensure the target window is focused in the foreground
            time.sleep(0.5)
            
            # Use clipboard paste for fast, 100% accurate typing of multi-line text & symbols
            try:
                pyperclip.copy(text)
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "v")
            except Exception:
                if text.isascii():
                    pyautogui.typewrite(text, interval=interval)
                else:
                    pyautogui.write(text)

            logger.info(f"Typed {len(text)} characters accurately")
            
            return ToolResult.ok(
                data={"characters": len(text)},
                message=f"Typed {len(text)} characters accurately",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class KeyboardPressTool(Tool):
    @property
    def name(self) -> str:
        return "keyboard.press"

    @property
    def description(self) -> str:
        return (
            "Press a single keyboard key. Supports special keys like "
            "enter, tab, escape, backspace, delete, up, down, left, right, "
            "f1-f12, home, end, pageup, pagedown, space."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="key", type="string",
                description="The key to press (e.g., 'enter', 'tab', 'escape', 'f5')",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui
            
            key = params.get("key", "")
            if not key:
                return ToolResult.fail("No key specified")
            
            pyautogui.press(key)
            logger.info(f"Pressed key: {key}")
            
            return ToolResult.ok(message=f"Pressed key: {key}")
        except Exception as e:
            return ToolResult.fail(str(e))


class KeyboardHotkeyTool(Tool):
    @property
    def name(self) -> str:
        return "keyboard.hotkey"

    @property
    def description(self) -> str:
        return (
            "Press a keyboard shortcut/hotkey combination. "
            "Examples: 'ctrl+c', 'ctrl+shift+s', 'alt+f4', 'win+d'."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="keys", type="string",
                description=(
                    "Key combination separated by '+'. "
                    "Examples: 'ctrl+c', 'ctrl+shift+s', 'alt+tab'"
                ),
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui
            
            keys_str = params.get("keys", "")
            if not keys_str:
                return ToolResult.fail("No key combination specified")
            
            # Split by + and strip whitespace
            keys = [k.strip() for k in keys_str.split("+")]
            
            # Map common key names
            key_map = {"win": "win", "windows": "win", "cmd": "win"}
            keys = [key_map.get(k.lower(), k) for k in keys]
            
            pyautogui.hotkey(*keys)
            logger.info(f"Hotkey pressed: {keys_str}")
            
            return ToolResult.ok(message=f"Pressed hotkey: {keys_str}")
        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [KeyboardTypeTool(), KeyboardPressTool(), KeyboardHotkeyTool()]
