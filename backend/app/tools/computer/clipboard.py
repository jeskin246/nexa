"""
NEXA Computer Tools — Clipboard operations.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class ClipboardReadTool(Tool):
    @property
    def name(self) -> str:
        return "clipboard.read"

    @property
    def description(self) -> str:
        return "Read the current contents of the system clipboard."

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyperclip
            content = pyperclip.paste()
            logger.info(f"Clipboard read: {len(content)} characters")
            return ToolResult.ok(
                data={"content": content, "length": len(content)},
                message=f"Clipboard contains {len(content)} characters",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class ClipboardWriteTool(Tool):
    @property
    def name(self) -> str:
        return "clipboard.write"

    @property
    def description(self) -> str:
        return "Write text content to the system clipboard."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="content", type="string",
                description="The text content to copy to clipboard",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pyperclip
            content = params.get("content", "")
            pyperclip.copy(content)
            logger.info(f"Clipboard write: {len(content)} characters")
            return ToolResult.ok(
                message=f"Copied {len(content)} characters to clipboard",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [ClipboardReadTool(), ClipboardWriteTool()]
